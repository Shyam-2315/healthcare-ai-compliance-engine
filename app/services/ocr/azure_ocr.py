from app.config import Settings
from app.services.ocr.base import OCRResult, OCRServiceBase


class AzureOCRService(OCRServiceBase):
    provider_name = "azure"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def extract_text(self, file_path: str, document_type: str) -> OCRResult:
        if not (
            self._settings.azure_document_intelligence_endpoint
            and self._settings.azure_document_intelligence_key
        ):
            raise NotImplementedError(
                "Azure Document Intelligence OCR is not configured. "
                "Set azure_document_intelligence_endpoint and "
                "azure_document_intelligence_key before using OCR_PROVIDER=azure."
            )
        raise NotImplementedError(
            "Azure Document Intelligence OCR provider is not implemented yet."
        )


AzureOCRClient = AzureOCRService
