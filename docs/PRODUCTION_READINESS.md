# Production Readiness

## Production-ready scope

The microservice is production-ready for the following responsibilities:

- OCR for supported healthcare compliance documents
- deterministic extraction into structured claim fields
- execution of 19 compliance validation rules
- compliance scoring and score band output
- end-to-end processing through `POST /api/v1/ai/analyze-claim`
- structured logging, request IDs, standard error responses, and container deployment support

## Not included by design

The following concerns are intentionally outside this service boundary:

- database persistence
- frontend delivery
- authentication
- user management
- organization management
- claim storage

These concerns remain the responsibility of the backend platform.

## Deployment requirements

- Python 3.11 runtime or the provided Docker image
- Tesseract OCR and native OCR dependencies for local/scanned document support
- writable temp directory for upload processing
- environment configuration through `.env` or deployment platform variables
- network path from backend service to the AI service

Containerized deployment is supported through:

- `Dockerfile`
- `docker-compose.yml`
- `Makefile`

## Backend integration path

Primary backend integration endpoint:

```text
POST /api/v1/ai/analyze-claim
```

Recommended backend flow:

1. Backend receives claim documents and authenticated business metadata.
2. Backend stores source files in its own storage layer.
3. Backend builds `bhs_matrix_json`, `cpt_credentials_json`, and `historical_claims_json`.
4. Backend calls `POST /api/v1/ai/analyze-claim`.
5. Backend persists `ai_status`, `compliance_score`, `rule_results`, `extracted_data`, and metadata as needed.

## Operational checks

Before production handoff or release, verify:

- service starts cleanly
- health endpoint returns `200`
- Swagger is reachable
- OCR works for expected file types
- extraction returns expected structured fields
- validation returns 19 results
- analyze-claim returns 19 `rule_results`, score band, flag summary, and processing metadata
- logs contain safe metadata only
- temp files are cleaned up

## Stability guarantees

The production contract currently guarantees:

- stable response keys for `/health`, `/ocr`, `/extract`, `/validate`, and `/analyze-claim`
- `/validate` returns exactly 19 rule results
- `/analyze-claim` returns exactly 19 `rule_results` when successful
- `compliance_score` stays within `0-100`
- `score_band` is always present on validation and analyze success responses
- `flag_summary` is always present on validation and analyze success responses

## Evidence of readiness

Production-readiness evidence currently includes:

- automated tests
- `ruff` lint validation
- `mypy` type validation
- compose configuration validation
- deployment and backend integration documentation
