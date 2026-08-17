"""
app/search/base_adapter.py — Abstract base class for all search adapters.

Every source (Google, LinkedIn, etc.) must implement this interface.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("search")


@dataclass
class BuyerRecord:
    """Normalised buyer data returned by any adapter."""

    email: str
    buyer_name: Optional[str] = None
    company_name: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    source_platform: str = "unknown"
    source_url: Optional[str] = None
    search_keyword: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        # Normalise email to lowercase
        if self.email:
            self.email = self.email.strip().lower()


class BaseSearchAdapter(ABC):
    """Abstract adapter every search source must implement."""

    SOURCE_NAME: str = "base"

    def __init__(self, keyword: str, max_results: int = 50):
        self.keyword = keyword
        self.max_results = max_results
        self._results: List[BuyerRecord] = []
        self._errors: List[str] = []

    # ── Abstract interface ─────────────────────────────────────────────────

    @abstractmethod
    def search(self) -> List[BuyerRecord]:
        """Execute the search and return a list of BuyerRecord objects."""
        ...

    # ── Helpers shared by all adapters ─────────────────────────────────────

    def _make_headers(self) -> dict:
        """Return randomised browser-like HTTP headers."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        }

    def _log_error(self, msg: str) -> None:
        logger.error("[%s] %s", self.SOURCE_NAME, msg)
        self._errors.append(msg)

    def _log_info(self, msg: str) -> None:
        logger.info("[%s] %s", self.SOURCE_NAME, msg)

    @property
    def errors(self) -> List[str]:
        return list(self._errors)

    def _is_valid_email(self, email: str) -> bool:
        """Filter out common false positives and image files."""
        if not email:
            return False
        email = email.lower()
        invalid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".css", ".js")
        if email.endswith(invalid_extensions):
            return False
            
        invalid_strings = ["example", "domain.com", "youremail", "sentry", "wixpress", "email.com", "yourdomain"]
        if any(skip in email for skip in invalid_strings):
            return False
            
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} keyword={self.keyword!r}>"
