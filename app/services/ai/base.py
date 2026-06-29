from abc import ABC, abstractmethod

from app.api.schemas.extraction_schema import ExtractionRequest, ExtractionResponse


class AIClient(ABC):
    provider_name: str

    @abstractmethod
    async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        raise NotImplementedError
