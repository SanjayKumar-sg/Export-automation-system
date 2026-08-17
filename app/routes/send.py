"""
app/routes/send.py — Email sending / campaign monitor blueprint.
"""
from flask import (
    Blueprint, current_app, jsonify, render_template, request
)
from flask_login import login_required

from app.models.campaign import Campaign
from app.services.campaign_service import CampaignService, get_campaign_state

send_bp = Blueprint("send", __name__, url_prefix="/send")


@send_bp.route("/")
@login_required
def index():
    """Campaign send monitor page."""
    campaigns = Campaign.query.filter(
        Campaign.status.in_(["draft", "paused"])
    ).order_by(Campaign.created_at.desc()).all()
    return render_template("send/index.html", campaigns=campaigns)


@send_bp.route("/start/<int:campaign_id>", methods=["POST"])
@login_required
def start(campaign_id: int):
    """Start sending a campaign."""
    CampaignService.start_campaign(
        campaign_id=campaign_id,
        app=current_app._get_current_object(),
    )
    return jsonify({"status": "started", "campaign_id": campaign_id})


@send_bp.route("/status")
@login_required
def status():
    """Return current send progress (AJAX polling)."""
    return jsonify(get_campaign_state())


@send_bp.route("/pause", methods=["POST"])
@login_required
def pause():
    CampaignService.pause()
    return jsonify({"status": "paused"})


@send_bp.route("/resume", methods=["POST"])
@login_required
def resume():
    CampaignService.resume()
    return jsonify({"status": "resumed"})


@send_bp.route("/stop", methods=["POST"])
@login_required
def stop():
    CampaignService.stop()
    return jsonify({"status": "stopped"})


@send_bp.route("/test", methods=["POST"])
@login_required
def send_test():
    """Send a test email to verify SMTP settings."""
    from app.services.email_service import EmailService
    from app.services.settings_service import SettingsService
    from app.models.attachment import Attachment

    data = request.get_json() or {}
    to_email = data.get("to_email", "")
    subject = data.get("subject", "Test Email from Export Automation")
    body = data.get("body", "<p>This is a test email.</p>")
    att_id = data.get("attachment_id")

    attachment_path = None
    if att_id:
        att = Attachment.query.get(int(att_id))
        if att:
            attachment_path = att.file_path

    sender = SettingsService.get("email_sender") or current_app.config["GMAIL_SENDER"]
    password = SettingsService.get("email_password") or current_app.config["GMAIL_APP_PASSWORD"]

    svc = EmailService(sender=sender, app_password=password, daily_limit=9999)
    connected = svc.connect()

    if not connected:
        return jsonify({"status": "error", "message": "SMTP connection failed"})

    success, error = svc.send_email(
        to_email=to_email,
        subject=subject,
        body_html=body,
        attachment_path=attachment_path,
    )
    svc.disconnect()

    return jsonify({
        "status": "sent" if success else "failed",
        "message": error or "Test email sent successfully!",
    })
