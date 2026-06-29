from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import normalize_text, text_references_area

INTENSIVE_CPT_CODES = {"90837", "90847", "H2017"}


class FunctionalDeficiencyScoreAlignsWithServiceLevelRule(BaseRule):
    rule_id = "DLA-001"
    rule_name = "Functional Deficiency Score Aligns with Service Level"
    category = "dla20"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        cpt_codes = {normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)}
        if not cpt_codes.intersection(INTENSIVE_CPT_CODES):
            return self._pass("No intensive service codes were billed. Rule treated as not applicable.")

        score = extracted.get("dla20_total_score")
        if score is None:
            return self._fail("DLA-20 total score is missing for an intensive service.", RedFlagLevel.MEDIUM)
        if float(score) > 2.5:
            return self._fail(
                "DLA-20 total score is too high for the billed intensive service level.",
                RedFlagLevel.MEDIUM,
                {"dla20_total_score": score, "intensive_cpt_codes": sorted(cpt_codes.intersection(INTENSIVE_CPT_CODES))},
            )

        return self._pass(
            "DLA-20 total score aligns with the billed intensive service level.",
            {"dla20_total_score": score},
        )


class Dla20GoalsReferencedInTreatmentPlanRule(BaseRule):
    rule_id = "DLA-002"
    rule_name = "DLA-20 Goals Referenced in Treatment Plan"
    category = "dla20"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        deficiency_areas = [normalize_text(area) for area in extracted.get("dla20_deficiency_areas", []) if normalize_text(area)]
        treatment_plan_raw = normalize_text(extracted.get("treatment_plan_raw"))
        if not deficiency_areas:
            return self._pass("No DLA-20 deficiency areas were supplied. Rule treated as not applicable.")
        if not treatment_plan_raw:
            return self._fail("Treatment plan text is missing for DLA-20 cross-reference validation.", RedFlagLevel.MEDIUM)

        missing_references = [area for area in deficiency_areas if not text_references_area(treatment_plan_raw, area)]
        if missing_references:
            return self._fail(
                "Treatment plan does not reference all documented DLA-20 deficiency areas.",
                RedFlagLevel.MEDIUM,
                {"missing_references": missing_references},
            )

        return self._pass(
            "Treatment plan references the documented DLA-20 deficiency areas.",
            {"deficiency_areas": deficiency_areas},
        )
