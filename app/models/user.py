"""
app/models/user.py — User account model with role-based access control.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    """Represents a system user with role-based access."""

    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    role: str = db.Column(
        db.String(20),
        nullable=False,
        default="operator",
        comment="admin | operator | viewer",
    )
    is_active: bool = db.Column(db.Boolean, default=True, nullable=False)
    avatar_url: Optional[str] = db.Column(db.String(512), nullable=True)
    last_login: Optional[datetime] = db.Column(db.DateTime, nullable=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # ── Password helpers ───────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash and store a plaintext password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if the plaintext password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ── Role helpers ───────────────────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_operator(self) -> bool:
        return self.role in ("admin", "operator")

    # ── Flask-Login interface ──────────────────────────────────────────────

    def get_id(self) -> str:
        return str(self.id)

    # ── Representation ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username!r} ({self.role})>"
