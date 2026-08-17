"""
app/routes/attachments.py — File attachment blueprint.
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.services.attachment_service import AttachmentService
from app.services.settings_service import SettingsService

attachments_bp = Blueprint("attachments", __name__, url_prefix="/attachments")


@attachments_bp.route("/")
@login_required
def index():
    """Attachments manager page."""
    attachments = AttachmentService.get_all()
    max_mb = SettingsService.get("max_upload_mb", 10)
    return render_template(
        "attachments/index.html",
        attachments=attachments,
        max_mb=max_mb,
    )


@attachments_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Handle file upload."""
    file = request.files.get("file")
    description = request.form.get("description", "")
    max_mb = int(SettingsService.get("max_upload_mb", 10))

    attachment, error = AttachmentService.upload(
        file=file,
        description=description,
        user_id=current_user.id,
        max_mb=max_mb,
    )
    if error:
        return jsonify({"status": "error", "message": error}), 400

    return jsonify({
        "status": "uploaded",
        "attachment": attachment.to_dict(),
    })


@attachments_bp.route("/<int:attachment_id>/delete", methods=["POST"])
@login_required
def delete(attachment_id: int):
    """Delete (soft) an attachment."""
    success = AttachmentService.delete(attachment_id)
    return jsonify({"status": "deleted" if success else "not_found"})


@attachments_bp.route("/api")
@login_required
def api_list():
    """Return all active attachments as JSON."""
    attachments = AttachmentService.get_all()
    return jsonify({"attachments": [a.to_dict() for a in attachments]})
