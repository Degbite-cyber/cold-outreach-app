import pytest
from datetime import datetime
import pytz
from safety_guard import SafetyGuard
from scheduler import TimezoneScheduler
from copywriter import AICopywriter
from sender import GmailSender
from verifier import EmailVerifier

def test_safety_guard_role_address():
    guard = SafetyGuard(sender_address="Lagos, Nigeria")
    assert guard.is_role_address("info@company.com") is True
    assert guard.is_role_address("sales@company.com") is True
    assert guard.is_role_address("john.smith@company.com") is False

def test_safety_guard_copy_validation():
    guard = SafetyGuard(sender_address="Lagos, Nigeria")
    
    # Test valid copy
    valid_res = guard.validate_copy("quick question", "Hi John, saw your website. We build n8n automations. Worth a chat?")
    assert valid_res["valid"] is True
    assert valid_res["issues"] == []

    # Test copy with em dash
    invalid_em = guard.validate_copy("quick question", "We build automations — they save time.")
    assert invalid_em["valid"] is False
    assert any("em dashes" in i for i in invalid_em["issues"])

    # Test copy with spam words
    invalid_spam = guard.validate_copy("100% free deal", "Act now and get instant cash.")
    assert invalid_spam["valid"] is False

def test_safety_guard_bounce_circuit_breaker():
    guard = SafetyGuard(sender_address="Lagos, Nigeria", max_bounce_rate=5.0)
    # 1 bounce out of 100 sent = 1% (Safe)
    assert guard.check_bounce_threshold(total_sent=100, total_bounced=1) is True
    # 6 bounces out of 100 sent = 6% (Trip breaker)
    assert guard.check_bounce_threshold(total_sent=100, total_bounced=6) is False

def test_scheduler_timezone_resolution():
    scheduler = TimezoneScheduler()
    assert scheduler.resolve_timezone(None, "US") == "America/New_York"
    assert scheduler.resolve_timezone(None, "UK") == "Europe/London"
    assert scheduler.resolve_timezone("America/Chicago", "US") == "America/Chicago"

def test_scheduler_send_window():
    scheduler = TimezoneScheduler()
    # Wednesday 9:30 AM New York time (In window)
    ny_tz = pytz.timezone("America/New_York")
    wed_930 = ny_tz.localize(datetime(2026, 11, 11, 9, 30, 0)) # Nov 11 2026 is Wednesday
    utc_time = wed_930.astimezone(pytz.utc)
    
    status = scheduler.is_in_send_window("America/New_York", now_utc=utc_time)
    assert status["can_send"] is True

    # Friday 9:30 AM (Out of window: only Tue-Thu allowed)
    fri_930 = ny_tz.localize(datetime(2026, 11, 13, 9, 30, 0))
    status_fri = scheduler.is_in_send_window("America/New_York", now_utc=fri_930.astimezone(pytz.utc))
    assert status_fri["can_send"] is False

def test_gmail_dry_run_safety():
    sender = GmailSender(
        sender_email="test@gmail.com",
        app_password="",
        sender_name="Adegbite David",
        dry_run=True
    )
    res = sender.send_email("prospect@business.com", "Test Subject", "Test Body")
    assert res["success"] is True
    assert res["dry_run"] is True
