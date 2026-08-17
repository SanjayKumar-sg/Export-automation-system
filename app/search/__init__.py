"""
app/search/__init__.py — Search adapter package.
"""
from app.search.base_adapter import BaseSearchAdapter, BuyerRecord
from app.search.google_search import GoogleSearchAdapter
from app.search.facebook_search import FacebookSearchAdapter
from app.search.linkedin_search import LinkedInSearchAdapter
from app.search.directory_search import DirectorySearchAdapter
from app.search.website_search import WebsiteSearchAdapter

ADAPTER_MAP = {
    "google": GoogleSearchAdapter,
    "facebook": FacebookSearchAdapter,
    "linkedin": LinkedInSearchAdapter,
    "directory": DirectorySearchAdapter,
    "website": WebsiteSearchAdapter,
}

__all__ = [
    "BaseSearchAdapter", "BuyerRecord", "ADAPTER_MAP",
    "GoogleSearchAdapter", "FacebookSearchAdapter",
    "LinkedInSearchAdapter", "DirectorySearchAdapter",
    "WebsiteSearchAdapter",
]
