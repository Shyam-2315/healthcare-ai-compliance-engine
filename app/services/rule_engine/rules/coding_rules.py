import re
from typing import Any

from app.services.rule_engine.base_rule import BaseRule, RedFlagLevel, RulePriority, RuleResult
from app.services.rule_engine.rules._shared import extract_allowed_values, normalize_text, rows_for_cpt

ICD10_PATTERN = re.compile(r"^[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?$")


class CptCodeValidPerBhsMatrixRule(BaseRule):
    rule_id = "CPT-001"
    rule_name = "CPT Code Valid per BHS Matrix"
    category = "coding"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        cpt_codes = [normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)]
        if not cpt_codes:
            return self._fail("No CPT codes were provided for validation.", RedFlagLevel.HIGH)

        invalid_codes = [code for code in cpt_codes if not rows_for_cpt(bhs_matrix, code)]
        if invalid_codes:
            return self._fail(
                "One or more CPT codes are not valid per the BHS matrix.",
                RedFlagLevel.HIGH,
                {"invalid_cpt_codes": invalid_codes},
            )

        return self._pass("All CPT codes are valid per the BHS matrix.", {"cpt_codes": cpt_codes})


class ModifierValidForCptCodeRule(BaseRule):
    rule_id = "MOD-001"
    rule_name = "Modifier Valid for CPT Code"
    category = "coding"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        modifiers = [normalize_text(modifier).upper() for modifier in extracted.get("modifiers", []) if normalize_text(modifier)]
        cpt_codes = [normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)]
        if not modifiers:
            return self._pass("No modifiers were supplied. Rule treated as not applicable.")
        if not cpt_codes:
            return self._fail("Modifiers were supplied without CPT codes.", RedFlagLevel.MEDIUM)

        allowed_modifiers: set[str] = set()
        for cpt_code in cpt_codes:
            for row in rows_for_cpt(bhs_matrix, cpt_code):
                allowed_modifiers.update(extract_allowed_values(row, "mod1", "mod2", "mod3", "mod4", "modifiers"))

        invalid_modifiers = [modifier for modifier in modifiers if modifier not in allowed_modifiers]
        if invalid_modifiers:
            return self._fail(
                "One or more modifiers are not valid for the billed CPT codes.",
                RedFlagLevel.MEDIUM,
                {"invalid_modifiers": invalid_modifiers, "allowed_modifiers": sorted(allowed_modifiers)},
            )

        return self._pass(
            "All modifiers are valid for the billed CPT codes.",
            {"modifiers": modifiers},
        )


class PlaceOfServiceAllowedRule(BaseRule):
    rule_id = "POS-001"
    rule_name = "Place of Service Allowed per BHS Matrix"
    category = "coding"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        place_of_service = normalize_text(extracted.get("place_of_service"))
        cpt_codes = [normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)]
        if not place_of_service:
            return self._fail("Place of service is missing.", RedFlagLevel.HIGH)
        if not cpt_codes:
            return self._fail("Place of service cannot be validated without CPT codes.", RedFlagLevel.HIGH)

        invalid_cpts: list[str] = []
        for cpt_code in cpt_codes:
            rows = rows_for_cpt(bhs_matrix, cpt_code)
            allowed_pos = set().union(*(extract_allowed_values(row, "pos_allowed", "place_of_service") for row in rows))
            if not rows or (allowed_pos and place_of_service.upper() not in allowed_pos):
                invalid_cpts.append(cpt_code)

        if invalid_cpts:
            return self._fail(
                "Place of service is not allowed for one or more billed CPT codes.",
                RedFlagLevel.HIGH,
                {"place_of_service": place_of_service, "invalid_cpt_codes": invalid_cpts},
            )

        return self._pass(
            "Place of service is allowed for the billed CPT codes.",
            {"place_of_service": place_of_service},
        )


class DiagnosisCodeValidRule(BaseRule):
    rule_id = "DX-001"
    rule_name = "ICD-10 Diagnosis Code Valid"
    category = "coding"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        diagnosis_codes = [normalize_text(code).upper() for code in extracted.get("diagnosis_codes", []) if normalize_text(code)]
        if not diagnosis_codes:
            return self._fail("No diagnosis codes were provided for validation.", RedFlagLevel.HIGH)

        invalid_format = [code for code in diagnosis_codes if not ICD10_PATTERN.fullmatch(code)]
        if invalid_format:
            return self._fail(
                "One or more diagnosis codes do not match ICD-10 format.",
                RedFlagLevel.HIGH,
                {"invalid_diagnosis_codes": invalid_format},
            )

        approved_codes: set[str] = set()
        for cpt_code in [normalize_text(code) for code in extracted.get("cpt_codes", []) if normalize_text(code)]:
            for row in rows_for_cpt(bhs_matrix, cpt_code):
                approved_codes.update(extract_allowed_values(row, "icd10", "icd10_list", "diagnosis_codes"))

        unapproved_codes = [code for code in diagnosis_codes if approved_codes and code not in approved_codes]
        if unapproved_codes:
            return self._fail(
                "One or more diagnosis codes are not approved in the BHS matrix.",
                RedFlagLevel.HIGH,
                {"unapproved_diagnosis_codes": unapproved_codes},
            )

        return self._pass(
            "Diagnosis codes are valid for billing.",
            {"diagnosis_codes": diagnosis_codes},
        )
