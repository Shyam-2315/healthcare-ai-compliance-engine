import re
from typing import Any

from app.api.schemas.extraction_schema import (
    ExtractedClaimData,
    ExtractionRequest,
    ExtractionResponse,
)
from app.services.ai.base import AIClient


class LocalAIClient(AIClient):
    provider_name = "local"

    async def extract(self, request: ExtractionRequest) -> ExtractionResponse:
        text = request.text
        fields: dict[str, Any] = {
            "patient_id": self._first_match(r"\bpatient[_\s-]?id[:\s]+([A-Za-z0-9-]+)", text),
            "claim_id": self._first_match(r"\bclaim[_\s-]?id[:\s]+([A-Za-z0-9-]+)", text),
            "cpt_codes": sorted(set(re.findall(r"\b\d{5}\b", text))),
            "diagnosis_codes": sorted(
                set(re.findall(r"\b[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?\b", text))
            ),
        }
        fields = {key: value for key, value in fields.items() if value not in (None, [], "")}
        extracted_fields = ExtractedClaimData.model_validate(fields)
        return ExtractionResponse(
            document_type=request.document_type,
            extracted_fields=extracted_fields,
            confidence=0.65,
            provider=self.provider_name,
        )

    @staticmethod
    def _first_match(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1) if match else None
