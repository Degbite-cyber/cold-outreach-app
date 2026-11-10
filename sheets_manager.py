import os
import json
import requests
from typing import List, Dict, Any

class SheetsManager:
    """
    Connects to Google Sheets via Google Apps Script Web App.
    100% free, zero Google Cloud permissions, bypasses all organization policies!
    """

    def __init__(self, webapp_url: str = ""):
        self.webapp_url = webapp_url or os.getenv("GOOGLE_SHEET_WEBAPP_URL", "")

    def is_connected(self) -> bool:
        return bool(self.webapp_url and self.webapp_url.startswith("https://script.google.com"))

    def get_leads(self) -> Dict[str, Any]:
        """Fetches all leads and checks if MASTER_PAUSE is active."""
        if not self.is_connected():
            return {"status": "error", "message": "No webapp_url configured", "leads": [], "is_paused": False}

        try:
            payload = {"action": "get_leads"}
            res = requests.post(self.webapp_url, json=payload, timeout=15)
            if res.status_code == 200:
                return res.json()
            return {"status": "error", "message": f"HTTP {res.status_code}", "leads": [], "is_paused": False}
        except Exception as e:
            return {"status": "error", "message": str(e), "leads": [], "is_paused": False}

    def update_lead(self, row_number: int, updates: Dict[str, Any]) -> bool:
        """Sends updates (e.g. draft, verified status) directly back to Google Sheet."""
        if not self.is_connected():
            return False

        try:
            payload = {
                "action": "update_lead",
                "row_number": row_number,
                "updates": updates
            }
            res = requests.post(self.webapp_url, json=payload, timeout=15)
            return res.status_code == 200 and res.json().get("status") == "success"
        except Exception:
            return False
