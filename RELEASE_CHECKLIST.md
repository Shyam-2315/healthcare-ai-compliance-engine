# Release Checklist

## Validation

- [ ] `python -m pytest -q` passes
- [ ] `python -m ruff check .` passes
- [ ] `python -m mypy app` passes
- [ ] `docker compose config` passes

## Container and startup

- [ ] `docker compose up --build` works
- [ ] container reaches healthy state
- [ ] `GET /api/v1/ai/health` returns `200`
- [ ] Swagger opens at `/docs`

## API verification

- [ ] `POST /api/v1/ai/ocr` tested with supported file type
- [ ] `POST /api/v1/ai/extract` tested with sample JSON
- [ ] `POST /api/v1/ai/validate` tested with sample JSON
- [ ] `POST /api/v1/ai/analyze-claim` tested end to end
- [ ] `/validate` verified to return exactly 19 rule results
- [ ] `/analyze-claim` verified to return exactly 19 `rule_results` on success
- [ ] `compliance_score` verified within `0-100`
- [ ] `score_band` verified present
- [ ] `flag_summary` verified present
- [ ] `metadata.processing_time_ms` verified present for `/analyze-claim`

## Rule engine checks

- [ ] `get_rule_count()` returns `19`
- [ ] `validate_rule_registry()` returns `true`
- [ ] rule IDs verified unique
- [ ] total scoring weight verified as `106.0`
- [ ] crash isolation verified so rule execution continues after unexpected rule failure

## Security and privacy

- [ ] raw OCR text not logged
- [ ] clinical narrative not logged
- [ ] PHI not logged
- [ ] stack traces not exposed in API responses
- [ ] upload file extensions validated
- [ ] upload file size validated
- [ ] temp files cleaned up after processing
- [ ] service confirmed stateless

## Documentation handoff

- [ ] backend integration docs completed
- [ ] API contract docs completed
- [ ] Swagger testing guide completed
- [ ] production readiness doc completed
- [ ] security and privacy doc completed
- [ ] sample payload package completed
- [ ] changelog completed
