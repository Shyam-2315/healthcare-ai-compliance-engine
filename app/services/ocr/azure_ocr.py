from app.api.schemas.ocr_schema import OCRResponse
from app.config import Settings
from app.services.ocr.base import OCRClient


class AzureOCRClient(OCRClient):
    provider_name = "azure"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def extract_text(self, content: bytes, filename: str | None = None) -> OCRResponse:
        if not (
            self._settings.azure_document_intelligence_endpoint
            and self._settings.azure_document_intelligence_key
        ):
            raise RuntimeError("Azure Document Intelligence settings are not configured.")
        raise NotImplementedError("Azure OCR provider is not implemented in this scaffold.")
