from app.config import get_settings
from app.services.ai.azure_openai import AzureOpenAIClient
from app.services.ai.base import AIClient
from app.services.ai.local_ai import LocalAIClient


def get_ai_client() -> AIClient:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "local":
        return LocalAIClient()
    if provider in {"azure", "azure_openai"}:
        return AzureOpenAIClient(settings)
    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")
