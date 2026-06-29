from app.config import get_settings
from app.services.ocr.azure_ocr import AzureOCRService
from app.services.ocr.base import OCRServiceBase
from app.services.ocr.local_ocr import LocalOCRService


def get_ocr_service() -> OCRServiceBase:
    settings = get_settings()
    provider = settings.ocr_provider.lower()
    if provider == "azure":
        return AzureOCRService(settings)
    return LocalOCRService()


get_ocr_client = get_ocr_service
