"""
app/search/website_search.py — Direct company website search adapter.

Uses Bing to find company websites for the keyword, then scrapes
their Contact Us pages for email addresses.
"""
from __future__ import annotations

import re
import time
from typing import List
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.search.base_adapter import BaseSearchAdapter, BuyerRecord


class WebsiteSearchAdapter(BaseSearchAdapter):
    """Discover buyers by scraping company websites directly."""

    SOURCE_NAME = "website"
    EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

    CONTACT_PATHS = [
        "/contact", "/contact-us", "/contactus", "/about",
        "/about-us", "/reach-us", "/get-in-touch",
    ]

    def search(self) -> List[BuyerRecord]:
        self._log_info(f"Starting website search for: {self.keyword!r}")
        results: List[BuyerRecord] = []

        # Step 1: find company websites via Bing
        websites = self._find_company_websites()
        self._log_info(f"Found {len(websites)} company websites to scrape.")

        for site_url in websites:
            if len(results) >= self.max_results:
                break
            try:
                records = self._scrape_website(site_url)
                results.extend(records)
                time.sleep(1.5)
            except Exception as e:
                self._log_error(f"Website scrape failed {site_url}: {e}")

        self._log_info(f"Website search complete. Found {len(results)} records.")
        return results[: self.max_results]

    def _find_company_websites(self) -> List[str]:
        query = f'"{self.keyword}" importer buyer company -alibaba -amazon -etsy'
        websites: List[str] = []
        try:
            from flask import current_app
            from app.services.settings_service import SettingsService
            import json
            import requests
            from urllib.parse import urlparse
            
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
            
            for item in data.get("organic", []):
                link = item.get("link")
                if link and link.startswith("http"):
                    parsed = urlparse(link)
                    base = f'{parsed.scheme}://{parsed.netloc}'
                    if base not in websites:
                        websites.append(base)
            
            self._log_info(f"Serper API found {len(websites)} websites.")
        except Exception as e:
            self._log_error(f'Serper API website search error: {e}')
            
        return websites

    def _scrape_website(self, base_url: str) -> List[BuyerRecord]:
        """Scrape homepage and contact pages of a company website."""
        records: List[BuyerRecord] = []
        domain = urlparse(base_url).netloc.replace("www.", "")
        company_name = None
        all_emails: set = set()

        pages_to_visit = [base_url] + [base_url.rstrip("/") + p for p in self.CONTACT_PATHS]

        for page_url in pages_to_visit[:4]:  # Visit at most 4 pages
            try:
                resp = requests.get(
                    page_url, headers=self._make_headers(), timeout=12, allow_redirects=True
                )
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")

                # Get company name from first page
                if company_name is None:
                    og_title = soup.find("meta", property="og:title")
                    if og_title:
                        company_name = og_title.get("content", "").strip()
                    elif soup.title:
                        company_name = soup.title.string.strip() if soup.title.string else None

                text = soup.get_text(" ", strip=True)
                emails = set(self.EMAIL_RE.findall(text))
                all_emails.update(emails)
                time.sleep(0.8)
            except Exception:
                continue

        for email in all_emails:
            if not self._is_valid_email(email):
                continue
            records.append(
                BuyerRecord(
                    email=email,
                    company_name=company_name or domain,
                    website=base_url,
                    source_platform=self.SOURCE_NAME,
                    source_url=base_url,
                    search_keyword=self.keyword,
                )
            )

        return records
