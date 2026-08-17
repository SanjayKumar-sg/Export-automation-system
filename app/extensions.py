"""
app/extensions.py — Flask extension singletons.

All extensions are instantiated here without a bound app.
The app is bound later via init_app() in the application factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ── SQLAlchemy ORM ─────────────────────────────────────────────────────────
db: SQLAlchemy = SQLAlchemy()

# ── Flask-Migrate (Alembic) ────────────────────────────────────────────────
migrate: Migrate = Migrate()

# ── Flask-Login ────────────────────────────────────────────────────────────
login_manager: LoginManager = LoginManager()
login_manager.login_view = "auth.login"         # type: ignore[assignment]
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# ── CSRF Protection ────────────────────────────────────────────────────────
csrf: CSRFProtect = CSRFProtect()
