"""
app/routes/logs.py — System logs blueprint.
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.services.logging_service import LoggingService

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")

EVENT_TYPES = [
    "user_login", "user_logout", "login_failed",
    "buyer_search", "buyer_deleted", "bulk_delete",
    "campaign_start", "campaign_stop", "email_sent", "email_failed",
    "classification_complete", "validation_complete",
    "attachment_upload", "settings_saved", "report_generated",
]


@logs_bp.route("/")
@login_required
def index():
    """System logs page."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    event_type = request.args.get("event_type", "")

    pagination = LoggingService.search_logs(
        query_str=q, event_type=event_type, page=page, per_page=50
    )
    return render_template(
        "logs/index.html",
        pagination=pagination,
        logs=pagination.items,
        q=q,
        event_type=event_type,
        event_types=EVENT_TYPES,
    )


@logs_bp.route("/api")
@login_required
def api_list():
    """JSON endpoint for logs (AJAX pagination)."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    event_type = request.args.get("event_type", "")
    pagination = LoggingService.search_logs(
        query_str=q, event_type=event_type, page=page, per_page=50
    )
    return jsonify({
        "logs": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    })


@logs_bp.route("/clear", methods=["POST"])
@login_required
def clear():
    """Clear logs older than N days."""
    days = request.get_json().get("days", 90)
    count = LoggingService.clear_old_logs(days=int(days))
    return jsonify({"status": "ok", "deleted": count})
