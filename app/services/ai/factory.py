from app.config import get_settings
from app.services.ai.azure_openai import AzureOpenAIService
from app.services.ai.base import AIFindingsServiceBase
from app.services.ai.local_ai import LocalDeterministicAI


def get_ai_service() -> AIFindingsServiceBase:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "azure_openai":
        return AzureOpenAIService(settings)
    return LocalDeterministicAI()


get_ai_client = get_ai_service
