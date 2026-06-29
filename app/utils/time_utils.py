from datetime import UTC, datetime


def utc_timestamp() -> int:
    return int(datetime.now(tz=UTC).timestamp())
