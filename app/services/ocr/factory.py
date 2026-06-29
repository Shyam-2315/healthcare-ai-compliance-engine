from app.config import get_settings
from app.services.ocr.azure_ocr import AzureOCRClient
from app.services.ocr.base import OCRClient
from app.services.ocr.local_ocr import LocalOCRClient


def get_ocr_client() -> OCRClient:
    settings = get_settings()
    provider = settings.ocr_provider.lower()
    if provider == "local":
        return LocalOCRClient()
    if provider == "azure":
        return AzureOCRClient(settings)
    raise ValueError(f"Unsupported OCR provider: {settings.ocr_provider}")
