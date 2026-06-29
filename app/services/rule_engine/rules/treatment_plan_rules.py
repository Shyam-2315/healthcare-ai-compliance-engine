from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import keywords_for_area, normalize_text, text_references_area
from app.utils.date_utils import days_between, safe_parse_date

PLAN_VALIDITY_DAYS = 180


class TreatmentPlanCurrentRule(BaseRule):
    rule_id = "TP-001"
    rule_name = "Treatment Plan Must Be Current"
    category = "treatment_plan"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        claim_date = safe_parse_date(extracted.get("claim_date"))
        treatment_plan_date = safe_parse_date(extracted.get("treatment_plan_date"))
        if claim_date is None or treatment_plan_date is None:
            return self._fail(
                "Claim date or treatment plan date is missing.",
                RedFlagLevel.HIGH,
                {"claim_date": extracted.get("claim_date"), "treatment_plan_date": extracted.get("treatment_plan_date")},
            )

        age_days = days_between(treatment_plan_date, claim_date)
        if age_days is None or age_days < 0 or age_days > PLAN_VALIDITY_DAYS:
            return self._fail(
                "Treatment plan is missing or expired for the claim date.",
                RedFlagLevel.HIGH,
                {"age_days": age_days, "validity_days": PLAN_VALIDITY_DAYS},
            )

        return self._pass(
            "Treatment plan is current for the claim date.",
            {"age_days": age_days, "validity_days": PLAN_VALIDITY_DAYS},
        )


class AuthorizationPresentRule(BaseRule):
    rule_id = "TP-002"
    rule_name = "Authorization Present on Plan"
    category = "treatment_plan"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        authorization_number = normalize_text(extracted.get("authorization_number"))
        if len(authorization_number) < 5:
            return self._fail(
                "Authorization number is missing or too short on the treatment plan.",
                RedFlagLevel.HIGH,
                {"authorization_number": authorization_number},
            )

        return self._pass(
            "Authorization number is present on the treatment plan.",
            {"authorization_number": authorization_number},
        )


class GoalsAlignWithDla20DeficienciesRule(BaseRule):
    rule_id = "TP-003"
    rule_name = "Goals Align with DLA-20 Deficiencies"
    category = "treatment_plan"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        treatment_goals = [normalize_text(goal) for goal in extracted.get("treatment_goals", []) if normalize_text(goal)]
        deficiency_areas = [normalize_text(area) for area in extracted.get("dla20_deficiency_areas", []) if normalize_text(area)]
        if not treatment_goals or not deficiency_areas:
            return self._fail(
                "Treatment goals or DLA-20 deficiency areas are missing.",
                RedFlagLevel.HIGH,
                {"treatment_goals": treatment_goals, "deficiency_areas": deficiency_areas},
            )

        combined_goals = " ".join(treatment_goals)
        unaddressed = [
            area
            for area in deficiency_areas
            if not any(keyword.lower() in combined_goals.lower() for keyword in keywords_for_area(area))
            and not text_references_area(combined_goals, area)
        ]
        if unaddressed:
            return self._fail(
                "Treatment plan goals do not address all DLA-20 deficiency areas.",
                RedFlagLevel.HIGH,
                {"unaddressed_deficiencies": unaddressed},
            )

        return self._pass(
            "Treatment plan goals align with documented DLA-20 deficiencies.",
            {"deficiency_areas": deficiency_areas},
        )
