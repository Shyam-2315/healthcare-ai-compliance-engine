from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import goal_match_ratio, normalize_text

FILLER_PHRASES = [
    "lorem ipsum",
    "insert text here",
    "n/a",
    "see above",
    "same as before",
]


class ClinicalNoteMatchesTreatmentPlanGoalsRule(BaseRule):
    rule_id = "CN-001"
    rule_name = "Clinical Note Matches Treatment Plan Goals"
    category = "documentation"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        treatment_goals = extracted.get("treatment_goals", [])
        clinical_narrative = normalize_text(extracted.get("clinical_narrative"))
        if not treatment_goals or not clinical_narrative:
            return self._fail(
                "Treatment goals or clinical narrative are missing.",
                RedFlagLevel.MEDIUM,
                {"treatment_goals_present": bool(treatment_goals), "clinical_narrative_present": bool(clinical_narrative)},
            )

        ratio = goal_match_ratio(treatment_goals, clinical_narrative)
        if ratio < 0.5:
            return self._fail(
                "Clinical narrative does not reference enough treatment plan goals.",
                RedFlagLevel.MEDIUM,
                {"goal_match_ratio": round(ratio, 2)},
            )

        return self._pass(
            "Clinical narrative references the treatment plan goals.",
            {"goal_match_ratio": round(ratio, 2)},
        )


class ProgressNoteSignedByProviderRule(BaseRule):
    rule_id = "SIG-001"
    rule_name = "Progress Note Signed by Provider"
    category = "documentation"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        if extracted.get("provider_signature_present") is True:
            return self._pass("Progress note is signed by the provider.")
        return self._fail("Progress note is missing a provider signature.", RedFlagLevel.MEDIUM)


class ContentQualityMeetsDocumentationStandardRule(BaseRule):
    rule_id = "CQ-001"
    rule_name = "Content Quality Meets Documentation Standard"
    category = "documentation"
    priority = RulePriority.LOW

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        clinical_narrative = normalize_text(extracted.get("clinical_narrative"))
        if not clinical_narrative:
            return self._fail("Clinical narrative is missing.", RedFlagLevel.LOW)

        lowered = clinical_narrative.lower()
        filler_hits = [phrase for phrase in FILLER_PHRASES if phrase in lowered]
        word_count = len([word for word in clinical_narrative.split() if word.strip()])
        if filler_hits or word_count < 50:
            return self._fail(
                "Clinical narrative does not meet the documentation quality standard.",
                RedFlagLevel.LOW,
                {"word_count": word_count, "filler_hits": filler_hits},
            )

        return self._pass(
            "Clinical narrative meets the documentation quality standard.",
            {"word_count": word_count},
        )
