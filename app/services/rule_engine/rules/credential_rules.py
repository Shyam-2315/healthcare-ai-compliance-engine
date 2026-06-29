from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import normalize_cpt_credentials, normalize_text


class ProviderLicenseMatchesCptCodeRule(BaseRule):
    rule_id = "CRED-001"
    rule_name = "Provider License Matches CPT Code"
    category = "credential"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        provider_license = normalize_text(extracted.get("provider_license")).upper()
        cpt_codes = [normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)]
        if not provider_license:
            return self._fail("Provider license is missing.", RedFlagLevel.HIGH)
        if not cpt_codes:
            return self._fail("Provider credentials cannot be validated without CPT codes.", RedFlagLevel.HIGH)

        credential_map = normalize_cpt_credentials(cpt_credentials)
        unauthorized_codes = [
            cpt_code
            for cpt_code in cpt_codes
            if credential_map.get(cpt_code) and provider_license not in credential_map[cpt_code]
        ]
        if unauthorized_codes:
            return self._fail(
                "Provider license is not authorized for one or more billed CPT codes.",
                RedFlagLevel.HIGH,
                {"provider_license": provider_license, "unauthorized_cpt_codes": unauthorized_codes},
            )

        return self._pass(
            "Provider license is authorized for the billed CPT codes.",
            {"provider_license": provider_license, "cpt_codes": cpt_codes},
        )
