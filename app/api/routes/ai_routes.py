from fastapi import APIRouter, UploadFile

from app.api.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse
from app.api.schemas.common import HealthResponse
from app.api.schemas.extraction_schema import ExtractionRequest, ExtractionResponse
from app.api.schemas.ocr_schema import OCRResponse
from app.api.schemas.validation_schema import ValidationRequest, ValidationResponse
from app.config import get_settings
from app.services.ai.factory import get_ai_client
from app.services.ocr.factory import get_ocr_client
from app.services.rule_engine.engine import ComplianceRuleEngine
from app.services.rule_engine.scoring import ComplianceScorer
from app.utils.file_utils import read_upload_file

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


@router.post("/ocr", response_model=OCRResponse, summary="Run OCR on an uploaded document")
async def run_ocr(file: UploadFile) -> OCRResponse:
    content = await read_upload_file(file)
    ocr_client = get_ocr_client()
    return await ocr_client.extract_text(content, filename=file.filename)


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extract structured claim details from text",
)
async def extract_claim(request: ExtractionRequest) -> ExtractionResponse:
    ai_client = get_ai_client()
    return await ai_client.extract(request)


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate extracted claim data against compliance rules",
)
async def validate_claim(request: ValidationRequest) -> ValidationResponse:
    engine = ComplianceRuleEngine()
    findings = engine.validate(request.claim, context=request.context)
    score = ComplianceScorer().score(findings)
    return ValidationResponse(findings=findings, score=score)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Run extraction, validation, and scoring for claim text",
)
async def analyze_claim(request: AnalyzeRequest) -> AnalyzeResponse:
    ai_client = get_ai_client()
    extraction = await ai_client.extract(
        ExtractionRequest(text=request.text, document_type=request.document_type)
    )
    validation = ValidationRequest(claim=extraction.extracted_fields, context=request.context)
    engine = ComplianceRuleEngine()
    findings = engine.validate(validation.claim, context=validation.context)
    score = ComplianceScorer().score(findings)
    return AnalyzeResponse(extraction=extraction, findings=findings, score=score)
