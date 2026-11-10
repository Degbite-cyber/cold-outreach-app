import re
from typing import Dict, Any

class SafetyGuard:
    """
    Enforces non-negotiable safety rules:
    - CAN-SPAM compliance (physical address, unsubscribe header/footer)
    - Anti-spam copywriting standards (no em dashes, under 100 words, no spam trigger words)
    - Bounce rate circuit breaker (threshold 5%)
    - Role address detection (e.g. info@, support@, admin@)
    """

    ROLE_PREFIXES = {
        "info@", "support@", "admin@", "sales@", "contact@", "help@",
        "hello@", "billing@", "team@", "careers@", "jobs@"
    }

    SPAM_TRIGGER_WORDS = [
        "100% free", "make money fast", "act now", "urgent", "guarantee",
        "no risk", "instant cash", "click here", "winner", "prize"
    ]

    def __init__(self, sender_address: str, max_bounce_rate: float = 5.0):
        self.sender_address = sender_address
        self.max_bounce_rate = max_bounce_rate

    def is_role_address(self, email: str) -> bool:
        if not email:
            return True
        email_clean = email.strip().lower()
        return any(email_clean.startswith(prefix) for prefix in self.ROLE_PREFIXES)

    def check_bounce_threshold(self, total_sent: int, total_bounced: int) -> bool:
        """Returns True if sending is SAFE, False if circuit breaker must trip."""
        if total_sent < 10:  # Need minimum sample size before tripping
            return True
        rate = (total_bounced / total_sent) * 100
        return rate < self.max_bounce_rate

    def validate_copy(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Validates email copy against Susana Playbook rules:
        - Word count strictly under 100 words
        - No em dashes (—) or double hyphens (--)
        - No spam buzzwords
        """
        issues = []
        clean_text = f"{subject} {body}"

        # 1. Em dash check
        if "—" in clean_text or "--" in clean_text:
            issues.append("Contains em dashes (—) or double hyphens (--).")

        # 2. Word count check
        words = body.split()
        if len(words) > 100:
            issues.append(f"Body too long ({len(words)} words; max 100 allowed).")

        # 3. Spam words check
        for spam_word in self.SPAM_TRIGGER_WORDS:
            if re.search(rf"\b{re.escape(spam_word)}\b", clean_text, re.IGNORECASE):
                issues.append(f"Contains flagged spam phrase: '{spam_word}'")

        return {
            "valid": len(issues) == 0,
            "word_count": len(words),
            "issues": issues
        }

    def append_can_spam_footer(self, body: str) -> str:
        """Appends physical address and plain-text opt-out note."""
        footer = (
            f"\n\n---\n"
            f"{self.sender_address}\n"
            f"If you'd rather not hear from me, reply 'stop' or 'unsubscribe' and I will immediately remove you."
        )
        return body.rstrip() + footer
