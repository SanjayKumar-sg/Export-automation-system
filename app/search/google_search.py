"""
app/search/google_search.py — Google/Bing web search adapter.

Uses public search results via requests + BeautifulSoup to find
buyers matching the keyword. Extracts emails from result pages.
"""
from __future__ import annotations

import re
import time
from typing import List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.search.base_adapter import BaseSearchAdapter, BuyerRecord


class GoogleSearchAdapter(BaseSearchAdapter):
    """Search buyers via Google (web scraping of public results)."""

    SOURCE_NAME = "google"

    # Email regex pattern
    EMAIL_RE = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )

    def search(self) -> List[BuyerRecord]:
        """Run Google search and extract buyer emails from result pages."""
        self._log_info(f"Starting Google search for: {self.keyword!r}")
        results: List[BuyerRecord] = []
        queries = self._build_queries()

        for query in queries:
            if len(results) >= self.max_results:
                break
            try:
                page_results = self._search_google(query)
                results.extend(page_results)
                time.sleep(2)  # Polite delay between requests
            except Exception as e:
                self._log_error(f"Google query failed: {e}")

        self._log_info(f"Google search complete. Found {len(results)} records.")
        return results[: self.max_results]

    def _build_queries(self) -> List[str]:
        """Build multiple search query variants for maximum coverage."""
        kw = self.keyword
        return [
            f'"{kw}" buyers importers email site:.com',
            f'"{kw}" wholesale suppliers contact email',
            f'"{kw}" importers "contact us" email',
            f'"{kw}" trading company email address',
            f'site:linkedin.com "{kw}" buyer email',
            f'"{kw}" distributor importer email contact',
        ]

    def _search_google(self, query: str) -> List[BuyerRecord]:
        records: List[BuyerRecord] = []
        links = []
        try:
            from flask import current_app
            from app.services.settings_service import SettingsService
            import json
            
            api_key = SettingsService.get("serper_api_key") or current_app.config.get("SERPER_API_KEY")
            if not api_key:
                self._log_error("SERPER_API_KEY is not set.")
                return records

            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": 10})
            headers = {
              'X-API-KEY': api_key,
              'Content-Type': 'application/json'
            }
            resp = requests.post(url, headers=headers, data=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            for item in data.get("organic", []):
                link = item.get("link")
                if link and link.startswith("http"):
                    links.append(link)
                    
        except Exception as e:
            self._log_error(f'Serper API error for query {query!r}: {e}')
            return records

        links = list(dict.fromkeys(links))
        self._log_info(f'Found {len(links)} links for: {query!r}')

        for link in links[:5]:
            try:
                page_records = self._scrape_page(link)
                records.extend(page_records)
                time.sleep(1.0)
            except Exception as e:
                self._log_error(f'Failed to scrape {link}: {e}')

        return records

    def _extract_result_links(self, soup: BeautifulSoup) -> List[str]:
        # Unused now, but kept for signature compatibility if needed
        return []

    def _scrape_page(self, url: str) -> List[BuyerRecord]:
        """Visit a page and extract email addresses from its text."""
        records: List[BuyerRecord] = []
        try:
            resp = requests.get(
                url,
                headers=self._make_headers(),
                timeout=15,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except Exception:
            return records

        text = resp.text
        soup = BeautifulSoup(text, "lxml")

        # Extract page metadata for company/country hints
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        domain = urlparse(url).netloc.replace("www.", "")

        # Find all emails in page content
        emails_found = set(self.EMAIL_RE.findall(text))

        for email in emails_found:
            # Skip obvious false positives
            if not self._is_valid_email(email):
                continue
            record = BuyerRecord(
                email=email,
                company_name=title or domain,
                website=f"https://{domain}",
                source_platform=self.SOURCE_NAME,
                source_url=url,
                search_keyword=self.keyword,
            )
            records.append(record)

        return records
