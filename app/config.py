"""
app/config.py — Configuration classes for all environments.

Reads all sensitive values from environment variables / .env file.
Never hardcode secrets here.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=7)

    # ── Database ───────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///export_automation.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False

    # ── CSRF ───────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED: bool = os.environ.get("WTF_CSRF_ENABLED", "True") == "True"
    WTF_CSRF_TIME_LIMIT: int = 3600

    # ── File Uploads ───────────────────────────────────────────────────────
    MAX_UPLOAD_MB: int = int(os.environ.get("MAX_UPLOAD_MB", 10))
    MAX_CONTENT_LENGTH: int = MAX_UPLOAD_MB * 1024 * 1024
    UPLOAD_FOLDER: str = os.environ.get("UPLOAD_FOLDER", "app/assets")
    ALLOWED_EXTENSIONS: set = {"pdf", "pptx", "docx"}

    # ── Gmail SMTP ─────────────────────────────────────────────────────────
    GMAIL_SENDER: str = os.environ.get("GMAIL_SENDER", "")
    GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = True
    MAIL_DEFAULT_SENDER: str = os.environ.get("MAIL_DEFAULT_SENDER", "")

    # ── AI & Search Providers ──────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    SERPER_API_KEY: str = os.environ.get("SERPER_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_BATCH_SIZE: int = 20
    GEMINI_MAX_RETRIES: int = 3

    # ── Search Defaults ────────────────────────────────────────────────────
    DEFAULT_KEYWORD: str = os.environ.get("DEFAULT_KEYWORD", "Singing Bowls")
    MAX_SEARCH_RESULTS: int = int(os.environ.get("MAX_SEARCH_RESULTS", 100))

    # ── Email Campaign ─────────────────────────────────────────────────────
    DAILY_SEND_LIMIT: int = int(os.environ.get("DAILY_SEND_LIMIT", 200))
    SEND_DELAY_SECONDS: int = int(os.environ.get("SEND_DELAY_SECONDS", 3))

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.environ.get("LOG_DIR", "logs")

    # ── Admin ──────────────────────────────────────────────────────────────
    ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "Admin@1234")


class DevelopmentConfig(Config):
    """Development configuration with debug enabled."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False


class ProductionConfig(Config):
    """Production configuration with security hardened."""

    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    WTF_CSRF_SSL_STRICT: bool = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False


# Environment → Config class mapping
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

def get_config() -> Config:
    """Return the appropriate config based on FLASK_ENV."""
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
