"""
app/routes/dashboard.py — Dashboard blueprint.
"""
from flask import Blueprint, jsonify, render_template
from flask_login import login_required

from app.services.report_service import ReportService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Main dashboard page."""
    stats = ReportService.get_dashboard_stats()
    return render_template("dashboard/index.html", stats=stats)


@dashboard_bp.route("/api/dashboard/stats")
@login_required
def api_stats():
    """JSON endpoint for live dashboard stats refresh."""
    stats = ReportService.get_dashboard_stats()
    return jsonify(stats)
