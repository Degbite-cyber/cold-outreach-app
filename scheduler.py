from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any

TIMEZONE_OFFSETS = {
    "America/New_York": -5,
    "US/Eastern": -5,
    "America/Chicago": -6,
    "US/Central": -6,
    "America/Denver": -7,
    "US/Mountain": -7,
    "America/Los_Angeles": -8,
    "US/Pacific": -8,
    "Europe/London": 0,
    "Africa/Lagos": 1,
    "Australia/Sydney": 11
}

COUNTRY_TIMEZONE_MAP = {
    "US": "America/New_York",
    "USA": "America/New_York",
    "UNITED STATES": "America/New_York",
    "UK": "Europe/London",
    "UNITED KINGDOM": "Europe/London",
    "CANADA": "America/New_York",
    "CA": "America/New_York",
    "AUSTRALIA": "Australia/Sydney",
    "AU": "Australia/Sydney",
    "NIGERIA": "Africa/Lagos",
    "NG": "Africa/Lagos"
}

class TimezoneScheduler:
    """
    Zero-dependency scheduler for sending Tue-Thu 9:00 - 10:00 AM local time.
    """

    def resolve_timezone(self, tz_str: Optional[str], country_str: Optional[str]) -> str:
        if tz_str and tz_str.strip() in TIMEZONE_OFFSETS:
            return tz_str.strip()

        if country_str and country_str.strip().upper() in COUNTRY_TIMEZONE_MAP:
            return COUNTRY_TIMEZONE_MAP[country_str.strip().upper()]

        return "America/New_York"

    def is_in_send_window(self, timezone_str: str, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        elif now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        offset_hours = TIMEZONE_OFFSETS.get(timezone_str, -5)
        local_time = now_utc + timedelta(hours=offset_hours)

        is_tue_wed_thu = local_time.weekday() in (1, 2, 3)
        is_between_9_and_10 = (local_time.hour == 9)

        return {
            "can_send": is_tue_wed_thu and is_between_9_and_10,
            "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": local_time.strftime("%A"),
            "hour": local_time.hour,
            "timezone": timezone_str
        }
