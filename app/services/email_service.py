"""
app/services/email_service.py — Gmail SMTP email sender service.

Handles SMTP connection management, auto-reconnect, retry logic,
daily send limits, personalisation tokens, HTML emails, and attachments.
"""
from __future__ import annotations

import logging
import os
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

logger = logging.getLogger("email")


class EmailService:
    """
    Gmail SMTP wrapper with auto-reconnect, retry, and daily limits.
    """

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(
        self,
        sender: str,
        app_password: str,
        daily_limit: int = 200,
        delay_seconds: int = 3,
        max_retries: int = 3,
    ):
        self.sender = sender
        self.app_password = app_password
        self.daily_limit = daily_limit
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries

        self._smtp: Optional[smtplib.SMTP] = None
        self._sent_today: int = 0

    # ── Connection Management ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Establish a TLS SMTP connection. Returns True on success."""
        try:
            self._smtp = smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT, timeout=30)
            self._smtp.ehlo()
            self._smtp.starttls()
            self._smtp.ehlo()
            self._smtp.login(self.sender, self.app_password)
            logger.info("SMTP connected: %s", self.sender)
            return True
        except Exception as e:
            logger.error("SMTP connection failed: %s", e)
            self._smtp = None
            return False

    def disconnect(self) -> None:
        """Close the SMTP connection gracefully."""
        if self._smtp:
            try:
                self._smtp.quit()
            except Exception:
                pass
            self._smtp = None

    def _ensure_connected(self) -> bool:
        """Reconnect if the SMTP connection is not alive."""
        if self._smtp is None:
            return self.connect()
        try:
            status = self._smtp.noop()
            return status[0] == 250
        except Exception:
            logger.warning("SMTP connection lost, reconnecting…")
            return self.connect()

    # ── Send Logic ─────────────────────────────────────────────────────────

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachment_path: Optional[str] = None,
        personalise: Optional[dict] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Send a single email.

        Args:
            personalise: dict with keys like name, company, country for {{token}} replacement.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        if self._sent_today >= self.daily_limit:
            return False, "Daily send limit reached"

        if not self._ensure_connected():
            return False, "SMTP connection failed"

        # Personalise content
        if personalise:
            subject, body_html, body_text = self._apply_tokens(
                subject, body_html, body_text, personalise
            )

        # Build MIME message
        msg = MIMEMultipart("mixed") if attachment_path else MIMEMultipart("alternative")
        msg["From"] = self.sender
        msg["To"] = to_email
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        plain = body_text if body_text else self._html_to_text(body_html)

        if attachment_path:
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(plain, "plain", "utf-8"))
            alt.attach(MIMEText(body_html, "html", "utf-8"))
            msg.attach(alt)
        else:
            msg.attach(MIMEText(plain, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        # Attachment
        if attachment_path and os.path.exists(attachment_path):
            self._attach_file(msg, attachment_path)

        # Collect all recipients for sendmail
        recipients = [to_email]
        if cc:
            recipients += [e.strip() for e in cc.split(",") if e.strip()]
        if bcc:
            recipients += [e.strip() for e in bcc.split(",") if e.strip()]

        # Retry loop
        for attempt in range(1, self.max_retries + 1):
            try:
                self._smtp.sendmail(self.sender, recipients, msg.as_string())
                self._sent_today += 1
                logger.info("Email sent to %s (attempt %d)", to_email, attempt)
                time.sleep(self.delay_seconds)
                return True, None
            except smtplib.SMTPException as e:
                logger.warning("SMTP send error (attempt %d): %s", attempt, e)
                if attempt < self.max_retries:
                    self._ensure_connected()
                    time.sleep(2)
            except Exception as e:
                return False, str(e)

        return False, "Max retries exceeded"

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _apply_tokens(
        subject: str,
        body_html: str,
        body_text: Optional[str],
        tokens: dict,
    ) -> tuple[str, str, Optional[str]]:
        """Replace {{token}} placeholders in all content parts."""
        for key, val in tokens.items():
            placeholder = f"{{{{{key}}}}}"
            val_str = str(val) if val else ""
            subject = subject.replace(placeholder, val_str)
            body_html = body_html.replace(placeholder, val_str)
            if body_text:
                body_text = body_text.replace(placeholder, val_str)
        return subject, body_html, body_text

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Strip HTML tags to produce a plain-text fallback."""
        import re
        text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()

    @staticmethod
    def _attach_file(msg: MIMEMultipart, path: str) -> None:
        """Attach a file to the email message."""
        with open(path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(path)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    def reset_daily_count(self) -> None:
        """Reset the daily sent counter (call at midnight)."""
        self._sent_today = 0
