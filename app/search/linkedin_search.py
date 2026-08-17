"""
app/search/linkedin_search.py — LinkedIn public profile search adapter.

Uses Google dork queries targeting linkedin.com/in and /company
to surface buyer profiles without requiring authentication.
"""
from __future__ import annotations

import re
import time
from typing import List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from app.search.base_adapter import BaseSearchAdapter, BuyerRecord


class LinkedInSearchAdapter(BaseSearchAdapter):
    """Search for buyers via LinkedIn public profiles using Google dorks."""

    SOURCE_NAME = "linkedin"
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    def search(self) -> List[BuyerRecord]:
        self._log_info(f"Starting LinkedIn search for: {self.keyword!r}")
        results: List[BuyerRecord] = []

        queries = [
            f'site:linkedin.com/in "{self.keyword}" buyer importer',
            f'site:linkedin.com/company "{self.keyword}" importing',
            f'site:linkedin.com "{self.keyword}" purchasing manager email',
        ]

        for query in queries:
            if len(results) >= self.max_results:
                break
            links = self._bing_dork(query)
            for link in links[:6]:
                try:
                    records = self._scrape_linkedin(link)
                    results.extend(records)
                    time.sleep(2)
                except Exception as e:
                    self._log_error(f"LinkedIn scrape failed: {e}")

        self._log_info(f"LinkedIn search complete. Found {len(results)} records.")
        return results[: self.max_results]

    def _bing_dork(self, query: str) -> List[str]:
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
                if link and "linkedin.com" in link and link.startswith("http"):
                    links.append(link)
            return list(dict.fromkeys(links))
        except Exception as e:
            self._log_error(f'Serper API dork error: {e}')
            return []

    def _scrape_linkedin(self, url: str) -> List[BuyerRecord]:
        """Extract publicly visible name and contact info from a LinkedIn page."""
        records: List[BuyerRecord] = []
        try:
            resp = requests.get(url, headers=self._make_headers(), timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")
            text = soup.get_text(" ", strip=True)

            # LinkedIn rarely shows emails publicly; extract from text
            emails = set(self.EMAIL_RE.findall(text))

            # Try to extract name from meta tags
            og_title = soup.find("meta", property="og:title")
            name = og_title.get("content", "").strip() if og_title else None

            # Company from description
            og_desc = soup.find("meta", property="og:description")
            description = og_desc.get("content", "") if og_desc else ""

            for email in emails:
                if not self._is_valid_email(email):
                    continue
                records.append(
                    BuyerRecord(
                        email=email,
                        buyer_name=name,
                        company_name=name,
                        source_platform=self.SOURCE_NAME,
                        source_url=url,
                        search_keyword=self.keyword,
                        extra={"description": description},
                    )
                )
        except Exception as e:
            self._log_error(f"LinkedIn parse error: {e}")
        return records
