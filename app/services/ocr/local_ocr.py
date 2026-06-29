from app.api.schemas.ocr_schema import OCRResponse
from app.services.ocr.base import OCRClient


class LocalOCRClient(OCRClient):
    provider_name = "local"

    async def extract_text(self, content: bytes, filename: str | None = None) -> OCRResponse:
        text = content.decode("utf-8", errors="ignore").strip()
        return OCRResponse(
            filename=filename,
            text=text,
            confidence=0.80 if text else 0.0,
            provider=self.provider_name,
        )
