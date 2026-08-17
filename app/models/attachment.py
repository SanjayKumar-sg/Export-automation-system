"""
app/models/attachment.py — Uploadable file attachment model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.extensions import db


class Attachment(db.Model):
    """Represents an uploaded file (PDF/PPTX/DOCX) used in campaigns."""

    __tablename__ = "attachments"

    id: int = db.Column(db.Integer, primary_key=True)
    original_filename: str = db.Column(db.String(255), nullable=False)
    stored_filename: str = db.Column(db.String(255), nullable=False, unique=True)
    file_path: str = db.Column(db.String(512), nullable=False)
    file_size_bytes: int = db.Column(db.Integer, nullable=False)
    mime_type: str = db.Column(db.String(100), nullable=False)
    extension: str = db.Column(db.String(10), nullable=False)

    description: Optional[str] = db.Column(db.Text, nullable=True)
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)

    # ── Ownership ──────────────────────────────────────────────────────────
    uploaded_by: Optional[int] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )

    # ── Timestamps ─────────────────────────────────────────────────────────
    uploaded_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    @property
    def human_size(self) -> str:
        """Return human-readable file size."""
        size = self.file_size_bytes
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_size": self.human_size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "description": self.description,
            "is_active": self.is_active,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }

    def __repr__(self) -> str:
        return f"<Attachment {self.original_filename!r}>"
