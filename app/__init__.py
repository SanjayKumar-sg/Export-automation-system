"""
app/__init__.py — Application factory.

Creates and configures the Flask application, registers all
blueprints, initialises extensions, sets up logging, and ensures
the database + default admin user exist on first run.
"""
from __future__ import annotations

import logging
import os
import mimetypes
from logging.handlers import RotatingFileHandler

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('text/javascript', '.js')

from flask import Flask

from app.config import get_config
from app.extensions import csrf, db, login_manager, migrate


def create_app() -> Flask:
    """Create and return the configured Flask application instance."""

    app = Flask(__name__, instance_relative_config=False)
    
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ── Load configuration ─────────────────────────────────────────────────
    cfg = get_config()
    app.config.from_object(cfg)

    # ── Ensure critical directories exist ──────────────────────────────────
    _ensure_directories(app)

    # ── Initialise extensions ──────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Register user loader ───────────────────────────────────────────────
    from app.models.user import User  # noqa: F401 (needed for login_manager)

    @login_manager.user_loader
    def load_user(user_id: str):  # type: ignore[return]
        return User.query.get(int(user_id))

    # ── Register blueprints ────────────────────────────────────────────────
    _register_blueprints(app)

    # ── Configure logging ──────────────────────────────────────────────────
    _configure_logging(app)

    # ── Create tables & seed defaults ─────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_defaults(app)

    # ── Global error handlers ──────────────────────────────────────────────
    _register_error_handlers(app)

    return app


# ── Private helpers ────────────────────────────────────────────────────────


def _ensure_directories(app: Flask) -> None:
    """Create runtime directories if they don't exist."""
    dirs = [
        app.config["UPLOAD_FOLDER"],
        app.config["LOG_DIR"],
        os.path.join(app.config["UPLOAD_FOLDER"], "attachments"),
        "app/database",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    """Import and register all route blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.search import search_bp
    from app.routes.buyers import buyers_bp
    from app.routes.validation import validation_bp
    from app.routes.classification import classification_bp
    from app.routes.campaigns import campaigns_bp
    from app.routes.send import send_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.logs import logs_bp
    from app.routes.templates_mgr import templates_bp
    from app.routes.attachments import attachments_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(buyers_bp)
    app.register_blueprint(validation_bp)
    app.register_blueprint(classification_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(send_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(templates_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(profile_bp)


def _configure_logging(app: Flask) -> None:
    """Set up rotating file handlers for each log category."""
    log_dir = app.config["LOG_DIR"]
    level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_files = {
        "app": "app.log",
        "search": "search.log",
        "email": "email.log",
        "error": "error.log",
        "audit": "audit.log",
    }

    for name, filename in log_files.items():
        handler = RotatingFileHandler(
            os.path.join(log_dir, filename),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        handler.setFormatter(fmt)
        handler.setLevel(level)
        logger = logging.getLogger(name)
        logger.setLevel(level)
        if not logger.handlers:
            logger.addHandler(handler)

    # Also attach to root Flask logger
    if not app.logger.handlers:
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        app.logger.addHandler(stream)
    app.logger.setLevel(level)


def _seed_defaults(app: Flask) -> None:
    """Create default admin user and settings on first run."""
    from app.models.user import User
    from app.models.setting import Setting
    from app.services.settings_service import SettingsService

    # Default admin user
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username="admin",
            email=app.config["ADMIN_EMAIL"],
            role="admin",
            is_active=True,
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Default admin user created: %s", app.config["ADMIN_EMAIL"])

    # Default settings
    SettingsService.seed_defaults()


def _register_error_handlers(app: Flask) -> None:
    """Register global HTTP error handlers."""
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("500 error: %s", str(e))
        return render_template("errors/500.html"), 500
