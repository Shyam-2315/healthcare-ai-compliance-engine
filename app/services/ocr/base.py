from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from app.api.schemas.common import APIModel
from app.utils import exceptions as app_exceptions

EmptyFileError = app_exceptions.EmptyFileError
OCRProcessingError = app_exceptions.OCRProcessingError
UnsupportedFileFormatError = app_exceptions.UnsupportedFileTypeError


class OCRServiceError(OCRProcessingError):
    """Compatibility base for OCR service failures."""


class OCRResult(APIModel):
    document_id: str
    document_type: str
    file_name: str
    raw_text: str
    page_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OCRServiceBase(ABC):
    provider_name: str

    @abstractmethod
    def extract_text(self, file_path: str, document_type: str) -> OCRResult:
        raise NotImplementedError

    def extract_batch(self, file_paths: list[str], document_type: str) -> list[OCRResult]:
        return [self.extract_text(file_path, document_type) for file_path in file_paths]


OCRClient = OCRServiceBase
