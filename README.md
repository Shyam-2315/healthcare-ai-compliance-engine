# healthcare-compliance-ai

## Project overview

`healthcare-compliance-ai` is a FastAPI microservice for healthcare compliance workflows. It provides OCR, deterministic AI extraction, 19-rule validation, compliance scoring, and an end-to-end analyze-claim pipeline for backend integration.

The service does not include a database, frontend, authentication, user management, organization management, or claim storage.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

Health check:

```text
http://127.0.0.1:8001/api/v1/ai/health
```

## Windows setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

If `make` is not available on Windows, run the Python commands directly or use Docker Desktop with `docker compose`.

## Tesseract setup note

Local OCR for images and scanned PDFs depends on `tesseract`. DOCX extraction does not require it, but image OCR and the scanned-PDF fallback do.

- Linux containers install `tesseract-ocr` in the Docker image.
- On Windows, install Tesseract OCR separately and ensure the `tesseract` executable is available on `PATH`.

## Docker setup

Build and start the service:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f ai-service
```

Stop the service:

```bash
docker compose down
```

The container listens on port `8001` and exposes the same Swagger and health URLs as the local setup.

## Swagger URL

```text
http://127.0.0.1:8001/docs
```

## API list

- `GET /api/v1/ai/health`
- `POST /api/v1/ai/ocr`
- `POST /api/v1/ai/extract`
- `POST /api/v1/ai/validate`
- `POST /api/v1/ai/analyze-claim`

## Testing commands

```bash
python -m pytest -q
python -m ruff check .
python -m mypy app
```

Or, with `make`:

```bash
make check
```

## Backend integration endpoint

The primary backend integration endpoint is:

```text
POST /api/v1/ai/analyze-claim
```

It accepts multipart claim documents plus master-data JSON, then runs OCR, AI extraction, rule validation, scoring, and returns the final AI findings payload.

## Backend Integration

Backend handoff documentation and sample payloads:

- [docs/API_CONTRACT.md](docs/API_CONTRACT.md)
- [docs/BACKEND_INTEGRATION.md](docs/BACKEND_INTEGRATION.md)
- [docs/SAMPLE_PAYLOADS.md](docs/SAMPLE_PAYLOADS.md)
- [docs/SWAGGER_TESTING.md](docs/SWAGGER_TESTING.md)

## Production Handover

Production handover and release references:

- [CHANGELOG.md](CHANGELOG.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md)
- [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md)
