from typing import Any

from app.api.schemas.extraction_schema import ExtractedClaimData, OCRTextInput
from app.config import Settings
from app.services.ai.base import AIFindingsServiceBase


class AzureOpenAIService(AIFindingsServiceBase):
    provider_name = "azure_openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def extract(
        self,
        ocr_results: list[OCRTextInput],
        claim_context: dict[str, Any] | None = None,
    ) -> ExtractedClaimData:
        if not (
            self._settings.azure_openai_endpoint
            and self._settings.azure_openai_key
            and self._settings.azure_openai_deployment
        ):
            raise NotImplementedError(
                "Azure OpenAI extraction is not configured. Set azure_openai_endpoint, "
                "azure_openai_key, and azure_openai_deployment before using "
                "AI_PROVIDER=azure_openai."
            )
        raise NotImplementedError("Azure OpenAI extraction provider is not implemented yet.")


AzureOpenAIClient = AzureOpenAIService
