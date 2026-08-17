"""
app/services/report_service.py — Report generation service.

Generates CSV, Excel, and PDF reports from buyer and campaign data.
"""
from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from app.extensions import db
from app.models.buyer import Buyer
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.models.report import Report

logger = logging.getLogger("search")


class ReportService:
    """Generates and stores reports in multiple formats."""

    REPORTS_DIR = "app/assets/reports"

    @classmethod
    def _ensure_dir(cls) -> None:
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    # ── Buyer Report ───────────────────────────────────────────────────────

    @classmethod
    def generate_buyers_report(
        cls,
        format: str = "excel",
        filters: Optional[dict] = None,
        user_id: Optional[int] = None,
    ) -> Report:
        """Generate a buyers database report."""
        cls._ensure_dir()
        query = Buyer.query

        if filters:
            if filters.get("country"):
                query = query.filter(Buyer.country == filters["country"])
            if filters.get("status"):
                query = query.filter(Buyer.email_status == filters["status"])
            if filters.get("buyer_type"):
                query = query.filter(Buyer.buyer_type == filters["buyer_type"])

        buyers = query.all()
        data = [b.to_dict() for b in buyers]
        df = pd.DataFrame(data)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ext = "xlsx" if format == "excel" else format
        filename = f"buyers_{timestamp}.{ext}"
        filepath = os.path.join(cls.REPORTS_DIR, filename)

        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "excel":
            cls._write_excel(df, filepath, sheet_name="Buyers")
        elif format == "pdf":
            cls._write_pdf(df, filepath, title="Buyers Report")
        elif format == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=str)

        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        report = Report(
            name=f"Buyers Report {timestamp}",
            report_type="buyers",
            format=format,
            file_path=filepath,
            file_size_bytes=size,
            filters_json=json.dumps(filters or {}),
            total_records=len(buyers),
            status="ready",
            created_by=user_id,
        )
        db.session.add(report)
        db.session.commit()
        return report

    # ── Campaign Report ────────────────────────────────────────────────────

    @classmethod
    def generate_campaign_report(
        cls,
        campaign_id: int,
        format: str = "excel",
        user_id: Optional[int] = None,
    ) -> Report:
        """Generate a per-campaign send report."""
        cls._ensure_dir()
        logs = EmailLog.query.filter_by(campaign_id=campaign_id).all()
        data = [l.to_dict() for l in logs]
        df = pd.DataFrame(data)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ext = "xlsx" if format == "excel" else format
        filename = f"campaign_{campaign_id}_{timestamp}.{ext}"
        filepath = os.path.join(cls.REPORTS_DIR, filename)

        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "excel":
            cls._write_excel(df, filepath, sheet_name="Campaign Emails")
        elif format == "pdf":
            cls._write_pdf(df, filepath, title=f"Campaign {campaign_id} Report")

        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        report = Report(
            name=f"Campaign {campaign_id} Report {timestamp}",
            report_type="campaign",
            format=format,
            file_path=filepath,
            file_size_bytes=size,
            total_records=len(logs),
            campaign_id=campaign_id,
            status="ready",
            created_by=user_id,
        )
        db.session.add(report)
        db.session.commit()
        return report

    # ── Dashboard Stats ────────────────────────────────────────────────────

    @staticmethod
    def get_dashboard_stats() -> dict:
        """Return aggregated stats for the dashboard cards and charts."""
        from sqlalchemy import func
        from datetime import date

        total_buyers = Buyer.query.count()
        business_emails = Buyer.query.filter_by(buyer_type="business").count()
        individual_emails = Buyer.query.filter_by(buyer_type="individual").count()
        valid_emails = Buyer.query.filter_by(email_status="valid").count()
        invalid_emails = Buyer.query.filter_by(email_status="invalid").count()
        duplicate_removed = Buyer.query.filter_by(is_duplicate=True).count()

        today = datetime.utcnow().date()
        sent_today = EmailLog.query.filter(
            func.date(EmailLog.sent_at) == today,
            EmailLog.status == "sent",
        ).count()
        failed_today = EmailLog.query.filter(
            func.date(EmailLog.sent_at) == today,
            EmailLog.status == "failed",
        ).count()
        pending = Buyer.query.filter_by(campaign_status="pending", email_status="valid").count()

        # Source distribution
        source_rows = (
            db.session.query(Buyer.source_platform, func.count(Buyer.id))
            .group_by(Buyer.source_platform)
            .all()
        )
        source_dist = {r[0]: r[1] for r in source_rows}

        # Country distribution (top 10)
        country_rows = (
            db.session.query(Buyer.country, func.count(Buyer.id))
            .filter(Buyer.country.isnot(None))
            .group_by(Buyer.country)
            .order_by(func.count(Buyer.id).desc())
            .limit(10)
            .all()
        )
        country_dist = {r[0]: r[1] for r in country_rows}

        # Classification distribution
        class_rows = (
            db.session.query(Buyer.buyer_type, func.count(Buyer.id))
            .group_by(Buyer.buyer_type)
            .all()
        )
        class_dist = {r[0]: r[1] for r in class_rows}

        # Daily sends (last 7 days)
        daily_rows = (
            db.session.query(
                func.date(EmailLog.sent_at).label("day"),
                func.count(EmailLog.id).label("count")
            )
            .filter(EmailLog.status == "sent")
            .group_by(func.date(EmailLog.sent_at))
            .order_by(func.date(EmailLog.sent_at).desc())
            .limit(7)
            .all()
        )
        daily_sends = [{"date": str(r.day), "count": r.count} for r in reversed(daily_rows)]

        return {
            "total_buyers": total_buyers,
            "business_emails": business_emails,
            "individual_emails": individual_emails,
            "valid_emails": valid_emails,
            "invalid_emails": invalid_emails,
            "duplicate_removed": duplicate_removed,
            "sent_today": sent_today,
            "failed_today": failed_today,
            "pending": pending,
            "source_distribution": source_dist,
            "country_distribution": country_dist,
            "classification_distribution": class_dist,
            "daily_sends": daily_sends,
        }

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _write_excel(df: pd.DataFrame, filepath: str, sheet_name: str = "Data") -> None:
        """Write a DataFrame to Excel with auto-column widths."""
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

    @staticmethod
    def _write_pdf(df: pd.DataFrame, filepath: str, title: str = "Report") -> None:
        """Write a DataFrame to a styled PDF."""
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=1 * cm, leftMargin=1 * cm,
            topMargin=1.5 * cm, bottomMargin=1 * cm,
        )
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.5 * cm))

        if df.empty:
            elements.append(Paragraph("No data available.", styles["Normal"]))
        else:
            # Take first 20 columns and 1000 rows to keep PDF manageable
            df_slice = df.iloc[:1000, :20]
            headers = list(df_slice.columns)
            table_data = [headers] + df_slice.fillna("").values.tolist()

            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 3),
                ])
            )
            elements.append(tbl)

        doc.build(elements)
