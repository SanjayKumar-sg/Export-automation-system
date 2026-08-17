"""
app/routes/search.py — Buyer Search blueprint.
"""
from __future__ import annotations

from flask import (
    Blueprint, current_app, jsonify, render_template, request
)
from flask_login import login_required

from app.search import ADAPTER_MAP
from app.services.search_service import SearchService, get_search_state
from app.services.settings_service import SettingsService

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("/")
@login_required
def index():
    """Buyer search page."""
    keyword = SettingsService.get("default_keyword", "Singing Bowls")
    max_results = SettingsService.get("max_search_results", 100)
    sources = list(ADAPTER_MAP.keys())
    return render_template(
        "search/index.html",
        keyword=keyword,
        max_results=max_results,
        sources=sources,
    )


@search_bp.route("/start", methods=["POST"])
@login_required
def start_search():
    """Start a new buyer search (AJAX)."""
    data = request.get_json() or request.form
    keyword = data.get("keyword", "").strip() or SettingsService.get("default_keyword")
    max_results = int(data.get("max_results", 100))
    sources = data.getlist("sources") if hasattr(data, "getlist") else data.get("sources", list(ADAPTER_MAP.keys()))

    if not sources:
        sources = list(ADAPTER_MAP.keys())

    SearchService.start_search(
        keyword=keyword,
        sources=sources,
        max_results=max_results,
        app=current_app._get_current_object(),
    )
    return jsonify({"status": "started", "keyword": keyword, "sources": sources})


@search_bp.route("/status")
@login_required
def search_status():
    """Return current search job state (AJAX polling)."""
    return jsonify(get_search_state())


@search_bp.route("/pause", methods=["POST"])
@login_required
def pause_search():
    SearchService.pause_search()
    return jsonify({"status": "paused"})


@search_bp.route("/resume", methods=["POST"])
@login_required
def resume_search():
    SearchService.resume_search()
    return jsonify({"status": "resumed"})


@search_bp.route("/cancel", methods=["POST"])
@login_required
def cancel_search():
    SearchService.cancel_search()
    return jsonify({"status": "cancelled"})
