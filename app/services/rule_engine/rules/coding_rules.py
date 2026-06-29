from typing import Any

from app.services.rule_engine.base_rule import ComplianceRule


class CptCodePresenceRule(ComplianceRule):
    rule_id = "COD-001"
    title = "CPT coding is present"
    severity = "medium"

    def evaluate(self, claim: dict[str, Any], context: dict[str, Any]):
        cpt_codes = claim.get("cpt_codes") or []
        return self.finding(
            passed=bool(cpt_codes),
            message="At least one CPT code is present." if cpt_codes else "No CPT codes were found.",
            evidence={"cpt_codes": cpt_codes},
        )
