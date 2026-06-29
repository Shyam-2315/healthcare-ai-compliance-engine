from app.services.rule_engine.base_rule import ComplianceRule
from app.services.rule_engine.rules.billing_rules import BillingAmountRule
from app.services.rule_engine.rules.coding_rules import CptCodePresenceRule
from app.services.rule_engine.rules.credential_rules import CredentialRule
from app.services.rule_engine.rules.dla20_rules import DLA20DocumentationRule
from app.services.rule_engine.rules.documentation_rules import DocumentationCompletenessRule
from app.services.rule_engine.rules.fraud_detection_rules import DuplicateClaimRule
from app.services.rule_engine.rules.travel_rules import TravelDocumentationRule
from app.services.rule_engine.rules.treatment_plan_rules import TreatmentPlanRule


def get_registered_rules() -> list[ComplianceRule]:
    return [
        TreatmentPlanRule(),
        CptCodePresenceRule(),
        BillingAmountRule(),
        DocumentationCompletenessRule(),
        CredentialRule(),
        TravelDocumentationRule(),
        DLA20DocumentationRule(),
        DuplicateClaimRule(),
    ]
