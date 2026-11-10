import re
import csv
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class FreeLeadFinder:
    """
    100% Free Lead Finder (Zero LinkedIn, Zero Paid Tools):
    1. Uses open web scraping to discover business sites.
    2. Scrapes homepage and /contact pages to extract public business emails.
    3. Formats them directly into sample_leads.csv for the engine.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    def extract_from_website(self, url: str) -> Dict[str, str]:
        """Extracts direct email and business details from a website URL."""
        if not url.startswith("http"):
            url = f"https://{url}"

        discovered = set()
        pages = [url, f"{url.rstrip('/')}/contact", f"{url.rstrip('/')}/about", f"{url.rstrip('/')}/team"]

        for p in pages:
            try:
                res = requests.get(p, headers=self.HEADERS, timeout=8)
                if res.status_code == 200:
                    emails = self.EMAIL_REGEX.findall(res.text)
                    for e in emails:
                        clean = e.lower().strip(".")
                        if not any(clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".js"]):
                            discovered.add(clean)
            except Exception:
                continue

        # Look for personal email first, otherwise fallback to any email found
        direct_emails = [
            e for e in discovered 
            if not any(e.startswith(r) for r in ["info@", "support@", "admin@", "sales@", "contact@"])
        ]

        chosen_email = direct_emails[0] if direct_emails else (list(discovered)[0] if discovered else "")
        first_name = ""
        if chosen_email and "." in chosen_email.split("@")[0]:
            first_name = chosen_email.split("@")[0].split(".")[0].capitalize()

        return {
            "email": chosen_email,
            "first_name": first_name
        }
