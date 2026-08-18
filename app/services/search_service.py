"""
app/services/search_service.py — Orchestrates buyer search across adapters.

Runs adapters in sequence (optionally threaded), deduplicates results,
normalises records, and persists them to the database.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

from app.extensions import db
from app.models.buyer import Buyer
from app.models.history import History
from app.search import ADAPTER_MAP, BuyerRecord

logger = logging.getLogger("search")

# ── In-memory job state (one search at a time) ─────────────────────────────
_search_state: Dict[str, Any] = {
    "running": False,
    "paused": False,
    "cancelled": False,
    "progress": 0,
    "total": 0,
    "found": 0,
    "saved": 0,
    "current_source": "",
    "log": [],
    "errors": [],
}
_search_lock = threading.Lock()


def get_search_state() -> Dict[str, Any]:
    """Return a copy of the current search state (thread-safe)."""
    with _search_lock:
        return dict(_search_state)


class SearchService:
    """Coordinates buyer search across multiple source adapters."""

    @staticmethod
    def start_search(
        keyword: str,
        sources: List[str],
        max_results: int = 100,
        app=None,
    ) -> None:
        """Launch a background search thread."""
        with _search_lock:
            if _search_state["running"]:
                return  # Already running
            _search_state.update(
                running=True, paused=False, cancelled=False,
                progress=0, total=len(sources),
                found=0, saved=0, log=[], errors=[],
            )

        thread = threading.Thread(
            target=SearchService._run_search,
            args=(keyword, sources, max_results, app),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _run_search(keyword: str, sources: List[str], max_results: int, app) -> None:
        """Worker that runs each adapter and saves results."""
        from app import create_app  # deferred to avoid circular import

        # Use existing app context if provided
        ctx = app.app_context() if app else create_app().app_context()
        with ctx:
            all_records: List[BuyerRecord] = []

            for i, source in enumerate(sources):
                with _search_lock:
                    if _search_state["cancelled"]:
                        break
                    _search_state["current_source"] = source

                # Wait while paused
                while True:
                    with _search_lock:
                        if not _search_state["paused"] or _search_state["cancelled"]:
                            break
                    import time; time.sleep(0.5)

                AdapterClass = ADAPTER_MAP.get(source)
                if AdapterClass is None:
                    SearchService._log_msg(f"Unknown source: {source}", level="warning")
                    continue

                SearchService._log_msg(f"Searching {source}...")
                try:
                    adapter = AdapterClass(keyword=keyword, max_results=max_results // len(sources) + 10)
                    records = adapter.search()
                    if hasattr(adapter, 'errors') and adapter.errors:
                        for err in adapter.errors:
                            SearchService._log_msg(f"{source} warning/error: {err}", level="error")
                    all_records.extend(records)
                    SearchService._log_msg(
                        f"{source}: found {len(records)} raw records"
                    )
                except Exception as exc:
                    SearchService._log_msg(f"{source} error: {exc}", level="error")
                    with _search_lock:
                        _search_state["errors"].append(str(exc))

                with _search_lock:
                    _search_state["found"] = len(all_records)
                    _search_state["progress"] = i + 1

            # Deduplicate and save
            SearchService._log_msg("Saving results to database…")
            saved = SearchService._save_records(all_records, keyword)

            with _search_lock:
                _search_state["saved"] = saved
                _search_state["running"] = False
                _search_state["current_source"] = ""

            SearchService._log_msg(
                f"Search complete. Saved {saved} new buyers.", level="info"
            )

            # Audit log
            h = History(
                event_type="buyer_search",
                description=f"Search '{keyword}' across {sources} — saved {saved} buyers",
            )
            db.session.add(h)
            db.session.commit()

    @staticmethod
    def _save_records(records: List[BuyerRecord], keyword: str) -> int:
        """Deduplicate and persist buyer records. Returns count of new rows saved."""
        saved = 0
        seen_emails: set = set()

        # Collect existing emails from DB
        existing = {b.email for b in Buyer.query.with_entities(Buyer.email).all()}

        for rec in records:
            email = rec.email.strip().lower()
            if not email or email in seen_emails:
                continue
            seen_emails.add(email)

            if email in existing:
                # Mark as duplicate but don't skip — update flag
                dup = Buyer.query.filter_by(email=email).first()
                if dup:
                    dup.is_duplicate = True
                continue

            from app.search.country_utils import infer_country
            country_val = rec.country or infer_country(email=email, website=rec.website, company_name=rec.company_name)

            buyer = Buyer(
                email=email,
                buyer_name=rec.buyer_name,
                company_name=rec.company_name,
                website=rec.website,
                country=country_val,
                phone=rec.phone,
                source_platform=rec.source_platform,
                source_url=rec.source_url,
                search_keyword=keyword,
                email_status="unverified",
                buyer_type="unclassified",
            )
            db.session.add(buyer)
            existing.add(email)
            saved += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("DB commit error: %s", e)

        return saved

    @staticmethod
    def pause_search() -> None:
        with _search_lock:
            _search_state["paused"] = True

    @staticmethod
    def resume_search() -> None:
        with _search_lock:
            _search_state["paused"] = False

    @staticmethod
    def cancel_search() -> None:
        with _search_lock:
            _search_state["cancelled"] = True
            _search_state["running"] = False

    @staticmethod
    def _log_msg(msg: str, level: str = "info") -> None:
        with _search_lock:
            _search_state["log"].append(msg)
        getattr(logger, level)(msg)
