"""
app/models/report.py — Generated report metadata model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Report(db.Model):
    """Tracks generated reports and their download locations."""

    __tablename__ = "reports"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(255), nullable=False)
    report_type: str = db.Column(
        db.String(50), nullable=False,
        comment="campaign | buyers | classification | validation | custom"
    )
    format: str = db.Column(
        db.String(10), nullable=False,
        comment="csv | excel | pdf | json"
    )
    file_path: Optional[str] = db.Column(db.String(512), nullable=True)
    file_size_bytes: Optional[int] = db.Column(db.Integer, nullable=True)

    # ── Filters applied ────────────────────────────────────────────────────
    filters_json: Optional[str] = db.Column(db.Text, nullable=True)

    # ── Summary Stats ──────────────────────────────────────────────────────
    total_records: int = db.Column(db.Integer, default=0)

    # ── Status ─────────────────────────────────────────────────────────────
    # pending | generating | ready | failed
    status: str = db.Column(db.String(20), nullable=False, default="pending")
    error_message: Optional[str] = db.Column(db.Text, nullable=True)

    campaign_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), nullable=True
    )
    created_by: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    campaign = db.relationship("Campaign", foreign_keys=[campaign_id])
    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "report_type": self.report_type,
            "format": self.format,
            "total_records": self.total_records,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Report {self.name!r} ({self.format})>"


class History(db.Model):
    """Audit log for all significant system events."""

    __tablename__ = "history"

    id: int = db.Column(db.Integer, primary_key=True)
    event_type: str = db.Column(db.String(50), nullable=False, index=True)
    description: str = db.Column(db.Text, nullable=False)
    entity_type: Optional[str] = db.Column(db.String(50), nullable=True)
    entity_id: Optional[int] = db.Column(db.Integer, nullable=True)
    extra_data: Optional[str] = db.Column(db.Text, nullable=True)  # JSON
    user_id: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    ip_address: Optional[str] = db.Column(db.String(45), nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "description": self.description,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<History {self.event_type!r}>"
