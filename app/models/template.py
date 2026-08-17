"""
app/models/template.py — Reusable email template model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Template(db.Model):
    """A reusable email template with Jinja-style variable placeholders."""

    __tablename__ = "templates"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False, unique=True)
    description: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Content ────────────────────────────────────────────────────────────
    subject: str = db.Column(db.String(500), nullable=False)
    body_html: str = db.Column(db.Text, nullable=False)
    body_text: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Categorisation ─────────────────────────────────────────────────────
    category: str = db.Column(db.String(50), nullable=False, default="general")
    # general | business | individual | follow_up | newsletter

    is_default: bool = db.Column(db.Boolean, default=False)
    is_active: bool = db.Column(db.Boolean, default=True)

    # ── Ownership ──────────────────────────────────────────────────────────
    created_by: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "subject": self.subject,
            "body_html": self.body_html,
            "category": self.category,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Template {self.name!r}>"
