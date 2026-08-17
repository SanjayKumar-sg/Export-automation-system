"""
app/routes/settings.py — Application settings blueprint.
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.services.settings_service import SettingsService

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def index():
    """Settings page."""
    all_settings = SettingsService.get_all()
    # Group by category
    grouped = {}
    for s in all_settings:
        grouped.setdefault(s.category, []).append(s)
    return render_template("settings/index.html", grouped=grouped)


@settings_bp.route("/save", methods=["POST"])
@login_required
def save():
    """Save settings from the form (AJAX or form submission)."""
    data = request.get_json() or request.form.to_dict()
    # Remove Flask internals
    data.pop("csrf_token", None)
    SettingsService.update_many(data)
    if request.is_json:
        return jsonify({"status": "saved"})
    flash("Settings saved successfully.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/export")
@login_required
def export():
    """Export non-sensitive settings as JSON."""
    from flask import Response
    json_str = SettingsService.export_settings()
    return Response(json_str, mimetype="application/json",
                    headers={"Content-Disposition": "attachment;filename=settings.json"})


@settings_bp.route("/import", methods=["POST"])
@login_required
def import_settings():
    """Import settings from a JSON file upload."""
    file = request.files.get("settings_file")
    if not file:
        return jsonify({"error": "No file provided"}), 400
    content = file.read().decode("utf-8")
    count = SettingsService.import_settings(content)
    return jsonify({"status": "imported", "count": count})


@settings_bp.route("/backup", methods=["POST"])
@login_required
def backup_db():
    """Create a database backup."""
    import shutil, os
    from datetime import datetime
    from flask import current_app
    src = "export_automation.db"
    if not os.path.exists(src):
        # Try instance folder
        src = os.path.join("instance", "export_automation.db")
    if not os.path.exists(src):
        return jsonify({"error": "Database file not found"}), 404

    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backup_dir, f"backup_{ts}.db")
    shutil.copy2(src, dest)
    return jsonify({"status": "ok", "file": dest})
