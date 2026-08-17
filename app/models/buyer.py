"""
app/models/buyer.py — Buyer record model.

Stores all discovered buyer contacts with validation and
classification status tracking.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Buyer(db.Model):
    """A discovered buyer/lead with full contact information."""

    __tablename__ = "buyers"

    id: int = db.Column(db.Integer, primary_key=True)

    # ── Contact Info ───────────────────────────────────────────────────────
    buyer_name: Optional[str] = db.Column(db.String(255), nullable=True)
    company_name: Optional[str] = db.Column(db.String(255), nullable=True, index=True)
    email: str = db.Column(db.String(255), nullable=False, index=True)
    website: Optional[str] = db.Column(db.String(512), nullable=True)
    country: Optional[str] = db.Column(db.String(100), nullable=True, index=True)
    phone: Optional[str] = db.Column(db.String(50), nullable=True)
    address: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Discovery Metadata ─────────────────────────────────────────────────
    source_platform: str = db.Column(db.String(100), nullable=False, default="unknown")
    search_keyword: Optional[str] = db.Column(db.String(255), nullable=True)
    source_url: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Validation Status ──────────────────────────────────────────────────
    # valid | invalid | duplicate | disposable | missing | unverified
    email_status: str = db.Column(db.String(30), nullable=False, default="unverified", index=True)
    validation_error: Optional[str] = db.Column(db.String(255), nullable=True)
    is_duplicate: bool = db.Column(db.Boolean, default=False, nullable=False)
    duplicate_of_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("buyers.id"), nullable=True
    )

    # ── AI Classification ──────────────────────────────────────────────────
    # business | individual | manufacturer | distributor | importer |
    # retailer | wholesaler | unclassified
    buyer_type: str = db.Column(db.String(50), nullable=False, default="unclassified", index=True)
    # high_intent | medium_intent | low_intent | unknown
    intent_level: str = db.Column(db.String(30), nullable=False, default="unknown")
    classification_confidence: Optional[float] = db.Column(db.Float, nullable=True)
    classification_notes: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Campaign Status ────────────────────────────────────────────────────
    # pending | sent | failed | bounced | unsubscribed | opted_out
    campaign_status: str = db.Column(db.String(30), nullable=False, default="pending")
    last_sent_at: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    send_count: int = db.Column(db.Integer, default=0, nullable=False)

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────
    email_logs = db.relationship("EmailLog", back_populates="buyer", lazy="dynamic")
    classifications = db.relationship(
        "Classification", back_populates="buyer", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "buyer_name": self.buyer_name,
            "company_name": self.company_name,
            "email": self.email,
            "website": self.website,
            "country": self.country,
            "phone": self.phone,
            "source_platform": self.source_platform,
            "search_keyword": self.search_keyword,
            "email_status": self.email_status,
            "is_duplicate": self.is_duplicate,
            "buyer_type": self.buyer_type,
            "intent_level": self.intent_level,
            "campaign_status": self.campaign_status,
            "send_count": self.send_count,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Buyer {self.email!r} ({self.buyer_type})>"
