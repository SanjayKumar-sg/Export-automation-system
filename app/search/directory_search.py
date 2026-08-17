"""
app/search/directory_search.py — Business directory search adapter.

Searches directories such as Alibaba, TradeIndia, ExportHub, and
GlobalSources for buyers matching the keyword.
"""
from __future__ import annotations

import re
import time
from typing import List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from app.search.base_adapter import BaseSearchAdapter, BuyerRecord


class DirectorySearchAdapter(BaseSearchAdapter):
    """Search business directories for buyer contacts."""

    SOURCE_NAME = "directory"
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    # Directory search URL templates (query is URL-encoded keyword)
    DIRECTORIES = [
        ("ExportHub",  "https://www.exporthub.com/search/?q={query}&type=buyer"),
        ("Tradeford",  "https://www.tradeford.com/buyers/?kw={query}"),
        ("EC21",       "https://www.ec21.com/wanted/?search={query}"),
        ("TradeWheel", "https://www.tradewheel.com/buy-offers/search/?q={query}"),
    ]

    def search(self) -> List[BuyerRecord]:
        self._log_info(f"Starting directory search for: {self.keyword!r}")
        results: List[BuyerRecord] = []
        encoded = quote_plus(self.keyword)

        for name, url_tpl in self.DIRECTORIES:
            if len(results) >= self.max_results:
                break
            url = url_tpl.format(query=encoded)
            try:
                records = self._scrape_directory(name, url)
                results.extend(records)
                self._log_info(f"[{name}] Found {len(records)} records.")
                time.sleep(2)
            except Exception as e:
                self._log_error(f"[{name}] Error: {e}")

        self._log_info(f"Directory search complete. Total: {len(results)}")
        return results[: self.max_results]

    def _scrape_directory(self, dir_name: str, url: str) -> List[BuyerRecord]:
        """Scrape a single directory page for buyer contacts."""
        records: List[BuyerRecord] = []
        try:
            resp = requests.get(
                url, headers=self._make_headers(), timeout=20, allow_redirects=True
            )
            soup = BeautifulSoup(resp.text, "lxml")
            text = soup.get_text(" ", strip=True)

            # Extract all emails visible on the listing page
            emails = set(self.EMAIL_RE.findall(text))

            # Try to find company names near email entries
            for email in emails:
                if not self._is_valid_email(email):
                    continue

                # Attempt to extract a nearby company name from the HTML
                company = self._extract_company_near_email(soup, email)
                country = self._extract_country(text)

                records.append(
                    BuyerRecord(
                        email=email,
                        company_name=company,
                        country=country,
                        source_platform=self.SOURCE_NAME,
                        source_url=url,
                        search_keyword=self.keyword,
                        extra={"directory": dir_name},
                    )
                )
        except Exception as e:
            self._log_error(f"Scrape error [{dir_name}] {url}: {e}")
        return records

    def _extract_company_near_email(self, soup: BeautifulSoup, email: str) -> str | None:
        """Try to find company name adjacent to the email in the DOM."""
        # Look for the email string in the page and climb up the DOM
        text_node = soup.find(string=re.compile(re.escape(email), re.I))
        if text_node:
            parent = text_node.parent
            for _ in range(4):  # Walk up 4 levels
                if parent is None:
                    break
                for heading in parent.find_all(["h1", "h2", "h3", "strong", "b"]):
                    name = heading.get_text(strip=True)
                    if name and len(name) > 3:
                        return name
                parent = parent.parent
        return None

    def _extract_country(self, text: str) -> str | None:
        """Heuristically extract a country name from page text."""
        # Common countries in export context
        countries = [
            "USA", "United States", "UK", "United Kingdom", "Germany", "France",
            "Australia", "Canada", "Japan", "China", "India", "Italy", "Netherlands",
            "Spain", "Brazil", "Mexico", "South Korea", "Singapore", "UAE",
        ]
        for country in countries:
            if country.lower() in text.lower():
                return country
        return None
