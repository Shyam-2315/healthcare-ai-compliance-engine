# Deployment

## Local run steps

1. Create a virtual environment and install dependencies.
2. Copy `.env.example` to `.env` and adjust values for the target environment.
3. Start the API on port `8001`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Docker run steps

Build and start the containerized service:

```bash
docker compose up -d --build
```

Check the resolved configuration:

```bash
docker compose config
```

Follow logs:

```bash
docker compose logs -f ai-service
```

Stop the service:

```bash
docker compose down
```

## Environment variables

Core runtime variables:

- `SERVICE_NAME=healthcare-compliance-ai`
- `APP_VERSION=1.0.0`
- `ENVIRONMENT=local`
- `LOG_LEVEL=INFO`
- `OCR_PROVIDER=local`
- `AI_PROVIDER=local`
- `TEMP_UPLOAD_DIR=/tmp/healthcare-compliance-ai`
- `MAX_UPLOAD_SIZE_MB=25`
- `REQUEST_TIMEOUT_SECONDS=120`
- `CORS_ORIGINS=*`
- `HOST=0.0.0.0`
- `PORT=8001`

Optional Azure placeholders remain available for future provider wiring:

- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
- `AZURE_DOCUMENT_INTELLIGENCE_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_KEY`
- `AZURE_OPENAI_DEPLOYMENT`

## Health check

Use the health endpoint for container probes and backend readiness checks:

```text
GET /api/v1/ai/health
```

Default local URL:

```text
http://127.0.0.1:8001/api/v1/ai/health
```

The Docker image also includes a built-in container health check against this endpoint.

## Logs

The service emits structured JSON logs with request IDs, endpoint metadata, status codes, timings, and safe error codes. Raw OCR text, clinical narrative text, and other sensitive payload content are intentionally excluded from logs.

## Production notes

- The service has no database dependency.
- The service has no authentication dependency.
- Run it behind your existing API gateway, reverse proxy, or backend platform ingress.
- Mount or provision writable storage for `TEMP_UPLOAD_DIR`.
- Tune `CORS_ORIGINS` for non-local environments instead of leaving `*`.
- Local OCR requires Tesseract and related native libraries; the provided Dockerfile installs them.

## Backend integration notes

The recommended integration path for backend teams is `POST /api/v1/ai/analyze-claim`.

That endpoint accepts:

- Claim identifiers and claim date
- Treatment plan files
- Clinical note files
- DLA-20 files
- Master-data JSON for BHS matrix, CPT credentials, and historical claims

The response returns OCR summary, extracted structured claim data, all 19 rule results, compliance score, score band, and processing metadata in a single call.
