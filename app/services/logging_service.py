"""
app/services/logging_service.py — Application-wide structured logging service.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from app.extensions import db
from app.models.history import History

logger = logging.getLogger("audit")


class LoggingService:
    """
    Central service for creating audit log entries in the database.
    Wraps History model and also writes to the audit log file.
    """

    @staticmethod
    def log(
        event_type: str,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        extra_data: Optional[dict] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> History:
        """Create an audit log entry."""
        entry = History(
            event_type=event_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            extra_data=json.dumps(extra_data) if extra_data else None,
            user_id=user_id,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
        )
        try:
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to write audit log: %s", e)

        logger.info("[%s] %s (user=%s)", event_type, description, user_id)
        return entry

    @staticmethod
    def get_recent(limit: int = 100, event_type: Optional[str] = None):
        """Retrieve recent log entries, optionally filtered by event type."""
        query = History.query.order_by(History.created_at.desc())
        if event_type:
            query = query.filter_by(event_type=event_type)
        return query.limit(limit).all()

    @staticmethod
    def search_logs(
        query_str: str = "",
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50,
    ):
        """Paginated log search with optional filters."""
        q = History.query
        if query_str:
            q = q.filter(History.description.ilike(f"%{query_str}%"))
        if event_type:
            q = q.filter_by(event_type=event_type)
        if start_date:
            q = q.filter(History.created_at >= start_date)
        if end_date:
            q = q.filter(History.created_at <= end_date)
        return q.order_by(History.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def clear_old_logs(days: int = 90) -> int:
        """Delete log entries older than `days` days. Returns count deleted."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = History.query.filter(History.created_at < cutoff).delete()
        db.session.commit()
        logger.info("Cleared %d log entries older than %d days", count, days)
        return count
