import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class AutoLeadScout:
    """
    100% Free Automated Lead Finder:
    You type: 'solar company in Austin' or 'marketing agency in London'
    It automatically:
    1. Finds 10-20 business websites.
    2. Scrapes each website to find real contact emails and owner names.
    3. Filters out bad/junk emails.
    4. Returns a ready-to-contact lead list!
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    def scout(self, niche: str, location: str, count: int = 5) -> List[Dict[str, str]]:
        query = f'"{niche}" "{location}" contact email'
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

        leads = []
        visited_domains = set()

        try:
            res = requests.get(search_url, headers=self.HEADERS, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                links = soup.find_all("a", class_="result__url")

                for link in links:
                    if len(leads) >= count:
                        break

                    raw_href = link.get("href", "").strip()
                    if "//duckduckgo.com/l/?uddg=" in raw_href:
                        actual_url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                        parsed = urllib.parse.urlparse(actual_url)
                        domain = parsed.netloc.replace("www.", "")

                        # Skip social media, directories
                        if any(bad in domain for bad in ["yelp.", "facebook.", "linkedin.", "yellowpages.", "instagram.", "twitter."]):
                            continue

                        if domain in visited_domains:
                            continue
                        visited_domains.add(domain)

                        biz_name = domain.split(".")[0].replace("-", " ").title()
                        base_site = f"{parsed.scheme}://{parsed.netloc}"

                        # Scrape email from site
                        contact_data = self._extract_contacts(base_site)
                        if contact_data.get("email"):
                            leads.append({
                                "business_name": biz_name,
                                "website": base_site,
                                "email": contact_data["email"],
                                "first_name": contact_data["first_name"] or "Owner"
                            })
        except Exception as e:
            print(f"Scout notice: {e}")

        return leads

    def _extract_contacts(self, base_url: str) -> Dict[str, str]:
        discovered = set()
        pages = [base_url, f"{base_url.rstrip('/')}/contact", f"{base_url.rstrip('/')}/about"]

        for p in pages:
            try:
                r = requests.get(p, headers=self.HEADERS, timeout=6)
                if r.status_code == 200:
                    found = self.EMAIL_REGEX.findall(r.text)
                    for e in found:
                        e_clean = e.lower().strip(".")
                        if not any(e_clean.endswith(ext) for ext in [".png", ".jpg", ".webp", ".svg", ".css", ".js"]):
                            discovered.add(e_clean)
            except Exception:
                continue

        # Look for personal emails first, fallback to general
        direct = [e for e in discovered if not any(e.startswith(r) for r in ["info@", "support@", "admin@", "sales@", "contact@"])]
        chosen = direct[0] if direct else (list(discovered)[0] if discovered else "")

        name = ""
        if chosen and "." in chosen.split("@")[0]:
            name = chosen.split("@")[0].split(".")[0].capitalize()

        return {"email": chosen, "first_name": name}
