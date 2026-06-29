from typing import Any

from app.api.schemas.common import ComplianceFinding
from app.services.rule_engine.base_rule import (
    BaseRule,
    ComplianceRule,
    RulePriority,
    RuleStatus,
    Severity,
)
from app.services.rule_engine.rules.billing_rules import (
    NoTimeOverlapInClaimsRule,
    SessionDurationMatchesBilledUnitsRule,
    UnitsWithinAllowableRangeRule,
)
from app.services.rule_engine.rules.coding_rules import (
    CptCodeValidPerBhsMatrixRule,
    DiagnosisCodeValidRule,
    ModifierValidForCptCodeRule,
    PlaceOfServiceAllowedRule,
)
from app.services.rule_engine.rules.credential_rules import ProviderLicenseMatchesCptCodeRule
from app.services.rule_engine.rules.dla20_rules import (
    Dla20GoalsReferencedInTreatmentPlanRule,
    FunctionalDeficiencyScoreAlignsWithServiceLevelRule,
)
from app.services.rule_engine.rules.documentation_rules import (
    ClinicalNoteMatchesTreatmentPlanGoalsRule,
    ContentQualityMeetsDocumentationStandardRule,
    ProgressNoteSignedByProviderRule,
)
from app.services.rule_engine.rules.fraud_detection_rules import (
    CloneNotesDetectionRule,
    TimeConflictDetectionRule,
)
from app.services.rule_engine.rules.travel_rules import TravelFeasibilityBetweenServiceLocationsRule
from app.services.rule_engine.rules.treatment_plan_rules import (
    AuthorizationPresentRule,
    GoalsAlignWithDla20DeficienciesRule,
    TreatmentPlanCurrentRule,
)

EXPECTED_RULE_COUNT = 19


def get_all_rules() -> list[BaseRule]:
    return [
        TreatmentPlanCurrentRule(),
        AuthorizationPresentRule(),
        GoalsAlignWithDla20DeficienciesRule(),
        CptCodeValidPerBhsMatrixRule(),
        ModifierValidForCptCodeRule(),
        PlaceOfServiceAllowedRule(),
        DiagnosisCodeValidRule(),
        SessionDurationMatchesBilledUnitsRule(),
        UnitsWithinAllowableRangeRule(),
        NoTimeOverlapInClaimsRule(),
        ClinicalNoteMatchesTreatmentPlanGoalsRule(),
        ProgressNoteSignedByProviderRule(),
        ContentQualityMeetsDocumentationStandardRule(),
        ProviderLicenseMatchesCptCodeRule(),
        TravelFeasibilityBetweenServiceLocationsRule(),
        FunctionalDeficiencyScoreAlignsWithServiceLevelRule(),
        Dla20GoalsReferencedInTreatmentPlanRule(),
        CloneNotesDetectionRule(),
        TimeConflictDetectionRule(),
    ]


def get_rule_count() -> int:
    return len(get_all_rules())


def validate_rule_registry() -> bool:
    rules = get_all_rules()
    rule_ids = [rule.rule_id for rule in rules]
    return (
        len(rules) == EXPECTED_RULE_COUNT
        and len(rule_ids) == len(set(rule_ids))
        and all(rule.rule_name.strip() for rule in rules)
        and all(rule.category.strip() for rule in rules)
    )


def get_registered_rules() -> list[ComplianceRule]:
    return [_CompatibilityRuleAdapter(rule) for rule in get_all_rules()]


class _CompatibilityRuleAdapter(ComplianceRule):
    def __init__(self, rule: BaseRule) -> None:
        self._rule = rule
        self.rule_id = rule.rule_id
        self.title = rule.rule_name
        self.severity = _priority_to_severity(rule.priority)

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]) -> ComplianceFinding:
        result = self._rule.evaluate(
            claim,
            context.get("bhs_matrix", {}),
            context.get("cpt_credentials", {}),
            context.get("historical_claims", []),
        )
        return ComplianceFinding(
            rule_id=result.rule_id,
            title=result.rule_name,
            severity=self.severity,
            passed=result.status == RuleStatus.PASS,
            message=result.message,
            evidence=result.detail,
        )


def _priority_to_severity(priority: RulePriority) -> Severity:
    if priority == RulePriority.HIGH:
        return "high"
    if priority == RulePriority.MEDIUM:
        return "medium"
    return "low"
