# Sample Payloads

All sample files referenced here live in `sample_data/`.

## sample_bhs_matrix.json

```json
[
  {
    "proc_code": "90837",
    "mod1": "HN",
    "mod2": "HO",
    "mod3": null,
    "mod4": null,
    "pos_allowed": "11,02",
    "icd10": "F32.1,F41.1,Z63.0"
  },
  {
    "proc_code": "90834",
    "mod1": "HN",
    "mod2": null,
    "mod3": null,
    "mod4": null,
    "pos_allowed": "11,02",
    "icd10": "F32.1,F41.1"
  },
  {
    "proc_code": "H2017",
    "mod1": "HQ",
    "mod2": null,
    "mod3": null,
    "mod4": null,
    "pos_allowed": "11,03",
    "icd10": "F32.1,F33.1"
  }
]
```

## sample_cpt_credentials.json

```json
[
  {
    "cpt_code": "90837",
    "license": [
      "LCSW",
      "LMHC"
    ]
  },
  {
    "cpt_code": "90834",
    "license": [
      "LCSW",
      "LMHC"
    ]
  },
  {
    "cpt_code": "H2017",
    "license": [
      "LCSW"
    ]
  }
]
```

## sample_historical_claims.json

```json
[
  {
    "claim_id": "HIST-001",
    "provider_id": "PROV-001",
    "patient_id": "PAT-009",
    "service_date": "2026-06-28",
    "session_start_time": "08:00",
    "session_end_time": "09:00",
    "service_location": "Clinic B",
    "distance_miles": 12,
    "clinical_notes_text": "Prior day note focused on medication adherence and family communication planning."
  },
  {
    "claim_id": "HIST-002",
    "provider_id": "PROV-001",
    "patient_id": "PAT-010",
    "service_date": "2026-06-29",
    "session_start_time": "14:00",
    "session_end_time": "15:00",
    "service_location": "Clinic A",
    "distance_miles": 0,
    "clinical_notes_text": "Afternoon session note focused on school attendance and transportation coordination."
  }
]
```

## sample_extract_request.json

File:

`sample_data/sample_extract_request.json`

Purpose:

- provides realistic OCR text for `treatment_plan`, `clinical_notes`, and `dla20`
- can be posted directly to `POST /api/v1/ai/extract`

## sample_validate_request.json

File:

`sample_data/sample_validate_request.json`

Purpose:

- contains a full `ValidationRequest`
- includes extracted structured data plus master-data inputs
- can be posted directly to `POST /api/v1/ai/validate`

## sample_analyze_claim_response.json

File:

`sample_data/sample_analyze_claim_response.json`

Top-level shape:

```json
{
  "claim_id": "CLAIM-001",
  "ai_status": "validated",
  "compliance_score": 100.0,
  "score_band": "Excellent",
  "ocr_summary": {
    "total_documents": 3,
    "treatment_plan_documents": 1,
    "clinical_note_documents": 1,
    "dla20_documents": 1
  },
  "flag_summary": {
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "metadata": {
    "processing_time_ms": 842,
    "rules_executed": 19,
    "ocr_documents_processed": 3
  }
}
```

The full file includes:

- complete `extracted_data`
- all 19 `rule_results`
- realistic processing metadata

## sample standard error response

```json
{
  "status": "error",
  "request_id": "req-analyze-001",
  "error_code": "MISSING_REQUIRED_FILES",
  "message": "At least one file is required for treatment_plan_files.",
  "details": {
    "field": "treatment_plan_files"
  }
}
```

## Suggested usage

- Use `sample_extract_request.json` to verify extraction-only integration.
- Use `sample_validate_request.json` to verify validation-only integration.
- Use `sample_analyze_claim_response.json` as the backend-side response mapping reference.
- Serialize `sample_bhs_matrix.json`, `sample_cpt_credentials.json`, and `sample_historical_claims.json` into JSON strings when calling `POST /api/v1/ai/analyze-claim`.
