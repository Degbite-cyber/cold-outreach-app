import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

class WebsiteResearcher:
    """
    Hybrid website researcher:
    1. Unlimited Free: Requests + BeautifulSoup (fast, no credits consumed)
    2. Fallback: Firecrawl API (for JavaScript-heavy or Cloudflare protected sites)
    """

    def __init__(self, firecrawl_api_key: str = ""):
        self.firecrawl_api_key = firecrawl_api_key
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def research(self, website_url: str) -> Dict[str, Any]:
        """Scrapes website and extracts relevant text summary and workflow bottlenecks."""
        if not website_url:
            return {"success": False, "summary": "No website provided", "source": "none"}

        url = website_url.strip()
        if not url.startswith("http"):
            url = f"https://{url}"

        # Attempt 1: Free Local Scrape (0 credit cost)
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200 and len(resp.text) > 500:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Remove scripts, styles, nav, footer to extract core content
                for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    element.extract()

                text = soup.get_text(separator=" ", strip=True)
                clean_text = re.sub(r"\s+", " ", text)[:2500]

                if len(clean_text) > 150:
                    return {
                        "success": True,
                        "text": clean_text,
                        "source": "local_scraper",
                        "title": soup.title.string.strip() if soup.title else ""
                    }
        except Exception:
            pass  # Fall through to Firecrawl

        # Attempt 2: Firecrawl Free Tier Fallback
        if self.firecrawl_api_key:
            try:
                firecrawl_url = "https://api.firecrawl.dev/v1/scrape"
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "url": url,
                    "formats": ["markdown"]
                }
                f_resp = requests.post(firecrawl_url, headers=headers, json=payload, timeout=20)
                if f_resp.status_code == 200:
                    data = f_resp.json()
                    markdown = data.get("data", {}).get("markdown", "")
                    clean_md = re.sub(r"\s+", " ", markdown)[:2500]
                    return {
                        "success": True,
                        "text": clean_md,
                        "source": "firecrawl",
                        "title": data.get("data", {}).get("metadata", {}).get("title", "")
                    }
            except Exception as e:
                return {"success": False, "error": str(e), "source": "firecrawl_error"}

        return {"success": False, "text": "", "source": "failed"}
