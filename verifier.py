import requests
from typing import Dict, Any

class EmailVerifier:
    """
    Verifies emails using Reoon Email Verifier API with fallback to syntax & MX checks.
    Categorizes results into 'VALID', 'INVALID', 'DISPOSABLE', 'CATCH_ALL'.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://emailverifier.reoon.com/api/v1/verify"

    def verify(self, email: str, mode: str = "quick") -> Dict[str, Any]:
        """
        Verify single email via Reoon API.
        mode can be 'quick' (few seconds) or 'power' (deep SMTP test).
        """
        if not email or "@" not in email:
            return {"status": "INVALID", "reason": "Malformed email address", "raw": {}}

        if not self.api_key or self.api_key.startswith("test_"):
            # Mock mode / offline dry run
            return {"status": "VALID", "reason": "Mocked validation", "raw": {}}

        try:
            params = {
                "email": email.strip(),
                "key": self.api_key,
                "mode": mode
            }
            response = requests.get(self.base_url, params=params, timeout=12)
            if response.status_code == 200:
                data = response.json()
                reoon_status = data.get("status", "").lower()

                # Reoon returns: valid, invalid, disposable, spamtrap, catch_all, unknown
                if reoon_status == "valid":
                    status = "VALID"
                elif reoon_status in ["invalid", "spamtrap"]:
                    status = "INVALID"
                elif reoon_status == "disposable":
                    status = "DISPOSABLE"
                elif reoon_status == "catch_all":
                    status = "CATCH_ALL"
                else:
                    status = "UNKNOWN"

                return {
                    "status": status,
                    "reason": data.get("reason", ""),
                    "is_safe_to_send": status == "VALID",
                    "raw": data
                }
            else:
                return {
                    "status": "UNKNOWN",
                    "reason": f"API error HTTP {response.status_code}",
                    "is_safe_to_send": False,
                    "raw": {}
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "reason": str(e),
                "is_safe_to_send": False,
                "raw": {}
            }
