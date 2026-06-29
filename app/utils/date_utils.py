from datetime import UTC, date, datetime


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)
