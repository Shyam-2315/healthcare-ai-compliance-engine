from datetime import UTC, datetime
import re


def utc_timestamp() -> int:
    return int(datetime.now(tz=UTC).timestamp())


def time_to_minutes(value: str) -> int:
    normalized = value.strip().upper()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)(?:\s*([AP]M))?", normalized)
    if not match:
        raise ValueError(f"Invalid time value: {value}")

    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3)

    if meridiem == "AM":
        if hour == 12:
            hour = 0
    elif meridiem == "PM":
        if hour != 12:
            hour += 12

    return hour * 60 + minute


def normalize_time(value: str) -> str:
    minutes = time_to_minutes(value)
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def ranges_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    start_a_minutes = time_to_minutes(start_a)
    end_a_minutes = time_to_minutes(end_a)
    start_b_minutes = time_to_minutes(start_b)
    end_b_minutes = time_to_minutes(end_b)
    return start_a_minutes < end_b_minutes and start_b_minutes < end_a_minutes
