# Changelog

## 1.0.0

### Phase 1: Schemas and API contracts

- added production-ready Pydantic schemas for OCR, extraction, validation, analyze, health, and error responses
- added schema validation for CPT codes, ICD-10 codes, compliance score bounds, claim dates, and document types
- added Swagger examples through model configuration

### Phase 2: Typing hardening

- fixed `mypy` issues in compliance scoring and extraction response typing
- introduced typed `RiskLevel` handling for compliance scoring
- ensured extraction responses use `ExtractedClaimData` instead of loose dictionaries

### Phase 3: OCR layer

- implemented stateless OCR abstractions and local OCR service
- added PDF, DOCX, and image OCR support
- added OCR factory, file utilities, OCR route, and OCR tests

### Phase 4: Deterministic AI extraction

- implemented local deterministic extraction from OCR text to `ExtractedClaimData`
- added extraction heuristics for patient, provider, coding, treatment plan, clinical note, and DLA-20 fields
- added extraction API and extraction coverage tests

### Phase 5: Rule engine core

- implemented rule base types, scoring engine, registry helpers, and time/date utilities
- added stable rule execution, crash isolation, score bands, and risk levels
- added core scoring and rule engine tests

### Phase 6: Compliance rules

- implemented all 19 production compliance validation rules
- registered rules in stable order with uniqueness and count validation
- added full rule pass/fail coverage and registry tests

### Phase 7: Validation API

- added `POST /api/v1/ai/validate`
- enforced 19-rule response shape and clean validation responses
- added validation API tests

### Phase 8: Analyze-claim pipeline

- added `POST /api/v1/ai/analyze-claim`
- wired OCR, extraction, validation, scoring, and final AI findings response
- added end-to-end analyze tests with generated DOCX inputs

### Phase 9: Error handling and observability

- added request ID middleware and structured logging
- added custom exception hierarchy and global safe error handlers
- hardened OCR and analyze routes, upload validation, and temp file cleanup
- added error-handling and observability tests

### Phase 10: Docker and deployment readiness

- added Dockerfile, docker-compose, Makefile, `.dockerignore`, and deployment configuration
- documented local and container runtime setup
- aligned environment handling for deployment use

### Phase 11: Backend integration package

- added API contract documentation and backend integration handoff docs
- added Swagger testing guide and realistic sample payload files
- updated README to point backend teams to the integration package

### Phase 12: Final production hardening

- added production readiness documentation and security/privacy notes
- added release checklist and production contract tests
- completed final handover validation for tests, lint, typing, and compose configuration
