from copy import deepcopy
from datetime import date, time
from typing import Any

import pytest

from app.services.rule_engine.base_rule import RuleResult, RuleStatus
from app.services.rule_engine.registry import get_all_rules


def _base_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    extracted = {
        "claim_id": "CLAIM-001",
        "provider_id": "PROV-001",
        "patient_id": "PAT-001",
        "claim_date": date(2026, 6, 29),
        "treatment_plan_date": date(2026, 6, 1),
        "authorization_number": "AUTH-12345",
        "treatment_goals": ["Improve coping skills", "Stabilize housing"],
        "dla20_deficiency_areas": ["coping_skills", "housing_stability"],
        "treatment_plan_raw": (
            "Treatment goals include improving coping skills, strengthening housing stability, "
            "and maintaining a safe home routine with practical daily supports."
        ),
        "cpt_codes": ["90837"],
        "modifiers": ["HN"],
        "place_of_service": "11",
        "diagnosis_codes": ["F32.1"],
        "session_duration_minutes": 60,
        "billed_units": 4,
        "service_dates": [date(2026, 6, 29)],
        "session_start_time": time(9, 0),
        "session_end_time": time(10, 0),
        "clinical_narrative": (
            "The clinician reviewed coping skills, grounding techniques, housing stability plans, "
            "budgeting steps, communication strategies, sleep routine goals, medication adherence, "
            "family stressors, problem solving, emotional regulation, safety planning, and community "
            "supports. The patient practiced coping skills in session, discussed housing follow-up tasks, "
            "identified barriers, responded to coaching, and agreed to continue the documented treatment goals."
        ),
        "provider_signature_present": True,
        "provider_license": "LCSW",
        "service_location": "Clinic A",
        "dla20_total_score": 2,
        "clinical_notes_raw": (
            "Unique clinical note about coping skills, housing stability, and patient-specific interventions."
        ),
    }
    bhs_matrix = {
        "rows": [
            {
                "proc_code": "90837",
                "mod1": "HN",
                "mod2": "HO",
                "pos_allowed": ["11", "02"],
                "icd10": ["F32.1", "F41.1", "Z63.0"],
            }
        ]
    }
    cpt_credentials = {"cpt_credentials": {"90837": ["LCSW", "LMHC"], "H2017": ["LCSW"]}}
    historical_claims: list[dict[str, Any]] = []
    return extracted, bhs_matrix, cpt_credentials, historical_claims


def _fail_case(rule_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    extracted, bhs_matrix, cpt_credentials, historical_claims = _base_inputs()
    extracted = deepcopy(extracted)
    bhs_matrix = deepcopy(bhs_matrix)
    cpt_credentials = deepcopy(cpt_credentials)
    historical_claims = deepcopy(historical_claims)

    if rule_id == "TP-001":
        extracted["treatment_plan_date"] = date(2025, 1, 1)
    elif rule_id == "TP-002":
        extracted["authorization_number"] = "1234"
    elif rule_id == "TP-003":
        extracted["treatment_goals"] = ["Improve coping skills"]
    elif rule_id == "CPT-001":
        extracted["cpt_codes"] = ["99999"]
    elif rule_id == "MOD-001":
        extracted["modifiers"] = ["ZZ"]
    elif rule_id == "POS-001":
        extracted["place_of_service"] = "99"
    elif rule_id == "DX-001":
        extracted["diagnosis_codes"] = ["INVALID"]
    elif rule_id == "DUR-001":
        extracted["billed_units"] = 2
    elif rule_id == "UNIT-001":
        extracted["billed_units"] = 17
    elif rule_id == "TOVL-001":
        historical_claims.append(
            {
                "claim_id": "HIST-OVL",
                "provider_id": "PROV-001",
                "service_dates": [date(2026, 6, 29)],
                "session_start_time": "09:30",
                "session_end_time": "10:30",
            }
        )
    elif rule_id == "CN-001":
        extracted["clinical_narrative"] = "Patient discussed paperwork, medication refill logistics, and billing."
    elif rule_id == "SIG-001":
        extracted["provider_signature_present"] = False
    elif rule_id == "CQ-001":
        extracted["clinical_narrative"] = "lorem ipsum"
    elif rule_id == "CRED-001":
        extracted["provider_license"] = "RBT"
    elif rule_id == "TRV-001":
        historical_claims.append(
            {
                "claim_id": "HIST-TRV",
                "provider_id": "PROV-001",
                "service_dates": [date(2026, 6, 29)],
                "session_start_time": "08:00",
                "session_end_time": "08:30",
                "service_location": "Clinic B",
                "distance_miles": 40,
            }
        )
    elif rule_id == "DLA-001":
        extracted["dla20_total_score"] = 4
    elif rule_id == "DLA-002":
        extracted["treatment_plan_raw"] = "Treatment goals include improving coping skills only."
    elif rule_id == "FRD-001":
        historical_claims.append(
            {
                "claim_id": "HIST-CLONE",
                "clinical_notes_text": extracted["clinical_notes_raw"],
            }
        )
    elif rule_id == "FRD-002":
        historical_claims.append(
            {
                "claim_id": "HIST-TIME",
                "provider_id": "PROV-001",
                "service_dates": [date(2026, 6, 29)],
                "session_start_time": "09:00",
                "session_end_time": "10:00",
            }
        )
    else:
        raise AssertionError(f"Unhandled rule id: {rule_id}")

    return extracted, bhs_matrix, cpt_credentials, historical_claims


RULES = get_all_rules()


@pytest.mark.parametrize("rule", RULES, ids=[rule.rule_id for rule in RULES])
def test_every_rule_has_a_pass_case(rule: Any) -> None:
    extracted, bhs_matrix, cpt_credentials, historical_claims = _base_inputs()

    result = rule.evaluate(extracted, bhs_matrix, cpt_credentials, historical_claims)

    assert isinstance(result, RuleResult)
    assert result.status == RuleStatus.PASS


@pytest.mark.parametrize("rule", RULES, ids=[rule.rule_id for rule in RULES])
def test_every_rule_has_a_fail_case(rule: Any) -> None:
    extracted, bhs_matrix, cpt_credentials, historical_claims = _fail_case(rule.rule_id)

    result = rule.evaluate(extracted, bhs_matrix, cpt_credentials, historical_claims)

    assert isinstance(result, RuleResult)
    assert result.status == RuleStatus.FAIL
