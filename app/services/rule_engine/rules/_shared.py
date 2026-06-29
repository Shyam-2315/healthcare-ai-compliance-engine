from __future__ import annotations

from datetime import date, time
from typing import Any, Iterable

from app.utils.date_utils import safe_parse_date
from app.utils.time_utils import normalize_time, time_to_minutes

DLA20_AREA_KEYWORDS: dict[str, list[str]] = {
    "health_practices": ["health", "wellness", "self-care", "hygiene", "medication"],
    "housing_stability": ["housing", "home", "residence", "shelter"],
    "communication": ["communication", "communicate", "express", "speak", "interpersonal"],
    "safety": ["safety", "crisis", "risk", "protection"],
    "managing_money": ["budget", "money", "finance", "financial"],
    "nutrition": ["nutrition", "diet", "meal", "food"],
    "problem_solving": ["problem solving", "decision", "planning", "solutions"],
    "family_relationships": ["family", "relationship", "parent", "caregiver"],
    "alcohol_and_drug_use": ["substance", "sobriety", "alcohol", "drug", "recovery"],
    "community_resources": ["community", "resource", "transportation", "benefits"],
    "personal_hygiene": ["hygiene", "grooming", "self-care", "cleanliness"],
    "productivity": ["work", "school", "productivity", "employment", "routine"],
    "coping_skills": ["coping", "stress", "anxiety", "skills", "regulation"],
}

STOPWORDS = {
    "and",
    "the",
    "with",
    "from",
    "that",
    "this",
    "into",
    "goal",
    "goals",
    "improve",
    "increase",
    "reduce",
    "support",
}


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_token(value: Any) -> str:
    return normalize_text(value).lower().replace(" ", "_")


def normalize_matrix_rows(bhs_matrix: Any) -> list[dict[str, Any]]:
    if isinstance(bhs_matrix, list):
        return [item for item in bhs_matrix if isinstance(item, dict)]
    if not isinstance(bhs_matrix, dict):
        return []

    for key in ("rows", "procedures", "entries", "data"):
        value = bhs_matrix.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    if "cpt_matrix" in bhs_matrix and isinstance(bhs_matrix["cpt_matrix"], dict):
        rows: list[dict[str, Any]] = []
        for proc_code, row in bhs_matrix["cpt_matrix"].items():
            if isinstance(row, dict):
                rows.append({"proc_code": proc_code, **row})
        return rows

    if "rules" in bhs_matrix and isinstance(bhs_matrix["rules"], list):
        return [item for item in bhs_matrix["rules"] if isinstance(item, dict)]

    if any(isinstance(value, dict) and "proc_code" in value for value in bhs_matrix.values()):
        return [value for value in bhs_matrix.values() if isinstance(value, dict)]

    return []


def rows_for_cpt(bhs_matrix: Any, cpt_code: str) -> list[dict[str, Any]]:
    code = normalize_text(cpt_code)
    return [
        row
        for row in normalize_matrix_rows(bhs_matrix)
        if normalize_text(row.get("proc_code") or row.get("cpt_code")) == code
    ]


def extract_allowed_values(row: dict[str, Any], *keys: str) -> set[str]:
    values: set[str] = set()
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            for item in value.split(","):
                cleaned = item.strip()
                if cleaned:
                    values.add(cleaned.upper())
        else:
            for item in ensure_list(value):
                cleaned = normalize_text(item)
                if cleaned:
                    values.add(cleaned.upper())
    return values


def normalize_cpt_credentials(cpt_credentials: Any) -> dict[str, set[str]]:
    data = cpt_credentials.get("cpt_credentials", cpt_credentials) if isinstance(cpt_credentials, dict) else {}
    normalized: dict[str, set[str]] = {}
    if isinstance(data, dict):
        for cpt_code, licenses in data.items():
            normalized[str(cpt_code)] = {normalize_text(item).upper() for item in ensure_list(licenses) if normalize_text(item)}
    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            code = normalize_text(item.get("proc_code") or item.get("cpt_code"))
            if code:
                normalized[code] = {
                    normalize_text(value).upper()
                    for value in ensure_list(
                        item.get("licenses") or item.get("credentials") or item.get("license")
                    )
                    if normalize_text(value)
                }
    return normalized


def historical_claim_list(historical_claims: Any) -> list[dict[str, Any]]:
    if isinstance(historical_claims, list):
        return [item for item in historical_claims if isinstance(item, dict)]
    if isinstance(historical_claims, dict):
        claims = historical_claims.get("claims")
        if isinstance(claims, list):
            return [item for item in claims if isinstance(item, dict)]
    return []


def claim_dates(claim: dict[str, Any]) -> set[date]:
    dates: set[date] = set()
    for value in ensure_list(claim.get("service_dates")):
        parsed = safe_parse_date(value)
        if parsed:
            dates.add(parsed)
    single_date = safe_parse_date(claim.get("service_date"))
    if single_date:
        dates.add(single_date)
    return dates


def format_time_value(value: Any) -> str | None:
    if isinstance(value, time):
        return value.strftime("%H:%M")
    text = normalize_text(value)
    if not text:
        return None
    try:
        return normalize_time(text)
    except ValueError:
        return None


def time_gap_minutes(
    start_a: str,
    end_a: str,
    start_b: str,
    end_b: str,
) -> int | None:
    try:
        first_start = time_to_minutes(start_a)
        first_end = time_to_minutes(end_a)
        second_start = time_to_minutes(start_b)
        second_end = time_to_minutes(end_b)
    except ValueError:
        return None

    if first_end <= second_start:
        return second_start - first_end
    if second_end <= first_start:
        return first_start - second_end
    return 0


def keywords_for_area(area: str) -> list[str]:
    normalized = normalize_token(area)
    if normalized in DLA20_AREA_KEYWORDS:
        return DLA20_AREA_KEYWORDS[normalized]
    return [part for part in normalized.replace("_", " ").split() if part]


def text_references_area(text: str, area: str) -> bool:
    lowered = normalize_text(text).lower()
    return any(keyword.lower() in lowered for keyword in keywords_for_area(area))


def goal_match_ratio(goals: Iterable[str], text: str) -> float:
    goal_list = [normalize_text(goal) for goal in goals if normalize_text(goal)]
    if not goal_list or not normalize_text(text):
        return 0.0

    text_lower = text.lower()
    matched = 0
    for goal in goal_list:
        goal_lower = goal.lower()
        if goal_lower in text_lower:
            matched += 1
            continue
        tokens = [
            token
            for token in goal_lower.replace("/", " ").replace("-", " ").split()
            if len(token) >= 4 and token not in STOPWORDS
        ]
        if any(token in text_lower for token in tokens):
            matched += 1
    return matched / len(goal_list)
