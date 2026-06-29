import json
from datetime import date
from json import JSONDecodeError
from logging import INFO
from time import perf_counter
from typing import Annotated, Any, cast

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.api.schemas.analyze_schema import (
    AnalyzeClaimMetadata,
    AnalyzeClaimOCRSummary,
    AnalyzeClaimResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.api.schemas.common import HealthResponse
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
from app.services.ocr.factory import get_ocr_service
from app.services.ocr.local_ocr import SUPPORTED_OCR_EXTENSIONS
from app.services.rule_engine.engine import ComplianceRuleEngine, RuleEngine
from app.services.rule_engine.registry import get_all_rules
from app.services.rule_engine.scoring import ComplianceScorer
from app.utils.file_utils import cleanup_temp_files, save_upload_files_temp
from app.utils.exceptions import (
    AIExtractionError,
    AppError,
    InvalidMasterDataError,
    MissingRequiredFilesError,
    OCRProcessingError,
    RuleValidationError,
)
from app.utils.logging_utils import get_logger, log_event, request_log_fields

logger = get_logger("app.api.routes.ai")

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
    request: Request,
    document_type: Annotated[DocumentType, Form()],
    files: Annotated[list[UploadFile], File()],
) -> OCRResponse:
    started_at = perf_counter()
    temp_paths: list[str] = []
    log_event(
        logger,
        INFO,
        "ocr_started",
        **request_log_fields(
            request_id=request.state.request_id,
            endpoint=request.url.path,
            method=request.method,
            document_type=document_type,
            file_count=len(files),
        ),
    )
    try:
        temp_paths = await save_upload_files_temp(files, SUPPORTED_OCR_EXTENSIONS)
        ocr_service = get_ocr_service()
        try:
            results = ocr_service.extract_batch(temp_paths, document_type)
        except AppError:
            raise
        except Exception as exc:
            raise OCRProcessingError(
                "OCR processing failed.",
                details={"document_type": document_type, "file_count": len(files)},
            ) from exc
        response_results = [OCRResultResponse.model_validate(result.model_dump()) for result in results]
        processing_time_ms = int((perf_counter() - started_at) * 1000)
        log_event(
            logger,
            INFO,
            "ocr_completed",
            **request_log_fields(
                request_id=request.state.request_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=200,
                processing_time_ms=processing_time_ms,
                document_type=document_type,
                file_count=len(files),
            ),
        )
        return OCRResponse(document_type=document_type, results=response_results)
    finally:
        cleanup_temp_files(temp_paths)


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
    try:
        return ai_service.extract(request.ocr_results, claim_context=claim_context)
    except AppError:
        raise
    except Exception as exc:
        raise AIExtractionError("AI extraction failed.", details={"document_count": len(request.ocr_results)}) from exc


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
    if len(output.results) != 19:
        raise RuleValidationError(
            "Rule engine did not return the expected number of results.",
            details={"expected_results": 19, "actual_results": len(output.results)},
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
    "/analyze-claim",
    response_model=AnalyzeClaimResponse,
    summary="Run OCR, AI extraction, and full 19-rule validation on claim files",
)
async def analyze_claim_files(
    request: Request,
    claim_id: Annotated[str, Form()],
    provider_id: Annotated[str, Form()],
    patient_id: Annotated[str, Form()],
    claim_date: Annotated[date, Form()],
    treatment_plan_files: Annotated[list[UploadFile] | None, File()] = None,
    clinical_note_files: Annotated[list[UploadFile] | None, File()] = None,
    dla20_files: Annotated[list[UploadFile] | None, File()] = None,
    bhs_matrix_json: Annotated[str, Form()] = "[]",
    cpt_credentials_json: Annotated[str, Form()] = "[]",
    historical_claims_json: Annotated[str, Form()] = "[]",
) -> AnalyzeClaimResponse:
    started_at = perf_counter()
    temp_paths: list[str] = []
    log_event(
        logger,
        INFO,
        "analyze_claim_started",
        **request_log_fields(
            request_id=request.state.request_id,
            endpoint=request.url.path,
            method=request.method,
            claim_id=claim_id,
            treatment_plan_documents=len(treatment_plan_files or []),
            clinical_note_documents=len(clinical_note_files or []),
            dla20_documents=len(dla20_files or []),
        ),
    )
    _require_file_group(treatment_plan_files, "treatment_plan_files")
    _require_file_group(clinical_note_files, "clinical_note_files")
    _require_file_group(dla20_files, "dla20_files")

    try:
        treatment_plan_paths = await save_upload_files_temp(
            treatment_plan_files or [],
            SUPPORTED_OCR_EXTENSIONS,
        )
        clinical_note_paths = await save_upload_files_temp(
            clinical_note_files or [],
            SUPPORTED_OCR_EXTENSIONS,
        )
        dla20_paths = await save_upload_files_temp(
            dla20_files or [],
            SUPPORTED_OCR_EXTENSIONS,
        )
        temp_paths.extend(treatment_plan_paths)
        temp_paths.extend(clinical_note_paths)
        temp_paths.extend(dla20_paths)

        ocr_service = get_ocr_service()
        try:
            treatment_plan_results = ocr_service.extract_batch(treatment_plan_paths, "treatment_plan")
            clinical_note_results = ocr_service.extract_batch(clinical_note_paths, "clinical_notes")
            dla20_results = ocr_service.extract_batch(dla20_paths, "dla20")
        except AppError:
            raise
        except Exception as exc:
            raise OCRProcessingError(
                "OCR processing failed during claim analysis.",
                details={
                    "treatment_plan_documents": len(treatment_plan_paths),
                    "clinical_note_documents": len(clinical_note_paths),
                    "dla20_documents": len(dla20_paths),
                },
            ) from exc
        ocr_results = treatment_plan_results + clinical_note_results + dla20_results

        ai_service = get_ai_service()
        try:
            extracted_data = ai_service.extract(
                [
                    OCRTextInput(
                        document_type=cast(DocumentType, result.document_type),
                        raw_text=result.raw_text,
                    )
                    for result in ocr_results
                ],
                claim_context={
                    "claim_id": claim_id,
                    "provider_id": provider_id,
                    "patient_id": patient_id,
                    "claim_date": claim_date,
                },
            )
        except AppError:
            raise
        except Exception as exc:
            raise AIExtractionError(
                "AI extraction failed during claim analysis.",
                details={"ocr_documents_processed": len(ocr_results)},
            ) from exc
        extracted_data = extracted_data.model_copy(
            update={
                "claim_id": extracted_data.claim_id or claim_id,
                "provider_id": extracted_data.provider_id or provider_id,
                "patient_id": extracted_data.patient_id or patient_id,
                "claim_date": extracted_data.claim_date or claim_date,
            }
        )

        bhs_matrix = _parse_master_data_json(bhs_matrix_json, "bhs_matrix_json")
        cpt_credentials = _parse_master_data_json(cpt_credentials_json, "cpt_credentials_json")
        historical_claims = _parse_master_data_json(
            historical_claims_json,
            "historical_claims_json",
        )

        output = RuleEngine(get_all_rules()).run(
            extracted_data.model_dump(exclude_none=True),
            {"rows": bhs_matrix},
            {"cpt_credentials": cpt_credentials},
            historical_claims,
        )
        if len(output.results) != 19:
            raise RuleValidationError(
                "Rule engine did not return the expected number of results.",
                details={"expected_results": 19, "actual_results": len(output.results)},
            )

        processing_time_ms = int((perf_counter() - started_at) * 1000)
        log_event(
            logger,
            INFO,
            "analyze_claim_completed",
            **request_log_fields(
                request_id=request.state.request_id,
                endpoint=request.url.path,
                method=request.method,
                claim_id=claim_id,
                status_code=200,
                processing_time_ms=processing_time_ms,
                rules_executed=len(output.results),
                ocr_documents_processed=len(ocr_results),
                treatment_plan_documents=len(treatment_plan_results),
                clinical_note_documents=len(clinical_note_results),
                dla20_documents=len(dla20_results),
            ),
        )
        return AnalyzeClaimResponse(
            claim_id=claim_id,
            ai_status="validated",
            compliance_score=output.compliance_score,
            score_band=output.score_band,
            ocr_summary=AnalyzeClaimOCRSummary(
                total_documents=len(ocr_results),
                treatment_plan_documents=len(treatment_plan_results),
                clinical_note_documents=len(clinical_note_results),
                dla20_documents=len(dla20_results),
            ),
            extracted_data=extracted_data,
            flag_summary=ValidationFlagSummary(
                high=output.high_red_flags,
                medium=output.medium_red_flags,
                low=output.low_red_flags,
            ),
            rule_results=[
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
            ],
            metadata=AnalyzeClaimMetadata(
                processing_time_ms=processing_time_ms,
                rules_executed=len(output.results),
                ocr_documents_processed=len(ocr_results),
            ),
        )
    finally:
        cleanup_temp_files(temp_paths)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Run extraction, validation, and scoring for claim text",
)
async def analyze_claim(request: AnalyzeRequest) -> AnalyzeResponse:
    ai_service = get_ai_service()
    try:
        extracted_fields = ai_service.extract(
            [OCRTextInput(document_type=request.document_type, raw_text=request.text)],
            claim_context=request.context,
        )
    except AppError:
        raise
    except Exception as exc:
        raise AIExtractionError("AI extraction failed.", details={"document_type": request.document_type}) from exc
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


def _format_category(value: str) -> str:
    return value.replace("_", " ").title()


def _parse_master_data_json(value: str, field_name: str) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value)
    except JSONDecodeError as exc:
        raise InvalidMasterDataError(f"{field_name} must be valid JSON.") from exc

    if not isinstance(parsed, list) or any(not isinstance(item, dict) for item in parsed):
        raise InvalidMasterDataError(f"{field_name} must parse into a list of objects.")
    return parsed


def _require_file_group(files: list[UploadFile] | None, field_name: str) -> None:
    if not files:
        raise MissingRequiredFilesError(
            f"At least one file is required for {field_name}.",
            details={"field": field_name},
        )
