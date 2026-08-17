"""
app/services/campaign_service.py — Email campaign orchestration service.

Manages campaign execution: recipient selection, personalisation,
sending via EmailService, progress tracking, and logging.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.extensions import db
from app.models.buyer import Buyer
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.services.email_service import EmailService

logger = logging.getLogger("email")

# ── Global campaign run state ──────────────────────────────────────────────
_campaign_state: Dict[str, Any] = {
    "running": False,
    "paused": False,
    "stopped": False,
    "campaign_id": None,
    "current_recipient": "",
    "progress": 0,
    "total": 0,
    "sent": 0,
    "failed": 0,
    "log": [],
    "estimated_remaining": "",
    "smtp_connected": False,
}
_campaign_lock = threading.Lock()


def get_campaign_state() -> Dict[str, Any]:
    with _campaign_lock:
        return dict(_campaign_state)


class CampaignService:
    """Orchestrates the execution of an email campaign."""

    @staticmethod
    def start_campaign(campaign_id: int, app=None) -> None:
        """Launch campaign execution in a background thread."""
        with _campaign_lock:
            if _campaign_state["running"]:
                return
            _campaign_state.update(
                running=True, paused=False, stopped=False,
                campaign_id=campaign_id, progress=0,
                sent=0, failed=0, log=[], current_recipient=""
            )

        thread = threading.Thread(
            target=CampaignService._run_campaign,
            args=(campaign_id, app),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _run_campaign(campaign_id: int, app) -> None:
        """Background worker: sends emails to all eligible recipients."""
        from flask import current_app

        ctx = app.app_context() if app else None
        with (ctx or _NullContext()):
            from flask import current_app as ca

            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                CampaignService._log("Campaign not found.")
                with _campaign_lock:
                    _campaign_state["running"] = False
                return

            # Update campaign status
            campaign.status = "running"
            campaign.started_at = datetime.utcnow()
            db.session.commit()

            # Build recipient list
            recipients = CampaignService._get_recipients(campaign)
            campaign.total_recipients = len(recipients)
            db.session.commit()

            with _campaign_lock:
                _campaign_state["total"] = len(recipients)

            CampaignService._log(f"Campaign '{campaign.name}' starting. Recipients: {len(recipients)}")

            from app.services.settings_service import SettingsService
            
            # Init SMTP
            sender = SettingsService.get("email_sender") or ca.config.get("GMAIL_SENDER", "")
            password = SettingsService.get("email_password") or ca.config.get("GMAIL_APP_PASSWORD", "")
            daily_limit = campaign.daily_limit or int(SettingsService.get("daily_send_limit") or ca.config.get("DAILY_SEND_LIMIT", 200))
            delay = campaign.delay_seconds or int(SettingsService.get("send_delay_seconds") or ca.config.get("SEND_DELAY_SECONDS", 3))

            email_svc = EmailService(
                sender=sender,
                app_password=password,
                daily_limit=daily_limit,
                delay_seconds=delay,
            )

            connected = email_svc.connect()
            with _campaign_lock:
                _campaign_state["smtp_connected"] = connected

            if not connected:
                campaign.status = "failed"
                db.session.commit()
                CampaignService._log("SMTP connection failed. Aborting campaign.")
                with _campaign_lock:
                    _campaign_state["running"] = False
                return

            # Attachment path
            attachment_path = None
            if campaign.attachment:
                attachment_path = campaign.attachment.file_path

            # Send loop
            start_time = time.time()
            for i, buyer in enumerate(recipients):
                with _campaign_lock:
                    if _campaign_state["stopped"]:
                        break
                    while _campaign_state["paused"] and not _campaign_state["stopped"]:
                        pass

                with _campaign_lock:
                    _campaign_state["current_recipient"] = buyer.email
                    _campaign_state["progress"] = i + 1

                tokens = {
                    "name": buyer.buyer_name or buyer.company_name or "Sir/Madam",
                    "company": buyer.company_name or "",
                    "country": buyer.country or "",
                    "email": buyer.email,
                }

                success, error = email_svc.send_email(
                    to_email=buyer.email,
                    subject=campaign.subject,
                    body_html=campaign.body_html,
                    body_text=campaign.body_text,
                    cc=campaign.cc,
                    bcc=campaign.bcc,
                    attachment_path=attachment_path,
                    personalise=tokens,
                )

                # Log result
                log_entry = EmailLog(
                    buyer_id=buyer.id,
                    campaign_id=campaign.id,
                    recipient_email=buyer.email,
                    recipient_name=buyer.buyer_name,
                    subject=campaign.subject,
                    status="sent" if success else "failed",
                    error_message=error,
                )
                db.session.add(log_entry)

                # Update buyer
                buyer.last_sent_at = datetime.utcnow()
                buyer.send_count = (buyer.send_count or 0) + 1
                buyer.campaign_status = "sent" if success else "failed"

                if success:
                    campaign.sent_count = (campaign.sent_count or 0) + 1
                    with _campaign_lock:
                        _campaign_state["sent"] += 1
                    CampaignService._log(f"✓ Sent to {buyer.email}")
                else:
                    campaign.failed_count = (campaign.failed_count or 0) + 1
                    with _campaign_lock:
                        _campaign_state["failed"] += 1
                    CampaignService._log(f"✗ Failed: {buyer.email} — {error}")

                # Estimate remaining time
                elapsed = time.time() - start_time
                if i > 0:
                    avg = elapsed / (i + 1)
                    remaining_secs = avg * (len(recipients) - i - 1)
                    mins, secs = divmod(int(remaining_secs), 60)
                    with _campaign_lock:
                        _campaign_state["estimated_remaining"] = f"{mins}m {secs}s"

                # Batch commit every 10 emails
                if (i + 1) % 10 == 0:
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error("DB commit error: %s", e)

            # Finalise
            email_svc.disconnect()
            campaign.status = "completed" if not _campaign_state["stopped"] else "stopped"
            campaign.completed_at = datetime.utcnow()
            db.session.commit()

            with _campaign_lock:
                _campaign_state["running"] = False

            CampaignService._log(
                f"Campaign complete. Sent: {_campaign_state['sent']}, "
                f"Failed: {_campaign_state['failed']}"
            )

    @staticmethod
    def _get_recipients(campaign: Campaign) -> List[Buyer]:
        """Return buyers eligible for this campaign."""
        query = Buyer.query.filter(
            Buyer.email_status == "valid",
            Buyer.campaign_status.in_(["pending"]),
        )
        if campaign.audience == "business":
            query = query.filter(Buyer.buyer_type == "business")
        elif campaign.audience == "individual":
            query = query.filter(Buyer.buyer_type == "individual")
        return query.all()

    @staticmethod
    def pause() -> None:
        with _campaign_lock:
            _campaign_state["paused"] = True

    @staticmethod
    def resume() -> None:
        with _campaign_lock:
            _campaign_state["paused"] = False

    @staticmethod
    def stop() -> None:
        with _campaign_lock:
            _campaign_state["stopped"] = True
            _campaign_state["running"] = False

    @staticmethod
    def _log(msg: str) -> None:
        with _campaign_lock:
            _campaign_state["log"].append(msg)
        logger.info(msg)


class _NullContext:
    def __enter__(self): return self
    def __exit__(self, *a): pass
