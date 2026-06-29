# Swagger Testing

## 1. Run service locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 2. Open Swagger

Open:

```text
http://127.0.0.1:8001/docs
```

## 3. Test /health

1. Expand `GET /api/v1/ai/health`
2. Click `Try it out`
3. Click `Execute`

Expected result:

- HTTP `200`
- body contains `status`, `service`, `version`, `environment`
- response header contains `X-Request-ID`

## 4. Test /ocr

1. Expand `POST /api/v1/ai/ocr`
2. Click `Try it out`
3. Set `document_type` to `clinical_notes`
4. Upload a supported `.docx`, `.pdf`, `.jpg`, `.jpeg`, or `.png` file
5. Click `Execute`

Expected result:

- HTTP `200`
- `document_type` echoes the request
- `results` array is returned
- each result includes `document_id`, `file_name`, `raw_text`, `page_count`, `confidence`, `metadata`

## 5. Test /extract

Use the contents of `sample_data/sample_extract_request.json`.

1. Expand `POST /api/v1/ai/extract`
2. Click `Try it out`
3. Paste the sample JSON into the request body
4. Click `Execute`

Expected result:

- HTTP `200`
- extracted response includes claim identifiers
- CPT code, modifier, ICD-10 code, dates, times, authorization number, treatment goals, and DLA-20 values are populated

## 6. Test /validate

Use the contents of `sample_data/sample_validate_request.json`.

1. Expand `POST /api/v1/ai/validate`
2. Click `Try it out`
3. Paste the sample JSON into the request body
4. Click `Execute`

Expected result:

- HTTP `200`
- response includes `compliance_score`
- response includes `score_band`
- response includes `flag_summary`
- `results` contains exactly 19 rule results

## 7. Test /analyze-claim

Prepare three local files:

- one treatment plan document
- one clinical note document
- one DLA-20 document

Then:

1. Expand `POST /api/v1/ai/analyze-claim`
2. Click `Try it out`
3. Enter:
   - `claim_id=CLAIM-001`
   - `provider_id=PROV-001`
   - `patient_id=PAT-001`
   - `claim_date=2026-06-29`
4. Upload the three document groups
5. Paste compact JSON strings from:
   - `sample_data/sample_bhs_matrix.json`
   - `sample_data/sample_cpt_credentials.json`
   - `sample_data/sample_historical_claims.json`
6. Click `Execute`

Expected result:

- HTTP `200`
- `ai_status` is `validated`
- `ocr_summary` is present
- `extracted_data` is present
- `rule_results` contains exactly 19 rows
- `metadata.processing_time_ms` is present

## 8. Expected output checklist

Use this checklist for manual verification:

- `GET /api/v1/ai/health` returns `200`
- `POST /api/v1/ai/ocr` returns OCR text and metadata
- `POST /api/v1/ai/extract` returns structured `ExtractedClaimData`
- `POST /api/v1/ai/validate` returns `compliance_score`, `score_band`, `flag_summary`, and 19 rules
- `POST /api/v1/ai/analyze-claim` returns `ai_status=validated`, extracted data, and 19 rules
- error responses use the standard shape with `status`, `request_id`, `error_code`, `message`, and `details`
