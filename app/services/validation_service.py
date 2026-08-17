"""
app/services/validation_service.py — Email validation logic.

Validates emails using regex, domain MX checks, and disposable
email domain detection. Marks status without deleting any records.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.extensions import db
from app.models.buyer import Buyer

logger = logging.getLogger("search")

# ── Regex ──────────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# ── Known disposable email domains ────────────────────────────────────────
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "trashmail.com",
    "tempmail.com", "throwaway.email", "yopmail.com", "maildrop.cc",
    "sharklasers.com", "spam4.me", "fakeinbox.com", "dispostable.com",
    "tempr.email", "10minutemail.com", "minutemail.com",
}

# ── Role-based email prefixes (generic, not personal) ─────────────────────
ROLE_PREFIXES = {
    "admin", "info", "contact", "support", "help", "noreply",
    "no-reply", "webmaster", "postmaster",
}


class ValidationService:
    """Validates and categorises buyer email addresses."""

    @staticmethod
    def validate_all(batch_size: int = 500) -> dict:
        """Run validation on all unverified buyers. Returns summary stats."""
        buyers = Buyer.query.filter(
            Buyer.email_status.in_(["unverified"])
        ).all()

        stats = {"total": len(buyers), "valid": 0, "invalid": 0,
                 "duplicate": 0, "disposable": 0}

        for buyer in buyers:
            status, error = ValidationService.validate_email(buyer.email)
            buyer.email_status = status
            buyer.validation_error = error
            stats[status if status in stats else "invalid"] += 1

        # Mark duplicates
        dup_count = ValidationService.mark_duplicates()
        stats["duplicate"] = dup_count

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Validation commit error: %s", e)

        logger.info("Validation complete: %s", stats)
        return stats

    @staticmethod
    def validate_email(email: str) -> tuple[str, Optional[str]]:
        """
        Validate a single email address.

        Returns:
            (status, error_message) where status is one of:
            valid | invalid | disposable | missing
        """
        if not email or not email.strip():
            return "missing", "Email is empty"

        email = email.strip().lower()

        # Regex check
        if not _EMAIL_RE.match(email):
            return "invalid", "Failed regex validation"

        # Split local and domain
        try:
            local, domain = email.rsplit("@", 1)
        except ValueError:
            return "invalid", "Malformed email (no @)"

        # Disposable domain check
        if domain in DISPOSABLE_DOMAINS:
            return "disposable", f"Disposable email domain: {domain}"

        # MX record check (optional — requires dnspython)
        if not ValidationService._has_mx_record(domain):
            return "invalid", f"No MX record found for domain: {domain}"

        return "valid", None

    @staticmethod
    def _has_mx_record(domain: str) -> bool:
        """Return True if the domain has at least one MX record."""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX", lifetime=5)
            return bool(answers)
        except Exception:
            # If DNS check fails (offline, etc.), assume valid to avoid false negatives
            return True

    @staticmethod
    def mark_duplicates() -> int:
        """Identify and flag duplicate emails. Returns count of duplicates marked."""
        from sqlalchemy import func

        # Find emails that appear more than once
        dup_query = (
            db.session.query(Buyer.email, func.count(Buyer.id).label("cnt"))
            .group_by(Buyer.email)
            .having(func.count(Buyer.id) > 1)
            .all()
        )

        count = 0
        for email, _ in dup_query:
            buyers = Buyer.query.filter_by(email=email).order_by(Buyer.created_at).all()
            # Keep the first (earliest), mark the rest as duplicates
            for dup_buyer in buyers[1:]:
                dup_buyer.is_duplicate = True
                dup_buyer.email_status = "duplicate"
                dup_buyer.duplicate_of_id = buyers[0].id
                count += 1

        db.session.commit()
        return count

    @staticmethod
    def revalidate_buyer(buyer_id: int) -> dict:
        """Revalidate a single buyer by ID."""
        buyer = Buyer.query.get(buyer_id)
        if not buyer:
            return {"error": "Buyer not found"}
        status, error = ValidationService.validate_email(buyer.email)
        buyer.email_status = status
        buyer.validation_error = error
        db.session.commit()
        return {"id": buyer_id, "status": status, "error": error}

    @staticmethod
    def get_validation_stats() -> dict:
        """Return a summary of email validation statuses."""
        from sqlalchemy import func

        rows = (
            db.session.query(Buyer.email_status, func.count(Buyer.id))
            .group_by(Buyer.email_status)
            .all()
        )
        return {status: count for status, count in rows}
