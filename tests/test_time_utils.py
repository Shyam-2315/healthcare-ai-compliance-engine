from datetime import date

from app.utils.date_utils import days_between, safe_parse_date
from app.utils.time_utils import normalize_time, ranges_overlap, time_to_minutes


def test_time_to_minutes_supports_24_hour_and_ampm() -> None:
    assert time_to_minutes("14:30") == 870
    assert time_to_minutes("2:30 PM") == 870
    assert time_to_minutes("12:00 AM") == 0
    assert time_to_minutes("12:00 PM") == 720


def test_normalize_time_returns_24_hour_value() -> None:
    assert normalize_time("2:05 PM") == "14:05"


def test_ranges_overlap_uses_minutes_based_comparison() -> None:
    assert ranges_overlap("09:00", "10:00", "09:30", "11:00") is True
    assert ranges_overlap("09:00", "10:00", "10:00", "11:00") is False
    assert ranges_overlap("1:00 PM", "2:00 PM", "12:30 PM", "1:30 PM") is True


def test_safe_parse_date_handles_valid_and_invalid_dates() -> None:
    assert safe_parse_date("2026-06-29") == date(2026, 6, 29)
    assert safe_parse_date("06/29/2026") == date(2026, 6, 29)
    assert safe_parse_date("June 29, 2026") == date(2026, 6, 29)
    assert safe_parse_date("not a date") is None
    assert safe_parse_date("2026-02-31") is None


def test_days_between_returns_difference_or_none() -> None:
    assert days_between("2026-06-01", "2026-06-29") == 28
    assert days_between("bad", "2026-06-29") is None
