"""
app/routes/validation.py — Email validation blueprint.
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.models.buyer import Buyer
from app.services.validation_service import ValidationService

validation_bp = Blueprint("validation", __name__, url_prefix="/validation")


@validation_bp.route("/")
@login_required
def index():
    """Validation overview page."""
    stats = ValidationService.get_validation_stats()
    return render_template("validation/index.html", stats=stats)


@validation_bp.route("/run", methods=["POST"])
@login_required
def run_validation():
    """Run email validation on all unverified buyers (AJAX)."""
    stats = ValidationService.validate_all()
    return jsonify({"status": "complete", "stats": stats})


@validation_bp.route("/revalidate/<int:buyer_id>", methods=["POST"])
@login_required
def revalidate(buyer_id: int):
    """Revalidate a single buyer's email."""
    result = ValidationService.revalidate_buyer(buyer_id)
    return jsonify(result)


@validation_bp.route("/stats")
@login_required
def stats():
    """Return validation statistics as JSON."""
    return jsonify(ValidationService.get_validation_stats())


@validation_bp.route("/buyers")
@login_required
def buyers_list():
    """Return buyers grouped by validation status (AJAX)."""
    status = request.args.get("status", "")
    query = Buyer.query
    if status:
        query = query.filter_by(email_status=status)
    buyers = query.order_by(Buyer.created_at.desc()).limit(200).all()
    return jsonify({"buyers": [b.to_dict() for b in buyers]})
