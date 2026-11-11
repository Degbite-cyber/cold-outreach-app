import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List

class SequenceFollowUpManager:
    """
    Manages 3-stage follow-up sequence according to Susana Otokpa's Prompt Playbook:
    - Stage 1: Initial Cold Pitch (Day 0)
    - Stage 2: Value follow-up (Day 3, gives a quick win, never says 'just following up')
    - Stage 3: Break-up / Final micro-angle (Day 7)
    - Rule: Immediately halts if status is 'REPLIED', 'BOUNCED', or 'UNSUBSCRIBED'.
    """

    def __init__(self, copywriter, sender_name: str = "Adegbite David"):
        self.copywriter = copywriter
        self.sender_name = sender_name

    def generate_follow_up(self, stage: int, business_name: str, first_name: str, initial_subject: str) -> Dict[str, str]:
        name_clean = first_name if first_name else "there"
        subject = f"Re: {initial_subject}"

        if stage == 1:
            # Stage 2 (48-72h later) - Susana Prompt 10: Value follow-up under 70 words, no guilt
            body = (
                f"Hi {name_clean},\n\n"
                f"Thought of one quick win for {business_name}: you can use an instant webhook from your website contact form into Slack or WhatsApp, so your team gets notified in 5 seconds without checking emails.\n\n"
                f"Still open to a 10-minute chat this week on streamlining the rest of your lead flow?\n\n"
                f"Best,\n{self.sender_name}"
            )
        elif stage == 2:
            # Stage 3 (Final touch)
            body = (
                f"Hi {name_clean},\n\n"
                f"Assuming your lead intake and CRM workflows are fully dialed in right now, so I will stop following up.\n\n"
                f"If you ever need to connect your intake forms or automate manual data entry down the road, feel free to keep my contact handy.\n\n"
                f"Best,\n{self.sender_name}"
            )
        else:
            return {}

        return {"subject": subject, "body": body}

    def should_trigger_followup(self, status: str, last_contacted_str: str, days_threshold: int = 3) -> bool:
        if status in ["REPLIED", "BOUNCED", "UNSUBSCRIBED", "COMPLETED", "HOLD"]:
            return False

        if not last_contacted_str:
            return False

        try:
            last_date = datetime.strptime(last_contacted_str, "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - last_date) >= timedelta(days=days_threshold)
        except Exception:
            return False
