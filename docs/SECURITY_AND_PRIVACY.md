# Security and Privacy

## Logging posture

The service is designed to avoid logging sensitive document content.

Confirmed controls:

- raw OCR text is not logged
- clinical narrative text is not logged
- PHI-bearing document bodies are not logged
- logs contain safe metadata only, such as request IDs, endpoint names, counts, timings, status codes, and error codes

## Error handling

The service uses standard JSON-safe error responses.

Properties:

- stack traces are not returned in API responses
- internal exceptions return a safe `INTERNAL_ERROR` message
- request IDs are included in error responses
- error responses use a stable shape: `status`, `request_id`, `error_code`, `message`, `details`

## Upload validation

Uploaded files are validated before OCR processing.

Controls:

- file extensions are restricted to supported OCR formats
- empty uploads are rejected
- file size is validated against configured limits
- invalid master-data JSON is rejected with clean `422` responses

## Temp file handling

The service uses temporary files only during request processing.

Controls:

- uploads are written to a temp directory only for active processing
- temp files are cleaned up on both success and failure paths
- OCR and analyze routes include cleanup in `finally` blocks

## Stateless service boundary

The service is stateless by design.

Properties:

- no database writes
- no claim storage
- no session storage
- no user state
- no organization state

All persistent storage responsibilities remain outside this service.

## Data retention posture

By design, the service does not retain processed claims after request completion.

Persistent data handling that must remain in the backend platform:

- source file storage
- database persistence
- audit retention
- user access controls

## Operational privacy notes

- run the service behind the backend platform or trusted network boundary
- limit CORS settings in non-local deployments
- treat logs as operational telemetry, not a source of claim content
- use request IDs for troubleshooting instead of logging document text
