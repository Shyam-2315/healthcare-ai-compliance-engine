from datetime import UTC, date, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def safe_parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    for date_format in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue
    return None


def days_between(start_date: Any, end_date: Any) -> int | None:
    start = safe_parse_date(start_date)
    end = safe_parse_date(end_date)
    if start is None or end is None:
        return None
    return (end - start).days
