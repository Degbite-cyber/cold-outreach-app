import unittest
from datetime import datetime, timezone, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from safety_guard import SafetyGuard
from scheduler import TimezoneScheduler
from sender import GmailSender

class TestColdOutreachEngine(unittest.TestCase):

    def setUp(self):
        self.guard = SafetyGuard(sender_address="Lagos, Nigeria", max_bounce_rate=5.0)
        self.scheduler = TimezoneScheduler()

    def test_role_address_filtering(self):
        self.assertTrue(self.guard.is_role_address("info@company.com"))
        self.assertTrue(self.guard.is_role_address("support@domain.org"))
        self.assertTrue(self.guard.is_role_address("sales@techfirm.co"))
        self.assertFalse(self.guard.is_role_address("david.adegbite@company.com"))

    def test_copy_rules_enforcement(self):
        res = self.guard.validate_copy(
            "quick question", 
            "Hi John, saw your booking flow. We connect intake forms to CRMs with Make. Worth a chat?"
        )
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["issues"]), 0)

        # Forbidden em dash
        res_em = self.guard.validate_copy(
            "quick question", 
            "We build automations — they save 10 hours a week."
        )
        self.assertFalse(res_em["valid"])
        self.assertTrue(any("em dashes" in issue for issue in res_em["issues"]))

    def test_bounce_rate_circuit_breaker(self):
        # 1 bounce out of 100 sent = 1% (Safe)
        self.assertTrue(self.guard.check_bounce_threshold(total_sent=100, total_bounced=1))
        # 6 bounces out of 100 sent = 6% (Breaker trips)
        self.assertFalse(self.guard.check_bounce_threshold(total_sent=100, total_bounced=6))

    def test_timezone_scheduling(self):
        scheduler = TimezoneScheduler()
        # Wednesday at 9:30 AM Eastern (-5 hours offset = 14:30 UTC)
        # Nov 11, 2026 is Wednesday
        utc_wed_1430 = datetime(2026, 11, 11, 14, 30, tzinfo=timezone.utc)
        status = scheduler.is_in_send_window("America/New_York", now_utc=utc_wed_1430)
        self.assertTrue(status["can_send"])

        # Friday at 9:30 AM Eastern (-5 offset = 14:30 UTC on Nov 13, 2026)
        utc_fri_1430 = datetime(2026, 11, 13, 14, 30, tzinfo=timezone.utc)
        status_fri = scheduler.is_in_send_window("America/New_York", now_utc=utc_fri_1430)
        self.assertFalse(status_fri["can_send"])

    def test_dry_run_safety(self):
        sender = GmailSender(
            sender_email="adegbiteishola001@gmail.com",
            app_password="",
            sender_name="Adegbite David",
            dry_run=True
        )
        result = sender.send_email("ceo@targetfirm.com", "quick question", "Hello, worth a chat?")
        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])

if __name__ == "__main__":
    unittest.main()
