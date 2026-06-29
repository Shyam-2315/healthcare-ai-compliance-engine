from app.api.schemas.extraction_schema import ExtractionRequest, ExtractionResponse
from app.config import Settings
from app.services.ai.base import AIClient


class AzureOpenAIClient(AIClient):
    provider_name = "azure_openai"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        if not (
            self._settings.azure_openai_endpoint
            and self._settings.azure_openai_key
            and self._settings.azure_openai_deployment
        ):
            raise RuntimeError("Azure OpenAI settings are not configured.")
        raise NotImplementedError("Azure OpenAI provider is not implemented in this scaffold.")
