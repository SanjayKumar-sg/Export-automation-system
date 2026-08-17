"""
app/services/attachment_service.py — File attachment upload and management.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models.attachment import Attachment

logger = logging.getLogger("search")

ALLOWED_EXTENSIONS = {"pdf", "pptx", "docx"}
MIME_MAP = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class AttachmentService:
    """Handles secure file uploads, validation, and storage."""

    UPLOAD_DIR = "app/assets/attachments"

    @classmethod
    def _ensure_dir(cls) -> None:
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)

    @classmethod
    def upload(
        cls,
        file: FileStorage,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        max_mb: int = 10,
    ) -> Tuple[Optional[Attachment], Optional[str]]:
        """
        Validate and store an uploaded file.

        Returns:
            (Attachment, None) on success
            (None, error_message) on failure
        """
        cls._ensure_dir()

        if not file or not file.filename:
            return None, "No file provided"

        original_name = file.filename
        ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

        if ext not in ALLOWED_EXTENSIONS:
            return None, f"File type '.{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Read content to check size
        content = file.read()
        size_bytes = len(content)
        max_bytes = max_mb * 1024 * 1024

        if size_bytes > max_bytes:
            return None, f"File size {size_bytes / 1024 / 1024:.1f} MB exceeds limit of {max_mb} MB"

        # Generate unique stored filename
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(cls.UPLOAD_DIR, stored_name)

        # Write to disk
        with open(filepath, "wb") as f:
            f.write(content)

        mime = MIME_MAP.get(ext, "application/octet-stream")
        attachment = Attachment(
            original_filename=original_name,
            stored_filename=stored_name,
            file_path=filepath,
            file_size_bytes=size_bytes,
            mime_type=mime,
            extension=ext,
            description=description,
            uploaded_by=user_id,
        )
        db.session.add(attachment)
        db.session.commit()

        logger.info("Attachment uploaded: %s → %s", original_name, stored_name)
        return attachment, None

    @classmethod
    def delete(cls, attachment_id: int) -> bool:
        """Soft-delete an attachment (mark is_active=False)."""
        att = Attachment.query.get(attachment_id)
        if not att:
            return False
        att.is_active = False
        db.session.commit()
        return True

    @classmethod
    def get_all(cls, active_only: bool = True):
        """Return all attachments, optionally only active ones."""
        q = Attachment.query
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(Attachment.uploaded_at.desc()).all()
