"""
app/routes/classification.py — AI Classification blueprint.
"""
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import login_required

from app.models.buyer import Buyer
from app.services.gemini_service import GeminiService, get_classify_state

classification_bp = Blueprint("classification", __name__, url_prefix="/classification")


@classification_bp.route("/")
@login_required
def index():
    """Classification overview page."""
    unclassified = Buyer.query.filter_by(
        buyer_type="unclassified", email_status="valid"
    ).count()
    classified = Buyer.query.filter(
        Buyer.buyer_type != "unclassified"
    ).count()
    return render_template(
        "classification/index.html",
        unclassified=unclassified,
        classified=classified,
    )


@classification_bp.route("/start", methods=["POST"])
@login_required
def start_classification():
    """Start Gemini classification job (AJAX)."""
    batch_size = request.get_json().get("batch_size", 20) if request.is_json else 20
    GeminiService.start_classification(
        batch_size=batch_size,
        app=current_app._get_current_object(),
    )
    return jsonify({"status": "started"})


@classification_bp.route("/status")
@login_required
def classification_status():
    """Return current classification job state (AJAX polling)."""
    return jsonify(get_classify_state())


@classification_bp.route("/stats")
@login_required
def stats():
    """Return classification distribution stats."""
    from sqlalchemy import func
    from app.extensions import db

    rows = (
        db.session.query(Buyer.buyer_type, func.count(Buyer.id))
        .group_by(Buyer.buyer_type)
        .all()
    )
    return jsonify({r[0]: r[1] for r in rows})
