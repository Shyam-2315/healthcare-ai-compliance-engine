# Backend Integration

## Primary integration path

The backend team should mainly integrate with:

```text
POST /api/v1/ai/analyze-claim
```

This endpoint runs the full pipeline in one request:

1. OCR
2. Field extraction
3. 19-rule validation
4. Compliance scoring
5. Final AI findings JSON

## Request payload expected from backend

The backend sends a `multipart/form-data` request containing:

- `claim_id`
- `provider_id`
- `patient_id`
- `claim_date`
- `treatment_plan_files`
- `clinical_note_files`
- `dla20_files`
- `bhs_matrix_json`
- `cpt_credentials_json`
- `historical_claims_json`

Important multipart note:

- `bhs_matrix_json`, `cpt_credentials_json`, and `historical_claims_json` must be serialized JSON strings, not nested multipart objects.
- `historical_claims_json` may be `[]` when no historical records are available.

## AI service response returned to backend

The AI service returns:

- `claim_id`
- `ai_status`
- `compliance_score`
- `score_band`
- `ocr_summary`
- `extracted_data`
- `flag_summary`
- `rule_results`
- `metadata`

`rule_results` always contains exactly 19 rows when the request succeeds.

## What backend should store

Suggested persistence targets in the backend system:

- `claims.ai_status`
- `claims.compliance_score`
- `claim_validations` rows derived from `rule_results`
- `extracted_data` if an audit trail is required
- processing metadata from `metadata` if operational analytics are needed

Suggested `claim_validations` row mapping:

- `claim_id`
- `rule_id`
- `rule_name`
- `category`
- `priority`
- `status`
- `message`
- `red_flag_level`
- `detail`

## AI Service Responsibilities

- OCR
- field extraction
- 19-rule validation
- scoring
- AI findings JSON

## Backend Responsibilities

- authentication
- user and organization management
- claim creation
- file storage
- database persistence
- calling the AI service
- saving the AI response
- frontend delivery

## Integration flow

1. Backend receives claim files and claim metadata from its own authenticated workflow.
2. Backend stores the raw uploaded files in its own storage layer.
3. Backend loads or assembles current BHS matrix, CPT credential mappings, and historical claims.
4. Backend sends the multipart request to `POST /api/v1/ai/analyze-claim`.
5. Backend stores the AI response in claim tables and validation tables.
6. Backend exposes compliance results to frontend or downstream workflows.

## Error handling guidance

The AI service returns standard JSON-safe error payloads:

```json
{
  "status": "error",
  "request_id": "req-123456",
  "error_code": "INVALID_MASTER_DATA",
  "message": "bhs_matrix_json must be valid JSON.",
  "details": {}
}
```

Recommended backend behavior:

- persist `request_id` for traceability
- retry only for infrastructure or timeout failures
- do not retry schema errors or missing-file errors without fixing the request
- surface `message` to internal operators, not directly as end-user business copy unless the backend wraps it

## Sample files

Use these repo files during backend integration:

- `sample_data/sample_bhs_matrix.json`
- `sample_data/sample_cpt_credentials.json`
- `sample_data/sample_historical_claims.json`
- `sample_data/sample_validate_request.json`
- `sample_data/sample_extract_request.json`
- `sample_data/sample_analyze_claim_response.json`

## No hidden dependencies

This AI service has:

- no database dependency
- no auth dependency
- no frontend dependency
- no claim storage dependency

The backend remains the system of record.
