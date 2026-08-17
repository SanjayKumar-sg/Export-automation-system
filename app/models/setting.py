"""
app/models/setting.py — Application-wide key/value settings model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.extensions import db


class Setting(db.Model):
    """Stores configurable application settings as key/value pairs."""

    __tablename__ = "settings"

    id: int = db.Column(db.Integer, primary_key=True)
    key: str = db.Column(db.String(100), nullable=False, unique=True, index=True)
    value: Optional[str] = db.Column(db.Text, nullable=True)
    value_type: str = db.Column(
        db.String(20), nullable=False, default="string",
        comment="string | int | float | bool | json"
    )
    category: str = db.Column(db.String(50), nullable=False, default="general")
    description: Optional[str] = db.Column(db.Text, nullable=True)
    is_sensitive: bool = db.Column(db.Boolean, default=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ── Typed getter ───────────────────────────────────────────────────────

    def get_value(self) -> Any:
        """Return the stored value cast to its declared type."""
        import json

        if self.value is None:
            return None
        t = self.value_type
        if t == "int":
            return int(self.value)
        if t == "float":
            return float(self.value)
        if t == "bool":
            return self.value.lower() in ("true", "1", "yes")
        if t == "json":
            return json.loads(self.value)
        return self.value  # string (default)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Convenience class method: fetch and cast a setting by key."""
        row = cls.query.filter_by(key=key).first()
        if row is None:
            return default
        return row.get_value()

    @classmethod
    def set(cls, key: str, value: Any, **kwargs) -> "Setting":
        """Upsert a setting value."""
        row = cls.query.filter_by(key=key).first()
        if row is None:
            row = cls(key=key, **kwargs)
            db.session.add(row)
        row.value = str(value) if value is not None else None
        db.session.commit()
        return row

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": None if self.is_sensitive else self.value,
            "value_type": self.value_type,
            "category": self.category,
            "description": self.description,
        }

    def __repr__(self) -> str:
        return f"<Setting {self.key!r}>"
