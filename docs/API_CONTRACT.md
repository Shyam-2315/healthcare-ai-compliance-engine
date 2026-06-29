# API Contract

This document describes the production-facing contract for the healthcare compliance AI microservice.

Base URL examples in this document use:

```text
http://127.0.0.1:8001
```

All endpoints return `X-Request-ID` in the response headers. Error responses use the standard shape:

```json
{
  "status": "error",
  "request_id": "req-123456",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed.",
  "details": {}
}
```

## GET /api/v1/ai/health

### Purpose

Readiness and liveness check for local, container, and backend platform integration.

### Request type

`GET`

### Request fields

None.

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Always `ok` on success |
| `service` | string | Service name from configuration |
| `version` | string | Application version |
| `environment` | string | Active environment name |

### Success response example

```json
{
  "status": "ok",
  "service": "healthcare-compliance-ai",
  "version": "1.0.0",
  "environment": "local"
}
```

### Error response example

```json
{
  "status": "error",
  "request_id": "req-123456",
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected internal error occurred.",
  "details": {}
}
```

### curl example

```bash
curl http://127.0.0.1:8001/api/v1/ai/health
```

### Backend usage note

Use this endpoint for deployment health checks, container health checks, and upstream service readiness validation before sending claims for processing.

## POST /api/v1/ai/ocr

### Purpose

Run OCR on uploaded claim-supporting documents and return raw extracted text plus OCR metadata.

### Request type

`multipart/form-data`

### Request fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `document_type` | string | Yes | One of `treatment_plan`, `clinical_notes`, `dla20` |
| `files` | file[] | Yes | One or more supported files: `.pdf`, `.docx`, `.jpg`, `.jpeg`, `.png` |

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| `document_type` | string | Echoes the request document type |
| `results` | array | OCR results for each uploaded file |
| `results[].document_id` | string | Generated OCR document identifier |
| `results[].document_type` | string | Document type for the OCR result |
| `results[].file_name` | string | Original uploaded filename |
| `results[].raw_text` | string | OCR extracted text |
| `results[].page_count` | integer | Number of pages processed |
| `results[].confidence` | number | OCR confidence value between `0` and `1` |
| `results[].metadata` | object | Safe OCR metadata such as method and provider |

### Success response example

```json
{
  "document_type": "clinical_notes",
  "results": [
    {
      "document_id": "6f6bc9f9-6a4d-4211-8f7d-8bf15c2d7646",
      "document_type": "clinical_notes",
      "file_name": "clinical-note-2026-06-29.docx",
      "raw_text": "Service Date: 06/29/2026\nCPT: 90837-HN\nDiagnosis: F32.1",
      "page_count": 1,
      "confidence": 1.0,
      "metadata": {
        "method": "python-docx",
        "provider": "local"
      }
    }
  ]
}
```

### Error response example

```json
{
  "status": "error",
  "request_id": "req-ocr-001",
  "error_code": "UNSUPPORTED_FILE_TYPE",
  "message": "Unsupported file extension '.txt'. Supported extensions: .docx, .jpeg, .jpg, .pdf, .png.",
  "details": {}
}
```

### curl example

```bash
curl -X POST http://127.0.0.1:8001/api/v1/ai/ocr \
  -F "document_type=clinical_notes" \
  -F "files=@./path/to/clinical-note.docx"
```

### Backend usage note

This endpoint is useful for debugging and operational inspection. The primary backend integration path should still be `POST /api/v1/ai/analyze-claim`.

## POST /api/v1/ai/extract

### Purpose

Convert OCR text into structured claim data using the deterministic AI extraction layer.

### Request type

`application/json`

### Request fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `claim_id` | string | Yes | Claim identifier provided by the backend |
| `provider_id` | string | Yes | Provider identifier provided by the backend |
| `patient_id` | string | Yes | Patient identifier provided by the backend |
| `claim_date` | date | Yes | Claim date provided by the backend |
| `ocr_results` | array | Yes | OCR inputs with `document_type` and `raw_text` |
| `claim_context` | object | No | Optional additional metadata |

`ocr_results[].document_type` must be one of `treatment_plan`, `clinical_notes`, or `dla20`.

