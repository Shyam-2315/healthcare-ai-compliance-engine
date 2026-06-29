from typing import Any

from app.services.rule_engine.base_rule import (
    BaseRule,
    RedFlagLevel,
    RulePriority,
    RuleResult,
    RuleStatus,
)
from app.services.rule_engine.engine import RuleEngine
from app.services.rule_engine.registry import get_all_rules, get_rule_count, validate_rule_registry


class DummyPassRule(BaseRule):
    rule_id = "PASS-001"
    rule_name = "Dummy pass rule"
    category = "test"
    priority = RulePriority.MEDIUM

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        return self._pass("Passed.", {"claim_id": extracted.get("claim_id")})


class DummyFailRule(BaseRule):
    rule_id = "FAIL-001"
    rule_name = "Dummy fail rule"
    category = "test"
    priority = RulePriority.HIGH

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        return self._fail("Failed.", RedFlagLevel.HIGH, {"reason": "missing"})


class DummyCrashRule(BaseRule):
    rule_id = "CRASH-001"
    rule_name = "Dummy crash rule"
    category = "test"
    priority = RulePriority.LOW

    def evaluate(
        self,
        extracted: dict[str, Any],
        bhs_matrix: dict[str, Any],
        cpt_credentials: dict[str, Any],
        historical_claims: list[dict[str, Any]],
    ) -> RuleResult:
        raise RuntimeError("boom")


def test_dummy_pass_rule_works() -> None:
    result = DummyPassRule().evaluate({"claim_id": "CLAIM-001"}, {}, {}, [])

    assert result.status == RuleStatus.PASS
    assert result.red_flag_level == RedFlagLevel.NONE
    assert result.detail == {"claim_id": "CLAIM-001"}


def test_dummy_fail_rule_works() -> None:
    result = DummyFailRule().evaluate({}, {}, {}, [])

    assert result.status == RuleStatus.FAIL
    assert result.red_flag_level == RedFlagLevel.HIGH


def test_rule_engine_continues_if_one_rule_crashes() -> None:
    output = RuleEngine([DummyPassRule(), DummyCrashRule(), DummyFailRule()]).run(
        {"claim_id": "CLAIM-001"},
        {},
        {},
        [],
    )

    assert [result.rule_id for result in output.results] == ["PASS-001", "CRASH-001", "FAIL-001"]
    assert len(output.passed_rules) == 1
    assert len(output.failed_rules) == 2
    assert output.failed_rules[0].message == "Rule execution failed: boom"


def test_rule_engine_flag_counts_are_correct() -> None:
    output = RuleEngine([DummyFailRule(), DummyCrashRule()]).run({}, {}, {}, [])

    assert output.high_red_flags == 1
    assert output.medium_red_flags == 0
    assert output.low_red_flags == 1
    assert output.total_rules == 2


def test_phase6_registry_is_valid() -> None:
    assert get_rule_count() == 19
    assert validate_rule_registry() is True


def test_rule_engine_with_all_rules_returns_19_results() -> None:
    output = RuleEngine(get_all_rules()).run(
        {
            "claim_id": "CLAIM-001",
            "provider_id": "PROV-001",
            "claim_date": "2026-06-29",
            "treatment_plan_date": "2026-06-01",
            "authorization_number": "AUTH-12345",
            "treatment_goals": ["Improve coping skills", "Stabilize housing"],
            "dla20_deficiency_areas": ["coping_skills", "housing_stability"],
            "treatment_plan_raw": "Goals include coping skills improvement and housing stabilization support.",
            "cpt_codes": ["90837"],
            "modifiers": ["HN"],
            "place_of_service": "11",
            "diagnosis_codes": ["F32.1"],
            "session_duration_minutes": 60,
            "billed_units": 4,
            "service_dates": ["2026-06-29"],
            "session_start_time": "09:00",
            "session_end_time": "10:00",
            "clinical_narrative": (
                "The clinician reviewed coping skills, emotional regulation, housing stability, "
                "budget planning, community supports, medication adherence, stress management, "
                "sleep hygiene, communication strategies, family stressors, and relapse "
                "prevention during the session while documenting progress toward treatment goals "
                "with patient-specific interventions and response."
            ),
            "provider_signature_present": True,
            "provider_license": "LCSW",
            "service_location": "Clinic A",
            "dla20_total_score": 2,
            "clinical_notes_raw": "Unique progress note text.",
        },
        {
            "rows": [
                {
                    "proc_code": "90837",
                    "mod1": "HN",
                    "pos_allowed": ["11"],
                    "icd10": ["F32.1"],
                }
            ]
        },
        {"cpt_credentials": {"90837": ["LCSW"]}},
        [],
    )

    assert len(output.results) == 19
