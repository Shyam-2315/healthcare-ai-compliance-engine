from datetime import date
from difflib import SequenceMatcher
from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import claim_dates, format_time_value, historical_claim_list, normalize_text

CLONE_NOTE_SIMILARITY_THRESHOLD = 0.85


class CloneNotesDetectionRule(BaseRule):
    rule_id = "FRD-001"
    rule_name = "Clone Notes Detection"
    category = "fraud_detection"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        clinical_notes_raw = normalize_text(extracted.get("clinical_notes_raw"))
        if not clinical_notes_raw:
            return self._pass("Skipped clone notes detection because clinical notes text is missing.")

        for historical_claim in historical_claim_list(historical_claims):
            historical_text = normalize_text(historical_claim.get("clinical_notes_text"))
            if not historical_text:
                continue
            similarity = SequenceMatcher(None, clinical_notes_raw, historical_text).ratio()
            if similarity >= CLONE_NOTE_SIMILARITY_THRESHOLD:
                return self._fail(
                    "Clinical note is too similar to a historical note.",
                    RedFlagLevel.HIGH,
                    {
                        "historical_claim_id": normalize_text(historical_claim.get("claim_id")) or "unknown",
                        "similarity": round(similarity, 2),
                        "threshold": CLONE_NOTE_SIMILARITY_THRESHOLD,
                    },
                )

        return self._pass("No cloned clinical notes were detected.")


class TimeConflictDetectionRule(BaseRule):
    rule_id = "FRD-002"
    rule_name = "Time Conflict Detection"
    category = "fraud_detection"
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
            return self._pass("Skipped time conflict detection because provider, service date, or session time is missing.")

        conflicting_claims: list[str] = []
        for historical_claim in historical_claim_list(historical_claims):
            if normalize_text(historical_claim.get("provider_id")) != provider_id:
                continue
            if not _shares_service_date(service_dates, claim_dates(historical_claim)):
                continue
            if (
                format_time_value(historical_claim.get("session_start_time")) == start_time
                and format_time_value(historical_claim.get("session_end_time")) == end_time
            ):
                conflicting_claims.append(normalize_text(historical_claim.get("claim_id")) or "unknown")

        if conflicting_claims:
            return self._fail(
                "Exact time conflict detected with a historical claim.",
                RedFlagLevel.HIGH,
                {"conflicting_claim_ids": conflicting_claims},
            )

        return self._pass("No exact time conflicts were detected.")


def _shares_service_date(current_dates: set[date], historical_dates: set[date]) -> bool:
    return bool(current_dates.intersection(historical_dates))
