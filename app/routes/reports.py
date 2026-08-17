"""
app/routes/reports.py — Reports blueprint.
"""
import os

from flask import Blueprint, jsonify, render_template, request, send_file
from flask_login import current_user, login_required

from app.models.report import Report
from app.services.report_service import ReportService

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    """Reports overview page."""
    reports = Report.query.order_by(Report.created_at.desc()).limit(50).all()
    stats = ReportService.get_dashboard_stats()
    return render_template("reports/index.html", reports=reports, stats=stats)


@reports_bp.route("/generate/buyers", methods=["POST"])
@login_required
def gen_buyers():
    """Generate a buyers report."""
    data = request.get_json() or {}
    fmt = data.get("format", "excel")
    filters = data.get("filters", {})
    report = ReportService.generate_buyers_report(
        format=fmt, filters=filters, user_id=current_user.id
    )
    return jsonify({"status": "ready", "report_id": report.id, "format": fmt})


@reports_bp.route("/generate/campaign/<int:campaign_id>", methods=["POST"])
@login_required
def gen_campaign(campaign_id: int):
    """Generate a campaign report."""
    data = request.get_json() or {}
    fmt = data.get("format", "excel")
    report = ReportService.generate_campaign_report(
        campaign_id=campaign_id, format=fmt, user_id=current_user.id
    )
    return jsonify({"status": "ready", "report_id": report.id})


@reports_bp.route("/download/<int:report_id>")
@login_required
def download(report_id: int):
    """Download a generated report file."""
    report = Report.query.get_or_404(report_id)
    if not report.file_path or not os.path.exists(report.file_path):
        return jsonify({"error": "Report file not found"}), 404

    mime_map = {
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
        "json": "application/json",
    }
    return send_file(
        os.path.abspath(report.file_path),
        as_attachment=True,
        download_name=os.path.basename(report.file_path),
        mimetype=mime_map.get(report.format, "application/octet-stream"),
    )


@reports_bp.route("/api/stats")
@login_required
def api_stats():
    """Return dashboard stats for charts."""
    return jsonify(ReportService.get_dashboard_stats())
