"""
app/search/country_utils.py — Country inference & extraction utility.
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

# ccTLD -> Country name mapping
TLD_MAP = {
    "au": "Australia",
    "uk": "United Kingdom",
    "ca": "Canada",
    "de": "Germany",
    "fr": "France",
    "in": "India",
    "it": "Italy",
    "es": "Spain",
    "nl": "Netherlands",
    "cn": "China",
    "jp": "Japan",
    "ae": "United Arab Emirates",
    "sg": "Singapore",
    "nz": "New Zealand",
    "br": "Brazil",
    "mx": "Mexico",
    "us": "United States",
    "np": "Nepal",
    "za": "South Africa",
    "se": "Sweden",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "pl": "Poland",
    "ch": "Switzerland",
    "at": "Austria",
    "be": "Belgium",
    "tr": "Turkey",
    "tw": "Taiwan",
    "hk": "Hong Kong",
    "kr": "South Korea",
    "vn": "Vietnam",
    "th": "Thailand",
    "my": "Malaysia",
    "id": "Indonesia",
    "ph": "Philippines",
    "pk": "Pakistan",
    "bd": "Bangladesh",
    "eg": "Egypt",
    "ng": "Nigeria",
    "ke": "Kenya",
    "ar": "Argentina",
    "cl": "Chile",
    "co": "Colombia",
}

# Country names & common variations to look for in text
COUNTRY_PATTERNS = [
    ("United States", [r"\bUnited States\b", r"\bUSA\b", r"\bU\.S\.A\.\b", r"\bU\.S\.\b"]),
    ("United Kingdom", [r"\bUnited Kingdom\b", r"\bUK\b", r"\bU\.K\.\b", r"\bGreat Britain\b", r"\bEngland\b"]),
    ("Australia", [r"\bAustralia\b", r"\bAU\b"]),
    ("Canada", [r"\bCanada\b"]),
    ("Germany", [r"\bGermany\b", r"\bDeutschland\b"]),
    ("France", [r"\bFrance\b"]),
    ("India", [r"\bIndia\b"]),
    ("China", [r"\bChina\b"]),
    ("Japan", [r"\bJapan\b"]),
    ("Italy", [r"\bItaly\b"]),
    ("Spain", [r"\bSpain\b"]),
    ("Netherlands", [r"\bNetherlands\b", r"\bHolland\b"]),
    ("Singapore", [r"\bSingapore\b"]),
    ("United Arab Emirates", [r"\bUnited Arab Emirates\b", r"\bUAE\b", r"\bDubai\b"]),
    ("Brazil", [r"\bBrazil\b", r"\bBrasil\b"]),
    ("Mexico", [r"\bMexico\b"]),
    ("South Korea", [r"\bSouth Korea\b", r"\bKorea\b"]),
    ("Nepal", [r"\bNepal\b"]),
    ("New Zealand", [r"\bNew Zealand\b"]),
    ("South Africa", [r"\bSouth Africa\b"]),
    ("Sweden", [r"\bSweden\b"]),
    ("Norway", [r"\bNorway\b"]),
    ("Switzerland", [r"\bSwitzerland\b"]),
    ("Turkey", [r"\bTurkey\b", r"\bTürkiye\b"]),
    ("Vietnam", [r"\bVietnam\b"]),
    ("Thailand", [r"\bThailand\b"]),
    ("Malaysia", [r"\bMalaysia\b"]),
    ("Indonesia", [r"\bIndonesia\b"]),
]

def infer_country(
    email: Optional[str] = None,
    website: Optional[str] = None,
    text: Optional[str] = None,
    company_name: Optional[str] = None,
) -> str:
    """
    Infer country from email domain, website URL, company name, or page text.
    """
    # 1. Check email domain ccTLD
    if email:
        email_clean = email.strip().lower()
        parts = email_clean.split("@")
        if len(parts) == 2:
            domain_parts = parts[1].split(".")
            if len(domain_parts) >= 2:
                last_tld = domain_parts[-1]
                if last_tld in TLD_MAP:
                    return TLD_MAP[last_tld]

    # 2. Check website domain ccTLD
    if website:
        parsed = urlparse(website if website.startswith("http") else f"https://{website}")
        netloc = parsed.netloc.replace("www.", "").lower()
        domain_parts = netloc.split(".")
        if len(domain_parts) >= 2:
            last_tld = domain_parts[-1]
            if last_tld in TLD_MAP:
                return TLD_MAP[last_tld]

    # 3. Check company name suffixes & keywords
    if company_name:
        cname = company_name.lower()
        if "pty ltd" in cname or "pty. ltd" in cname:
            return "Australia"
        if "gmbh" in cname:
            return "Germany"
        if "s.a." in cname or "s.r.l." in cname:
            return "Italy"
        if "pvt ltd" in cname or "private limited" in cname:
            return "India"
        if "llc" in cname or "inc." in cname or "inc" in cname or "corp" in cname:
            return "United States"

    # 4. Check text content for explicit country names
    full_text = f"{company_name or ''} {text or ''}"
    if full_text.strip():
        for country_name, patterns in COUNTRY_PATTERNS:
            for pat in patterns:
                if re.search(pat, full_text, re.IGNORECASE):
                    return country_name

    # 5. Domain / email name hints
    if email:
        domain = email.split("@")[-1].lower()
        if "go4worldbusiness" in domain:
            return "Global"
        if "exporaja" in domain:
            return "India"
        if "export" in domain or "global" in domain or "trade" in domain:
            if "india" in domain or "raja" in domain:
                return "India"

    # 6. Fallback
    if text and "go4worldbusiness" in text.lower():
        return "Global"

    return "United States"
