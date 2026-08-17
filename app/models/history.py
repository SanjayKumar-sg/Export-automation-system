"""
app/models/history.py — Re-exports History from report.py for clean imports.
"""
from app.models.report import History  # noqa: F401

__all__ = ["History"]