### Response fields

The response body is `ExtractedClaimData`:

- `claim_id`
- `provider_id`
- `patient_id`
- `claim_date`
- `patient_name`
- `patient_dob`
- `provider_name`
- `provider_license`
- `provider_npi`
- `service_dates`
- `session_start_time`
- `session_end_time`
- `session_duration_minutes`
- `service_location`
- `cpt_codes`
- `modifiers`
- `place_of_service`
- `diagnosis_codes`
- `billed_units`
- `treatment_plan_date`
- `authorization_number`
- `treatment_goals`
- `clinical_narrative`
- `clinical_note_date`
- `provider_signature_present`
- `dla20_deficiency_areas`
- `dla20_scores`
- `dla20_total_score`
- `treatment_plan_raw`
- `clinical_notes_raw`
- `dla20_raw`

### Success response example

```json
{
  "claim_id": "CLAIM-001",
  "provider_id": "PROV-001",
  "patient_id": "PAT-001",
  "claim_date": "2026-06-29",
  "patient_name": "Jane Doe",
  "patient_dob": "1990-05-14",
  "provider_name": "Jordan Smith, LCSW",
  "provider_license": "LCSW",
  "provider_npi": "1234567890",
  "service_dates": [
    "2026-06-29"
  ],
  "session_start_time": "09:00:00",
  "session_end_time": "10:00:00",
  "session_duration_minutes": 60,
  "service_location": "Clinic A",
  "cpt_codes": [
    "90837"
  ],
  "modifiers": [
    "HN"
  ],
  "place_of_service": "11",
  "diagnosis_codes": [
    "F32.1"
  ],
  "billed_units": 4,
  "treatment_plan_date": "2026-06-01",
  "authorization_number": "AUTH-2026-4451",
  "provider_signature_present": true,
  "dla20_total_score": 2.0
}
```

### Error response example

```json
{
  "status": "error",
  "request_id": "req-extract-001",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed.",
  "details": {
    "path": "/api/v1/ai/extract",
    "errors": [
      {
        "loc": [
          "body",
          "ocr_results",
          0,
          "document_type"
        ],
        "type": "literal_error"
      }
    ]
  }
}
```

### curl example

```bash
curl -X POST http://127.0.0.1:8001/api/v1/ai/extract \
  -H "Content-Type: application/json" \
  --data @sample_data/sample_extract_request.json
```

### Backend usage note

This endpoint is helpful when the backend already has OCR text or needs to inspect extraction behavior independently. In the normal claim-processing flow, prefer `POST /api/v1/ai/analyze-claim`.

## POST /api/v1/ai/validate

### Purpose

Run the 19-rule compliance engine on already extracted claim data.

### Request type

`application/json`

### Request fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `claim_id` | string | Yes | Claim identifier |
| `provider_id` | string | Yes | Provider identifier |
| `patient_id` | string | Yes | Patient identifier |
| `claim_date` | date | Yes | Claim date |
| `extracted_data` | object | Yes | `ExtractedClaimData` payload |
| `bhs_matrix` | array | No | BHS matrix rows with `proc_code`, `mod1-mod4`, `pos_allowed`, `icd10` |
| `cpt_credentials` | array | No | CPT credential rows with `cpt_code` and `license` |
| `historical_claims` | array | No | Historical claim rows used by overlap, fraud, and travel checks |

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| `claim_id` | string | Claim identifier |
| `compliance_score` | number | Score from `0` to `100` |
| `score_band` | string | One of `Excellent`, `Good`, `Fair`, `Poor`, `Critical` |
| `passed_rules` | array | Rule IDs that passed |
| `failed_rules` | array | Rule IDs that failed |
| `flag_summary` | object | Counts for `high`, `medium`, `low` |
| `results` | array | Exactly 19 rule results |
| `results[].rule_id` | string | Rule identifier |
| `results[].rule_name` | string | Human-readable rule name |
| `results[].category` | string | Category label |
| `results[].priority` | string | `high`, `medium`, or `low` |
| `results[].status` | string | `pass` or `fail` |
| `results[].message` | string | Rule outcome message |
| `results[].red_flag_level` | string | `high`, `medium`, `low`, or `none` |
| `results[].detail` | object | Rule-specific detail |

