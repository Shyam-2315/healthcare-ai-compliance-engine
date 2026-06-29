from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel
from app.api.schemas.extraction_schema import DocumentType


class OCRRequest(APIModel):
    filename: str = Field(min_length=1)
    document_type: DocumentType
    content_type: str | None = None

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "filename": "clinical-note-2026-06-12.pdf",
                    "document_type": "clinical_notes",
                    "content_type": "application/pdf",
                }
            ]
        },
    )


class OCRResponse(APIModel):
    filename: str | None = None
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    provider: str

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "filename": "clinical-note-2026-06-12.pdf",
                    "text": "Claim ID: CLM-2026-00042\nCPT 90837\nDiagnosis F41.1",
                    "confidence": 0.96,
                    "provider": "azure_document_intelligence",
                }
            ]
        },
    )
