from fastapi.testclient import TestClient

from app.main import app


def _validation_payload() -> dict[str, object]:
    return {
        "claim_id": "CLAIM-001",
        "provider_id": "PROV-001",
        "patient_id": "PAT-001",
        "claim_date": "2026-06-29",
        "extracted_data": {
            "provider_license": "LICSW",
            "cpt_codes": ["90837"],
            "modifiers": ["HN"],
            "place_of_service": "11",
            "diagnosis_codes": ["F32.1"],
            "billed_units": 4,
            "session_start_time": "10:00",
            "session_end_time": "11:00",
            "session_duration_minutes": 60,
            "service_dates": ["2026-06-29"],
            "service_location": "Clinic A",
            "treatment_plan_date": "2026-05-01",
            "authorization_number": "AUTH-2026-4451",
            "provider_signature_present": True,
            "treatment_goals": ["Improve coping skills", "Stabilize housing"],
            "clinical_narrative": (
                "The patient worked on coping skills, emotional regulation, housing stability, "
                "sleep routine, self-care, community supports, communication strategies, safety "
                "planning, budgeting, problem solving, and family stress during the session. "
                "The clinician connected these interventions directly to the documented treatment "
                "goals and reviewed daily functioning tasks with the patient."
            ),
            "dla20_deficiency_areas": ["coping_skills", "housing_stability"],
            "dla20_scores": {
                "coping_skills": 2,
                "housing_stability": 2,
            },
            "dla20_total_score": 2.0,
            "treatment_plan_raw": (
                "Treatment plan references coping skills, housing stability, and daily living goals."
            ),
            "clinical_notes_raw": (
                "Patient worked on coping skills, housing stability, and daily functioning goals."
            ),
            "dla20_raw": "Coping skills: 2\nHousing stability: 2",
        },
        "bhs_matrix": [
            {
                "proc_code": "90837",
                "mod1": "HN",
                "mod2": None,
                "mod3": None,
                "mod4": None,
                "pos_allowed": "11,02",
                "icd10": "F32.1,F41.1",
            }
        ],
        "cpt_credentials": [{"cpt_code": "90837", "license": "LICSW"}],
        "historical_claims": [],
    }


def test_successful_validation_request() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/ai/validate", json=_validation_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "CLAIM-001"
    assert len(body["results"]) == 19
    assert 0 <= body["compliance_score"] <= 100
    assert body["score_band"]
    assert set(body["flag_summary"]) == {"high", "medium", "low"}


def test_validation_response_includes_exactly_19_results() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/ai/validate", json=_validation_payload())

    assert response.status_code == 200
    assert len(response.json()["results"]) == 19


def test_invalid_cpt_code_fails_schema_validation() -> None:
    client = TestClient(app)
    payload = _validation_payload()
    payload["extracted_data"]["cpt_codes"] = ["ABCDE"]  # type: ignore[index]

    response = client.post("/api/v1/ai/validate", json=payload)

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


def test_missing_optional_extracted_fields_do_not_crash_api() -> None:
    client = TestClient(app)
    payload = _validation_payload()
    payload["extracted_data"] = {
        "cpt_codes": ["90837"],
        "diagnosis_codes": ["F32.1"],
    }
    payload["bhs_matrix"] = [{"proc_code": "90837", "pos_allowed": "11", "icd10": "F32.1"}]
    payload["cpt_credentials"] = [{"cpt_code": "90837", "license": "LICSW"}]

    response = client.post("/api/v1/ai/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 19
    assert 0 <= body["compliance_score"] <= 100


def test_invalid_master_data_shape_returns_clean_error() -> None:
    client = TestClient(app)
    payload = _validation_payload()
    payload["bhs_matrix"] = [{"mod1": "HN"}]

    response = client.post("/api/v1/ai/validate", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["message"] == "Request validation failed."