### Success response example

```json
{
  "claim_id": "CLAIM-001",
  "compliance_score": 100.0,
  "score_band": "Excellent",
  "passed_rules": [
    "TP-001",
    "TP-002",
    "TP-003"
  ],
  "failed_rules": [],
  "flag_summary": {
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "results": [
    {
      "rule_id": "TP-001",
      "rule_name": "Treatment Plan Must Be Current",
      "category": "Treatment Plan",
      "priority": "high",
      "status": "pass",
      "message": "Treatment plan is current for the claim date.",
      "red_flag_level": "none",
      "detail": {
        "age_days": 28,
        "validity_days": 180
      }
    }
  ]
}
```

The actual success response always includes exactly 19 `results` entries.

### Error response example

```json
{
  "status": "error",
  "request_id": "req-validate-001",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed.",
  "details": {
    "path": "/api/v1/ai/validate",
    "errors": [
      {
        "loc": [
          "body",
          "extracted_data",
          "cpt_codes"
        ],
        "type": "value_error"
      }
    ]
  }
}
```

### curl example

```bash
curl -X POST http://127.0.0.1:8001/api/v1/ai/validate \
  -H "Content-Type: application/json" \
  --data @sample_data/sample_validate_request.json
```

### Backend usage note

Use this endpoint only when the backend already has structured extracted data and needs rule validation without rerunning OCR and extraction.

## POST /api/v1/ai/analyze-claim

### Purpose

Run the full AI pipeline:

1. OCR
2. Deterministic AI extraction
3. 19-rule validation
4. Compliance scoring
5. Final AI findings response

### Request type

`multipart/form-data`

### Request fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `claim_id` | string | Yes | Claim identifier |
| `provider_id` | string | Yes | Provider identifier |
| `patient_id` | string | Yes | Patient identifier |
| `claim_date` | date | Yes | Claim date |
| `treatment_plan_files` | file[] | Yes | At least one treatment plan document |
| `clinical_note_files` | file[] | Yes | At least one clinical note document |
| `dla20_files` | file[] | Yes | At least one DLA-20 document |
| `bhs_matrix_json` | string | Yes | JSON string containing a list of BHS matrix rows |
| `cpt_credentials_json` | string | Yes | JSON string containing a list of CPT credential rows |
| `historical_claims_json` | string | Yes | JSON string containing a list of historical claims; `[]` is valid |

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| `claim_id` | string | Claim identifier |
| `ai_status` | string | `validated` on success |
| `compliance_score` | number | Score from `0` to `100` |
| `score_band` | string | Score band |
| `ocr_summary` | object | OCR document counts |
| `extracted_data` | object | Structured extracted claim data |
| `flag_summary` | object | Counts for `high`, `medium`, `low` |
| `rule_results` | array | Exactly 19 rule results |
| `metadata` | object | Processing metadata with timing and counts |

### Success response example

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

Full sample response:

`sample_data/sample_analyze_claim_response.json`

### Error response example

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

### curl example

```bash
curl -X POST http://127.0.0.1:8001/api/v1/ai/analyze-claim \
  -F "claim_id=CLAIM-001" \
  -F "provider_id=PROV-001" \
  -F "patient_id=PAT-001" \
  -F "claim_date=2026-06-29" \
  -F "treatment_plan_files=@./path/to/treatment-plan.docx" \
  -F "clinical_note_files=@./path/to/clinical-note.docx" \
  -F "dla20_files=@./path/to/dla20.docx" \
  -F "bhs_matrix_json=$(tr -d '\n' < sample_data/sample_bhs_matrix.json)" \
  -F "cpt_credentials_json=$(tr -d '\n' < sample_data/sample_cpt_credentials.json)" \
  -F "historical_claims_json=$(tr -d '\n' < sample_data/sample_historical_claims.json)"
```

### Backend usage note

This is the primary integration endpoint for the backend team. The backend should send the claim files and master-data JSON here, then persist the returned AI output in its own database and expose the result to the frontend or downstream workflows.
