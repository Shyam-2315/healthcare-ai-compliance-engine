from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class TreatmentPlanRule(ComplianceRule):
    rule_id = "TP-001"
    title = "Treatment plan is present"
    severity = "high"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        treatment_plan = claim.get("treatment_plan") or context.get("treatment_plan")
        return self.finding(
            passed=bool(treatment_plan),
            message=(
                "Treatment plan documentation is present."
                if treatment_plan
                else "Treatment plan documentation is missing."
            ),
            evidence={"treatment_plan_present": bool(treatment_plan)},
        )
