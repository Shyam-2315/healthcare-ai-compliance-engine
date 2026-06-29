from typing import Any

from pydantic import ConfigDict, Field

from app.api.schemas.common import APIModel
from app.api.schemas.extraction_schema import DocumentType


class OCRRequest(APIModel):
    document_type: DocumentType

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={"examples": [{"document_type": "clinical_notes"}]},
    )


class OCRResultResponse(APIModel):
    document_id: str
    document_type: DocumentType
    file_name: str
    raw_text: str
    page_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "document_id": "6f6bc9f9-6a4d-4211-8f7d-8bf15c2d7646",
                    "document_type": "clinical_notes",
                    "file_name": "clinical-note-2026-06-12.pdf",
                    "raw_text": "Claim ID: CLM-2026-00042\nCPT 90837\nDiagnosis F41.1",
                    "page_count": 2,
                    "confidence": 0.96,
                    "metadata": {"method": "pdfplumber", "provider": "local"},
                }
            ]
        },
    )


class OCRResponse(APIModel):
    document_type: DocumentType
    results: list[OCRResultResponse]

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "document_type": "clinical_notes",
                    "results": [
                        {
                            "document_id": "6f6bc9f9-6a4d-4211-8f7d-8bf15c2d7646",
                            "document_type": "clinical_notes",
                            "file_name": "clinical-note-2026-06-12.pdf",
                            "raw_text": "Claim ID: CLM-2026-00042",
                            "page_count": 1,
                            "confidence": 1.0,
                            "metadata": {"method": "python-docx", "provider": "local"},
                        }
                    ],
                }
            ]
        },
    )
