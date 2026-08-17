"""
app/routes/profile.py — User profile blueprint.
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def index():
    """User profile page."""
    return render_template("profile/index.html", user=current_user)


@profile_bp.route("/update", methods=["POST"])
@login_required
def update():
    """Update username and avatar."""
    data = request.get_json() or request.form.to_dict()
    username = data.get("username", "").strip()
    if username and username != current_user.username:
        current_user.username = username
    db.session.commit()
    if request.is_json:
        return jsonify({"status": "updated"})
    flash("Profile updated.", "success")
    return redirect(url_for("profile.index"))


@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change the current user's password."""
    data = request.get_json() or request.form
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")
    confirm_pw = data.get("confirm_password", "")

    if not current_user.check_password(current_pw):
        return jsonify({"status": "error", "message": "Current password is incorrect"}), 400
    if new_pw != confirm_pw:
        return jsonify({"status": "error", "message": "Passwords do not match"}), 400
    if len(new_pw) < 8:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters"}), 400

    current_user.set_password(new_pw)
    db.session.commit()
    return jsonify({"status": "ok", "message": "Password changed successfully"})
