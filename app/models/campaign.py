"""
app/models/campaign.py — Email campaign model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Campaign(db.Model):
    """An email marketing campaign configuration and run record."""

    __tablename__ = "campaigns"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False)
    subject: str = db.Column(db.String(500), nullable=False)
    body_html: str = db.Column(db.Text, nullable=False)
    body_text: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Targeting ──────────────────────────────────────────────────────────
    # all | business | individual
    audience: str = db.Column(db.String(50), nullable=False, default="all")
    cc: Optional[str] = db.Column(db.String(500), nullable=True)
    bcc: Optional[str] = db.Column(db.String(500), nullable=True)

    # ── Attachment ─────────────────────────────────────────────────────────
    attachment_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("attachments.id"), nullable=True
    )

    # ── Template reference ─────────────────────────────────────────────────
    template_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("templates.id"), nullable=True
    )

    # ── Status ─────────────────────────────────────────────────────────────
    # draft | running | paused | completed | failed | stopped
    status: str = db.Column(db.String(30), nullable=False, default="draft", index=True)

    # ── Progress Counters ──────────────────────────────────────────────────
    total_recipients: int = db.Column(db.Integer, default=0)
    sent_count: int = db.Column(db.Integer, default=0)
    failed_count: int = db.Column(db.Integer, default=0)
    bounce_count: int = db.Column(db.Integer, default=0)

    # ── Config ─────────────────────────────────────────────────────────────
    daily_limit: int = db.Column(db.Integer, default=200)
    delay_seconds: int = db.Column(db.Integer, default=3)

    # ── Timestamps ─────────────────────────────────────────────────────────
    started_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    completed_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ── Created by ─────────────────────────────────────────────────────────
    created_by: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    # ── Relationships ──────────────────────────────────────────────────────
    email_logs = db.relationship("EmailLog", back_populates="campaign", lazy="dynamic")
    attachment = db.relationship("Attachment", foreign_keys=[attachment_id])
    template = db.relationship("Template", foreign_keys=[template_id])
    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "audience": self.audience,
            "status": self.status,
            "total_recipients": self.total_recipients,
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "bounce_count": self.bounce_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self) -> str:
        return f"<Campaign {self.name!r} ({self.status})>"
