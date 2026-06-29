from abc import ABC, abstractmethod

from app.api.schemas.ocr_schema import OCRResponse


class OCRClient(ABC):
    provider_name: str

    @abstractmethod
    async def extract_text(self, content: bytes, filename: str | None = None) -> OCRResponse:
        raise NotImplementedError
