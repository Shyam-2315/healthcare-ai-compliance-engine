from typing import Any

from pydantic import Field

from app.api.schemas.common import APIModel


class ExtractionRequest(APIModel):
    text: str = Field(min_length=1)
    document_type: str = "claim"


class ExtractionResponse(APIModel):
    document_type: str
    extracted_fields: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    provider: str
