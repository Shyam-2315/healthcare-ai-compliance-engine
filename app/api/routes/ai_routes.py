from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse
from app.api.schemas.common import ErrorResponse, HealthResponse
from app.api.schemas.extraction_schema import (
    DocumentType,
    ExtractedClaimData,
    ExtractionRequest,
    ExtractionResponse,
    OCRTextInput,
)
from app.api.schemas.ocr_schema import OCRResponse, OCRResultResponse
from app.api.schemas.validation_schema import (
    ValidationFlagSummary,
    ValidationRequest,
    ValidationResponse,
    ValidationRuleResult,
)
from app.config import get_settings
from app.services.ai.factory import get_ai_service
from app.services.ocr.base import (
    EmptyFileError,
    OCRProcessingError,
    UnsupportedFileFormatError,
)
from app.services.ocr.factory import get_ocr_service
from app.services.ocr.local_ocr import SUPPORTED_OCR_EXTENSIONS
from app.services.rule_engine.engine import ComplianceRuleEngine, RuleEngine
from app.services.rule_engine.registry import get_all_rules
from app.services.rule_engine.scoring import ComplianceScorer
from app.utils.file_utils import cleanup_temp_file, save_upload_file_temp

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
        environment=settings.environment,
    )


@router.post("/ocr", response_model=OCRResponse, summary="Run OCR on uploaded documents")
async def run_ocr(
    document_type: Annotated[DocumentType, Form()],
    files: Annotated[list[UploadFile], File()],
) -> OCRResponse | JSONResponse:
    temp_paths: list[str] = []
    try:
        for file in files:
            temp_paths.append(await save_upload_file_temp(file, SUPPORTED_OCR_EXTENSIONS))

        ocr_service = get_ocr_service()
        results = ocr_service.extract_batch(temp_paths, document_type)
        response_results = [
            OCRResultResponse.model_validate(result.model_dump()) for result in results
        ]
        return OCRResponse(document_type=document_type, results=response_results)
    except UnsupportedFileFormatError as exc:
        return _error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="unsupported_file_format",
            message=str(exc),
        )
    except EmptyFileError as exc:
        return _error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="empty_file",
            message=str(exc),
        )
    except OCRProcessingError as exc:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="ocr_failure",
            message=str(exc),
        )
    finally:
        for temp_path in temp_paths:
            cleanup_temp_file(temp_path)


@router.post(
    "/extract",
    response_model=ExtractedClaimData,
    summary="Extract structured claim details from text",
)
async def extract_claim(request: ExtractionRequest) -> ExtractedClaimData:
    ai_service = get_ai_service()
    claim_context = {
        **request.claim_context,
        "claim_id": request.claim_id,
        "provider_id": request.provider_id,
        "patient_id": request.patient_id,
        "claim_date": request.claim_date,
    }
    return ai_service.extract(request.ocr_results, claim_context=claim_context)


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Run the full 19-rule compliance engine on extracted claim data",
)
async def validate_claim(request: ValidationRequest) -> ValidationResponse:
    extracted_data = request.extracted_data.model_dump(exclude_none=True)
    extracted_data.setdefault("claim_id", request.claim_id)
    extracted_data.setdefault("provider_id", request.provider_id)
    extracted_data.setdefault("patient_id", request.patient_id)
    extracted_data.setdefault("claim_date", request.claim_date)

    engine = RuleEngine(get_all_rules())
    output = engine.run(
        extracted_data,
        {"rows": [entry.model_dump(exclude_none=True) for entry in request.bhs_matrix]},
        {
            "cpt_credentials": [
                entry.model_dump(exclude_none=True) for entry in request.cpt_credentials
            ]
        },
        request.historical_claims,
    )

    results = [
        ValidationRuleResult(
            rule_id=result.rule_id,
            rule_name=result.rule_name,
            category=_format_category(result.category),
            priority=result.priority,
            status=result.status,
            message=result.message,
            red_flag_level=result.red_flag_level,
            detail=result.detail,
        )
        for result in output.results
    ]

    return ValidationResponse(
        claim_id=request.claim_id,
        compliance_score=output.compliance_score,
        score_band=output.score_band,
        passed_rules=[result.rule_id for result in output.passed_rules],
        failed_rules=[result.rule_id for result in output.failed_rules],
        flag_summary=ValidationFlagSummary(
            high=output.high_red_flags,
            medium=output.medium_red_flags,
            low=output.low_red_flags,
        ),
        results=results,
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Run extraction, validation, and scoring for claim text",
)
async def analyze_claim(request: AnalyzeRequest) -> AnalyzeResponse:
    ai_service = get_ai_service()
    extracted_fields = ai_service.extract(
        [OCRTextInput(document_type=request.document_type, raw_text=request.text)],
        claim_context=request.context,
    )
    extraction = ExtractionResponse(
        document_type=request.document_type,
        extracted_fields=extracted_fields,
        confidence=1.0,
        provider=ai_service.provider_name,
    )
    engine = ComplianceRuleEngine()
    findings = engine.validate(
        extraction.extracted_fields.model_dump(exclude_none=True),
        context=request.context,
    )
    score = ComplianceScorer().score(findings)
    return AnalyzeResponse(extraction=extraction, findings=findings, score=score)


def _error_response(*, status_code: int, error: str, message: str) -> JSONResponse:
    payload = ErrorResponse(error=error, message=message)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _format_category(value: str) -> str:
    return value.replace("_", " ").title()
