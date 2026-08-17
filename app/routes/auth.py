"""
app/routes/auth.py — Authentication blueprint.

Handles login, logout, and session management with Flask-Login.
"""
from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint, flash, redirect, render_template,
    request, url_for, current_app
)
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models.user import User
from app.services.logging_service import LoggingService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page and form handler."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            LoggingService.log(
                event_type="user_login",
                description=f"User {user.email} logged in",
                user_id=user.id,
                ip_address=request.remote_addr,
            )

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password.", "danger")
        LoggingService.log(
            event_type="login_failed",
            description=f"Failed login attempt for {email}",
            ip_address=request.remote_addr,
        )

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the user out and clear the session."""
    LoggingService.log(
        event_type="user_logout",
        description=f"User {current_user.email} logged out",
        user_id=current_user.id,
    )
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
