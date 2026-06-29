from datetime import date
from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import (
    claim_dates,
    format_time_value,
    historical_claim_list,
    normalize_text,
    time_gap_minutes,
)

MAX_TRAVEL_SPEED_MPH = 30.0


class TravelFeasibilityBetweenServiceLocationsRule(BaseRule):
    rule_id = "TRV-001"
    rule_name = "Travel Feasibility Between Service Locations"
    category = "travel"
    priority = RulePriority.LOW

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        provider_id = normalize_text(extracted.get("provider_id"))
        current_dates = claim_dates(extracted)
        current_location = normalize_text(extracted.get("service_location"))
        current_start = format_time_value(extracted.get("session_start_time"))
        current_end = format_time_value(extracted.get("session_end_time"))
        if not provider_id or not current_dates or not current_location:
            return self._pass("Skipped travel feasibility check because provider, service date, or location is missing.")

        impossible_claims: list[str] = []
        for historical_claim in historical_claim_list(historical_claims):
            if normalize_text(historical_claim.get("provider_id")) != provider_id:
                continue
            if not _shares_service_date(current_dates, claim_dates(historical_claim)):
                continue
            historical_location = normalize_text(historical_claim.get("service_location"))
            if not historical_location or historical_location == current_location:
                continue
            distance = historical_claim.get("distance_miles")
            historical_start = format_time_value(historical_claim.get("session_start_time"))
            historical_end = format_time_value(historical_claim.get("session_end_time"))
            if distance is None or not current_start or not current_end or not historical_start or not historical_end:
                continue
            gap_minutes = time_gap_minutes(current_start, current_end, historical_start, historical_end)
            if gap_minutes is None:
                continue
            if gap_minutes <= 0:
                impossible_claims.append(normalize_text(historical_claim.get("claim_id")) or "unknown")
                continue
            speed_required = float(distance) / (gap_minutes / 60)
            if speed_required > MAX_TRAVEL_SPEED_MPH:
                impossible_claims.append(normalize_text(historical_claim.get("claim_id")) or "unknown")

        if impossible_claims:
            return self._fail(
                "Travel between service locations is not feasible for the documented schedule.",
                RedFlagLevel.LOW,
                {"historical_claim_ids": impossible_claims, "max_travel_speed_mph": MAX_TRAVEL_SPEED_MPH},
            )

        return self._pass("Travel feasibility check passed or was not applicable.")


def _shares_service_date(current_dates: set[date], historical_dates: set[date]) -> bool:
    return bool(current_dates.intersection(historical_dates))
