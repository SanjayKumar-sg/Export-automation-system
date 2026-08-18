"""
app/routes/buyers.py — Buyer database blueprint.
"""
from __future__ import annotations

from flask import (
    Blueprint, jsonify, redirect, render_template,
    request, url_for, flash, current_app
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models.buyer import Buyer
from app.services.logging_service import LoggingService

buyers_bp = Blueprint("buyers", __name__, url_prefix="/buyers")


@buyers_bp.route("/")
@login_required
def index():
    """Buyer database listing page."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("q", "")
    country = request.args.get("country", "")
    status = request.args.get("status", "")
    buyer_type = request.args.get("buyer_type", "")

    # Auto-fill country for existing records missing country
    missing_country_buyers = Buyer.query.filter(
        db.or_(Buyer.country.is_(None), Buyer.country == "", Buyer.country == "—")
    ).all()
    if missing_country_buyers:
        from app.search.country_utils import infer_country
        for b in missing_country_buyers:
            b.country = infer_country(email=b.email, website=b.website, company_name=b.company_name)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    query = Buyer.query

    if search:
        query = query.filter(
            db.or_(
                Buyer.email.ilike(f"%{search}%"),
                Buyer.company_name.ilike(f"%{search}%"),
                Buyer.buyer_name.ilike(f"%{search}%"),
            )
        )
    if country:
        query = query.filter_by(country=country)
    if status:
        query = query.filter_by(email_status=status)
    if buyer_type:
        query = query.filter_by(buyer_type=buyer_type)

    pagination = query.order_by(Buyer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Filter options
    countries = [r[0] for r in db.session.query(Buyer.country).distinct().filter(Buyer.country.isnot(None)).all()]
    types = [r[0] for r in db.session.query(Buyer.buyer_type).distinct().all()]

    return render_template(
        "buyers/index.html",
        pagination=pagination,
        buyers=pagination.items,
        countries=countries,
        types=types,
        search=search,
        country=country,
        status=status,
        buyer_type=buyer_type,
    )


@buyers_bp.route("/api")
@login_required
def api_list():
    """JSON API endpoint for buyers datatable."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    q = request.args.get("q", "")

    query = Buyer.query
    if q:
        query = query.filter(
            db.or_(
                Buyer.email.ilike(f"%{q}%"),
                Buyer.company_name.ilike(f"%{q}%"),
            )
        )

    pagination = query.order_by(Buyer.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "buyers": [b.to_dict() for b in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    })


@buyers_bp.route("/<int:buyer_id>")
@login_required
def detail(buyer_id: int):
    """Single buyer detail view."""
    buyer = Buyer.query.get_or_404(buyer_id)
    return render_template("buyers/detail.html", buyer=buyer)


@buyers_bp.route("/<int:buyer_id>/delete", methods=["POST"])
@login_required
def delete(buyer_id: int):
    """Delete a single buyer record."""
    buyer = Buyer.query.get_or_404(buyer_id)
    db.session.delete(buyer)
    db.session.commit()
    LoggingService.log("buyer_deleted", f"Deleted buyer {buyer.email}", user_id=current_user.id)
    return jsonify({"status": "deleted"})


@buyers_bp.route("/bulk-delete", methods=["POST"])
@login_required
def bulk_delete():
    """Bulk delete buyers by ID list."""
    ids = request.get_json().get("ids", [])
    Buyer.query.filter(Buyer.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    LoggingService.log("bulk_delete", f"Deleted {len(ids)} buyers", user_id=current_user.id)
    return jsonify({"status": "ok", "deleted": len(ids)})


@buyers_bp.route("/export")
@login_required
def export_csv():
    """Export buyers as CSV download."""
    from app.services.report_service import ReportService
    import os
    from flask import send_file
    report = ReportService.generate_buyers_report(format="csv", user_id=current_user.id)
    return send_file(
        os.path.abspath(report.file_path),
        as_attachment=True,
        download_name="buyers.csv",
        mimetype="text/csv",
    )


@buyers_bp.route("/export/excel")
@login_required
def export_excel():
    """Export buyers as Excel download."""
    from app.services.report_service import ReportService
    import os
    from flask import send_file
    report = ReportService.generate_buyers_report(format="excel", user_id=current_user.id)
    return send_file(
        os.path.abspath(report.file_path),
        as_attachment=True,
        download_name="buyers.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
