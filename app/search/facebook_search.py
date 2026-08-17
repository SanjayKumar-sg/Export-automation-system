"""
app/search/facebook_search.py — Facebook public pages search adapter.

Uses Google dork queries targeting facebook.com to find public
business pages related to the keyword without requiring a login.
"""
from __future__ import annotations

import re
import time
from typing import List
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

from app.search.base_adapter import BaseSearchAdapter, BuyerRecord


class FacebookSearchAdapter(BaseSearchAdapter):
    """Search for buyers via Facebook public business pages."""

    SOURCE_NAME = "facebook"
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    def search(self) -> List[BuyerRecord]:
        """Find Facebook business pages via Google dorks and extract contacts."""
        self._log_info(f"Starting Facebook search for: {self.keyword!r}")
        results: List[BuyerRecord] = []

        queries = [
            f'site:facebook.com "{self.keyword}" importer buyer email',
            f'site:facebook.com/pages "{self.keyword}" wholesale',
            f'site:facebook.com "{self.keyword}" trading company',
        ]

        for query in queries:
            if len(results) >= self.max_results:
                break
            try:
                links = self._google_dork(query)
                for link in links[:8]:
                    records = self._scrape_fb_page(link)
                    results.extend(records)
                    time.sleep(1.5)
            except Exception as e:
                self._log_error(f"Facebook query failed: {e}")

        self._log_info(f"Facebook search complete. Found {len(results)} records.")
        return results[: self.max_results]

    def _google_dork(self, query: str) -> List[str]:
        try:
            from flask import current_app
            from app.services.settings_service import SettingsService
            import json
            import requests
            
            api_key = SettingsService.get("serper_api_key") or current_app.config.get("SERPER_API_KEY")
            if not api_key:
                self._log_error("SERPER_API_KEY is not set.")
                return []

            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": query, "num": 10})
            headers = {
              'X-API-KEY': api_key,
              'Content-Type': 'application/json'
            }
            resp = requests.post(url, headers=headers, data=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            links = []
            for item in data.get("organic", []):
                link = item.get("link")
                if link and "facebook.com" in link and link.startswith("http"):
                    links.append(link)
            return list(dict.fromkeys(links))
        except Exception as e:
            self._log_error(f'Serper API dork error: {e}')
            return []

    def _scrape_fb_page(self, url: str) -> List[BuyerRecord]:
        """Attempt to extract emails from a public Facebook page."""
        records: List[BuyerRecord] = []
        try:
            resp = requests.get(
                url, headers=self._make_headers(), timeout=15, allow_redirects=True
            )
            soup = BeautifulSoup(resp.text, "lxml")
            text = soup.get_text(" ", strip=True)
            emails = set(self.EMAIL_RE.findall(text))

            page_name = None
            og_title = soup.find("meta", property="og:title")
            if og_title:
                page_name = og_title.get("content", "")

            for email in emails:
                if not self._is_valid_email(email):
                    continue
                records.append(
                    BuyerRecord(
                        email=email,
                        company_name=page_name,
                        source_platform=self.SOURCE_NAME,
                        source_url=url,
                        search_keyword=self.keyword,
                    )
                )
        except Exception as e:
            self._log_error(f"FB scrape error {url}: {e}")
        return records
