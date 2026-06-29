from __future__ import annotations

from datetime import date
from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import claim_dates, format_time_value, historical_claim_list, normalize_text
from app.utils.time_utils import ranges_overlap

MAX_UNITS_PER_DAY = 16


class SessionDurationMatchesBilledUnitsRule(BaseRule):
    rule_id = "DUR-001"
    rule_name = "Session Duration Matches Billed Units"
    category = "billing"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        duration = extracted.get("session_duration_minutes")
        billed_units = extracted.get("billed_units")
        if not isinstance(duration, int) or not isinstance(billed_units, int):
            return self._fail(
                "Session duration or billed units are missing.",
                RedFlagLevel.HIGH,
                {"session_duration_minutes": duration, "billed_units": billed_units},
            )

        expected_units = round(duration / 15)
        minute_delta = abs(duration - (billed_units * 15))
        if minute_delta > 8:
            return self._fail(
                "Session duration does not align with billed units.",
                RedFlagLevel.HIGH,
                {
                    "session_duration_minutes": duration,
                    "billed_units": billed_units,
                    "expected_units": expected_units,
                    "minute_delta": minute_delta,
                },
            )

        return self._pass(
            "Session duration aligns with billed units.",
            {
                "session_duration_minutes": duration,
                "billed_units": billed_units,
                "expected_units": expected_units,
            },
        )


class UnitsWithinAllowableRangeRule(BaseRule):
    rule_id = "UNIT-001"
    rule_name = "Units Within Allowable Range"
    category = "billing"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        billed_units = extracted.get("billed_units")
        if not isinstance(billed_units, int):
            return self._fail("Billed units are missing.", RedFlagLevel.MEDIUM)
        if billed_units > MAX_UNITS_PER_DAY:
            return self._fail(
                "Billed units exceed the allowable daily limit.",
                RedFlagLevel.MEDIUM,
                {"billed_units": billed_units, "max_units_per_day": MAX_UNITS_PER_DAY},
            )
        return self._pass(
            "Billed units are within the allowable daily range.",
            {"billed_units": billed_units, "max_units_per_day": MAX_UNITS_PER_DAY},
        )


class NoTimeOverlapInClaimsRule(BaseRule):
    rule_id = "TOVL-001"
    rule_name = "No Time Overlap in Claims"
    category = "billing"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        provider_id = normalize_text(extracted.get("provider_id"))
        service_dates = claim_dates(extracted)
        start_time = format_time_value(extracted.get("session_start_time"))
        end_time = format_time_value(extracted.get("session_end_time"))
        if not provider_id or not service_dates or not start_time or not end_time:
            return self._pass(
                "Skipped overlap validation because provider, service date, or session time is missing.",
                {
                    "provider_id": provider_id,
                    "service_dates": sorted(value.isoformat() for value in service_dates),
                    "session_start_time": start_time,
                    "session_end_time": end_time,
                },
            )

        overlapping_claims: list[str] = []
        for historical_claim in historical_claim_list(historical_claims):
            if normalize_text(historical_claim.get("provider_id")) != provider_id:
                continue
            if not _shares_service_date(service_dates, claim_dates(historical_claim)):
                continue
            historical_start = format_time_value(historical_claim.get("session_start_time"))
            historical_end = format_time_value(historical_claim.get("session_end_time"))
            if not historical_start or not historical_end:
                continue
            if ranges_overlap(start_time, end_time, historical_start, historical_end):
                overlapping_claims.append(normalize_text(historical_claim.get("claim_id")) or "unknown")

        if overlapping_claims:
            return self._fail(
                "Current claim overlaps a historical claim for the same provider and service date.",
                RedFlagLevel.HIGH,
                {"overlapping_claim_ids": overlapping_claims},
            )

        return self._pass("No overlapping claims were detected for the same provider and service date.")


def _shares_service_date(current_dates: set[date], historical_dates: set[date]) -> bool:
    return bool(current_dates.intersection(historical_dates))
