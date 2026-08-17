"""
app/models/classification.py — Gemini AI classification result model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Classification(db.Model):
    """Records the Gemini AI classification result for a buyer."""

    __tablename__ = "classifications"

    id: int = db.Column(db.Integer, primary_key=True)

    buyer_id: int = db.Column(
        db.Integer, db.ForeignKey("buyers.id"), nullable=False, index=True
    )

    # ── Classification Outputs ─────────────────────────────────────────────
    buyer_type: str = db.Column(db.String(50), nullable=False)
    # business | individual | manufacturer | distributor | importer |
    # retailer | wholesaler | unclassified

    intent_level: str = db.Column(db.String(30), nullable=False, default="unknown")
    # high_intent | medium_intent | low_intent | unknown

    confidence_score: Optional[float] = db.Column(db.Float, nullable=True)
    reasoning: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Model Metadata ─────────────────────────────────────────────────────
    model_name: str = db.Column(db.String(100), nullable=False, default="gemini-1.5-flash")
    prompt_tokens: int = db.Column(db.Integer, default=0)
    response_tokens: int = db.Column(db.Integer, default=0)
    total_tokens: int = db.Column(db.Integer, default=0)

    # ── Status ─────────────────────────────────────────────────────────────
    # success | failed | retry
    status: str = db.Column(db.String(20), nullable=False, default="success")
    error_message: Optional[str] = db.Column(db.Text, nullable=True)

    classified_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────
    buyer = db.relationship("Buyer", back_populates="classifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "buyer_id": self.buyer_id,
            "buyer_type": self.buyer_type,
            "intent_level": self.intent_level,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "model_name": self.model_name,
            "total_tokens": self.total_tokens,
            "status": self.status,
            "classified_at": self.classified_at.isoformat() if self.classified_at else None,
        }

    def __repr__(self) -> str:
        return f"<Classification buyer={self.buyer_id} type={self.buyer_type!r}>"
