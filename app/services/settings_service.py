"""
app/services/settings_service.py — Application settings management service.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.extensions import db
from app.models.setting import Setting

logger = logging.getLogger("search")

# ── Default settings definitions ───────────────────────────────────────────
DEFAULT_SETTINGS: List[Dict[str, Any]] = [
    # General
    {"key": "default_keyword",    "value": "Singing Bowls",  "value_type": "string",  "category": "search",    "description": "Default product keyword for buyer search"},
    {"key": "max_search_results", "value": "100",            "value_type": "int",     "category": "search",    "description": "Maximum results per search run"},
    # Email
    {"key": "daily_send_limit",   "value": "200",            "value_type": "int",     "category": "email",     "description": "Maximum emails to send per day"},
    {"key": "send_delay_seconds", "value": "3",              "value_type": "int",     "category": "email",     "description": "Delay (seconds) between emails"},
    {"key": "email_sender",       "value": "",               "value_type": "string",  "category": "email",     "description": "Gmail sender address",           "is_sensitive": True},
    {"key": "email_password",     "value": "",               "value_type": "string",  "category": "email",     "description": "Gmail app password",             "is_sensitive": True},
    # Gemini / Groq / Serper
    {"key": "gemini_api_key",     "value": "",               "value_type": "string",  "category": "ai",        "description": "Gemini API key",                 "is_sensitive": True},
    {"key": "groq_api_key",       "value": "",               "value_type": "string",  "category": "ai",        "description": "Secondary Groq API key",         "is_sensitive": True},
    {"key": "serper_api_key",     "value": "",               "value_type": "string",  "category": "search",    "description": "Serper (Google Search) API key", "is_sensitive": True},
    {"key": "gemini_model",       "value": "gemini-1.5-flash","value_type": "string", "category": "ai",        "description": "Gemini model name"},
    {"key": "gemini_batch_size",  "value": "20",             "value_type": "int",     "category": "ai",        "description": "Classification batch size"},
    # UI
    {"key": "theme",              "value": "dark",           "value_type": "string",  "category": "ui",        "description": "UI theme: dark | light"},
    {"key": "company_name",       "value": "Export Company", "value_type": "string",  "category": "ui",        "description": "Company name shown in header"},
    # Upload
    {"key": "max_upload_mb",      "value": "10",             "value_type": "int",     "category": "upload",    "description": "Maximum file upload size in MB"},
    # Backup
    {"key": "auto_backup",        "value": "false",          "value_type": "bool",    "category": "backup",    "description": "Enable automatic database backups"},
    {"key": "backup_interval_hours","value": "24",           "value_type": "int",     "category": "backup",    "description": "Hours between automatic backups"},
]


class SettingsService:
    """CRUD service for application settings."""

    @staticmethod
    def seed_defaults() -> None:
        """Insert default settings if they don't already exist."""
        for s in DEFAULT_SETTINGS:
            if not Setting.query.filter_by(key=s["key"]).first():
                setting = Setting(
                    key=s["key"],
                    value=s.get("value"),
                    value_type=s.get("value_type", "string"),
                    category=s.get("category", "general"),
                    description=s.get("description"),
                    is_sensitive=s.get("is_sensitive", False),
                )
                db.session.add(setting)
        db.session.commit()

    @staticmethod
    def get_all() -> List[Setting]:
        return Setting.query.order_by(Setting.category, Setting.key).all()

    @staticmethod
    def get_by_category(category: str) -> List[Setting]:
        return Setting.query.filter_by(category=category).all()

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return Setting.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> Setting:
        return Setting.set(key, value)

    @staticmethod
    def update_many(updates: Dict[str, Any]) -> None:
        """Batch-update multiple settings at once."""
        for key, value in updates.items():
            row = Setting.query.filter_by(key=key).first()
            if row:
                row.value = str(value) if value is not None else None
        db.session.commit()

    @staticmethod
    def export_settings() -> str:
        """Export all non-sensitive settings as JSON string."""
        rows = Setting.query.filter_by(is_sensitive=False).all()
        data = {r.key: r.value for r in rows}
        return json.dumps(data, indent=2)

    @staticmethod
    def import_settings(json_str: str) -> int:
        """Import settings from a JSON string. Returns count updated."""
        data = json.loads(json_str)
        count = 0
        for key, value in data.items():
            row = Setting.query.filter_by(key=key).first()
            if row and not row.is_sensitive:
                row.value = str(value)
                count += 1
        db.session.commit()
        return count
