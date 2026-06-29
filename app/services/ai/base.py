from abc import ABC, abstractmethod
from typing import Any

from app.api.schemas.extraction_schema import ExtractedClaimData, OCRTextInput


class AIFindingsServiceBase(ABC):
    provider_name: str

    @abstractmethod
    def extract(
        self,
        ocr_results: list[OCRTextInput],
        claim_context: dict[str, Any] | None = None,
    ) -> ExtractedClaimData:
        raise NotImplementedError


AIClient = AIFindingsServiceBase
