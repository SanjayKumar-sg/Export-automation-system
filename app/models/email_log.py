"""
app/models/email_log.py — Per-email send event log.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class EmailLog(db.Model):
    """Records the result of every individual email send attempt."""

    __tablename__ = "email_logs"

    id: int = db.Column(db.Integer, primary_key=True)

    # ── Foreign Keys ───────────────────────────────────────────────────────
    buyer_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("buyers.id"), nullable=True, index=True
    )
    campaign_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), nullable=True, index=True
    )

    # ── Email Details ──────────────────────────────────────────────────────
    recipient_email: str = db.Column(db.String(255), nullable=False, index=True)
    recipient_name: Optional[str] = db.Column(db.String(255), nullable=True)
    subject: Optional[str] = db.Column(db.String(500), nullable=True)

    # ── Status ─────────────────────────────────────────────────────────────
    # sent | failed | bounced | retry
    status: str = db.Column(db.String(30), nullable=False, default="sent", index=True)
    error_message: Optional[str] = db.Column(db.Text, nullable=True)
    retry_count: int = db.Column(db.Integer, default=0)

    # ── Tracking ───────────────────────────────────────────────────────────
    message_id: Optional[str] = db.Column(db.String(255), nullable=True)
    opened: bool = db.Column(db.Boolean, default=False)
    clicked: bool = db.Column(db.Boolean, default=False)

    # ── Timestamps ─────────────────────────────────────────────────────────
    sent_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    opened_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────
    buyer = db.relationship("Buyer", back_populates="email_logs")
    campaign = db.relationship("Campaign", back_populates="email_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "campaign_id": self.campaign_id,
            "recipient_email": self.recipient_email,
            "recipient_name": self.recipient_name,
            "subject": self.subject,
            "status": self.status,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

    def __repr__(self) -> str:
        return f"<EmailLog {self.recipient_email!r} ({self.status})>"
