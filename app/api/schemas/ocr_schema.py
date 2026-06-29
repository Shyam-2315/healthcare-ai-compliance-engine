from pydantic import Field

from app.api.schemas.common import APIModel


class OCRResponse(APIModel):
    filename: str | None = None
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    provider: str
