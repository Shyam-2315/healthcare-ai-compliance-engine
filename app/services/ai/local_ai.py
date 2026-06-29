import re
from datetime import date, datetime, time, timedelta
from typing import Any

from app.api.schemas.extraction_schema import ExtractedClaimData, OCRTextInput
from app.services.ai.base import AIFindingsServiceBase

DATE_PATTERNS = [
    r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    r"\b\d{1,2}-\d{1,2}-\d{4}\b",
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}\b",
]
DATE_FORMATS = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%B %d %Y", "%B %d, %Y"]
TIME_PATTERN = r"\b([01]?\d|2[0-3]):([0-5]\d)(?:\s*([AaPp][Mm]))?\b"
ICD10_PATTERN = re.compile(r"\b([A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?)\b")
CPT_PATTERN = re.compile(r"(?<!\d)(\d{5})(?:-([A-Z0-9]{2}))?(?!\d)", re.IGNORECASE)
SIGNATURE_KEYWORDS = [
    "signed by",
    "electronically signed",
    "signature:",
    "clinician signature",
    "provider signature",
    "therapist signature",
    "/s/",
    "e-signed",
    "digital signature",
]
DLA_AREAS = [
    "health practices",
    "housing stability",
    "communication",
    "safety",
    "managing money",
    "nutrition",
    "problem solving",
    "family relationships",
    "alcohol and drug use",
    "community resources",
    "personal hygiene",
    "productivity",
    "coping skills",
]


class LocalDeterministicAI(AIFindingsServiceBase):
    provider_name = "local"

    def extract(
        self,
        ocr_results: list[OCRTextInput],
        claim_context: dict[str, Any] | None = None,
    ) -> ExtractedClaimData:
        context = claim_context or {}
        texts_by_type = self._texts_by_type(ocr_results)
        all_text = "\n".join(item.raw_text for item in ocr_results)
        clinical_text = texts_by_type.get("clinical_notes", "")
        treatment_text = texts_by_type.get("treatment_plan", "")
        dla20_text = texts_by_type.get("dla20", "")

        session_start = self._extract_time(
            clinical_text,
            [r"(?:session\s+)?start(?:\s+time)?\s*[:\-]\s*(" + TIME_PATTERN + ")"],
        )
        session_end = self._extract_time(
            clinical_text,
            [r"(?:session\s+)?end(?:\s+time)?\s*[:\-]\s*(" + TIME_PATTERN + ")"],
        )
        range_start, range_end = self._extract_time_range(clinical_text)
        session_start = session_start or range_start
        session_end = session_end or range_end

        dla20_scores = self._extract_dla20_scores(dla20_text)

        return ExtractedClaimData(
            claim_id=self._string_context(context, "claim_id"),
            provider_id=self._string_context(context, "provider_id"),
            patient_id=self._string_context(context, "patient_id"),
            claim_date=self._date_context(context, "claim_date"),
            patient_name=self._first_labeled_value(
                all_text,
                [r"patient\s+name", r"client\s+name"],
            ),
            patient_dob=self._extract_labeled_date(
                all_text,
                [r"patient\s+dob", r"date\s+of\s+birth", r"dob"],
            ),
            provider_name=self._first_labeled_value(
                all_text,
                [r"provider\s+name", r"provider", r"clinic"],
            ),
            provider_license=self._first_labeled_value(
                all_text,
                [r"provider\s+license", r"license(?:\s+#|\s+number)?"],
            ),
            provider_npi=self._first_match(r"\b(?:provider\s+)?npi\s*[:#\-]?\s*(\d{10})\b", all_text),
            service_dates=self._extract_service_dates(clinical_text or all_text),
            session_start_time=session_start,
            session_end_time=session_end,
            session_duration_minutes=self._duration_minutes(session_start, session_end),
            service_location=self._first_labeled_value(
                all_text,
                [r"service\s+location", r"location", r"place\s+of\s+service\s+description"],
            ),
            cpt_codes=self._extract_cpt_codes(all_text),
            modifiers=self._extract_modifiers(all_text),
            place_of_service=self._first_match(
                r"\b(?:place\s+of\s+service|pos)\s*[:#\-]?\s*([0-9]{2})\b",
                all_text,
            ),
            diagnosis_codes=self._extract_diagnosis_codes(all_text),
            billed_units=self._extract_int(
                all_text,
                [r"\bbilled\s+units\s*[:#\-]?\s*(\d+)\b", r"\bunits\s*[:#\-]?\s*(\d+)\b"],
            ),
            treatment_plan_date=self._extract_labeled_date(
                treatment_text,
                [r"treatment\s+plan\s+date", r"plan\s+date"],
            ),
            authorization_number=self._first_match(
                r"\b(?:authorization\s*(?:#|number)?|auth)\s*[:#\-]?\s*([A-Za-z0-9-]+)\b",
                all_text,
            ),
            treatment_goals=self._extract_treatment_goals(treatment_text),
            clinical_narrative=self._extract_clinical_narrative(clinical_text),
            clinical_note_date=self._extract_labeled_date(
                clinical_text,
                [r"clinical\s+note\s+date", r"note\s+date", r"service\s+date"],
            ),
            provider_signature_present=self._has_provider_signature(clinical_text or all_text),
            dla20_deficiency_areas=self._extract_dla20_deficiency_areas(dla20_text, dla20_scores),
            dla20_scores=dla20_scores,
            dla20_total_score=self._extract_int(
                dla20_text,
                [r"\bdla[-\s]?20\s+total\s+score\s*[:#\-]?\s*(\d+)\b", r"\btotal\s+score\s*[:#\-]?\s*(\d+)\b"],
            ),
            treatment_plan_raw=treatment_text or None,
            clinical_notes_raw=clinical_text or None,
            dla20_raw=dla20_text or None,
        )

    @staticmethod
    def _texts_by_type(ocr_results: list[OCRTextInput]) -> dict[str, str]:
        grouped: dict[str, list[str]] = {}
        for item in ocr_results:
            grouped.setdefault(item.document_type, []).append(item.raw_text)
        return {key: "\n".join(values).strip() for key, values in grouped.items()}

    @staticmethod
    def _string_context(context: dict[str, Any], key: str) -> str | None:
        value = context.get(key)
        return str(value) if value not in (None, "") else None

    @classmethod
    def _date_context(cls, context: dict[str, Any], key: str) -> date | None:
        value = context.get(key)
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return cls._parse_date(value)
        return None

    @staticmethod
    def _first_match(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _first_labeled_value(text: str, labels: list[str]) -> str | None:
        for label in labels:
            pattern = rf"\b{label}\s*[:#\-]\s*([^\n\r;]+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                return re.sub(r"\s{2,}", " ", value)
        return None

    @classmethod
    def _extract_labeled_date(cls, text: str, labels: list[str]) -> date | None:
        for label in labels:
            match = re.search(
                rf"\b{label}\s*[:#\-]?\s*({cls._date_regex()})",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                return cls._parse_date(match.group(1))
        return None

    @classmethod
    def _extract_service_dates(cls, text: str) -> list[date]:
        dates: list[date] = []
        for match in re.finditer(
            rf"\b(?:service\s+date|date\s+of\s+service|dos)\s*[:#\-]?\s*({cls._date_regex()})",
            text,
            flags=re.IGNORECASE,
        ):
            parsed = cls._parse_date(match.group(1))
            if parsed and parsed not in dates:
                dates.append(parsed)
        return dates

    @classmethod
    def _date_regex(cls) -> str:
        return "|".join(f"(?:{pattern})" for pattern in DATE_PATTERNS)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        normalized = re.sub(r"\s+", " ", value.strip())
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(normalized, date_format).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_time(text: str, patterns: list[str]) -> time | None:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return LocalDeterministicAI._parse_time(match.group(1))
        return None

    @staticmethod
    def _extract_time_range(text: str) -> tuple[time | None, time | None]:
        match = re.search(
            rf"\b(?:session\s+time|time)\s*[:#\-]?\s*({TIME_PATTERN})\s*(?:-|to)\s*({TIME_PATTERN})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None, None
        return LocalDeterministicAI._parse_time(match.group(1)), LocalDeterministicAI._parse_time(match.group(5))

    @staticmethod
    def _parse_time(value: str) -> time | None:
        normalized = value.strip().upper().replace(" ", "")
        for time_format in ("%I:%M%p", "%H:%M"):
            try:
                return datetime.strptime(normalized, time_format).time()
            except ValueError:
                continue
        return None

    @staticmethod
    def _duration_minutes(start: time | None, end: time | None) -> int | None:
        if start is None or end is None:
            return None
        start_dt = datetime.combine(date(2000, 1, 1), start)
        end_dt = datetime.combine(date(2000, 1, 1), end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        return int((end_dt - start_dt).total_seconds() // 60)

    @staticmethod
    def _extract_cpt_codes(text: str) -> list[str]:
        codes: set[str] = set()
        for match in CPT_PATTERN.finditer(text):
            codes.add(match.group(1))
        return sorted(codes)

    @staticmethod
    def _extract_modifiers(text: str) -> list[str]:
        modifiers: set[str] = set()
        for match in CPT_PATTERN.finditer(text):
            if match.group(2):
                modifiers.add(match.group(2).upper())
        for match in re.finditer(r"\bmodifier(?:s)?\s*[:#\-]?\s*([A-Z0-9,\s-]+)", text, flags=re.IGNORECASE):
            for modifier in re.split(r"[\s,]+", match.group(1)):
                cleaned = modifier.strip().upper()
                if re.fullmatch(r"[A-Z0-9]{2}", cleaned):
                    modifiers.add(cleaned)
        return sorted(modifiers)

    @staticmethod
    def _extract_diagnosis_codes(text: str) -> list[str]:
        return sorted({match.group(1).upper() for match in ICD10_PATTERN.finditer(text)})

    @staticmethod
    def _extract_int(text: str, patterns: list[str]) -> int | None:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _extract_treatment_goals(text: str) -> list[str]:
        goals: list[str] = []
        in_goal_block = False
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                in_goal_block = False
                continue
            header_match = re.match(r"^(?:treatment\s+)?goals?\s*[:\-]\s*(.*)$", stripped, flags=re.IGNORECASE)
            bullet_match = re.match(r"^(?:goal\s*\d+|[-*•])\s*[:.\-]?\s*(.+)$", stripped, flags=re.IGNORECASE)
            if header_match:
                in_goal_block = True
                remainder = header_match.group(1).strip()
                if remainder:
                    goals.append(remainder)
                continue
            if bullet_match:
                goals.append(bullet_match.group(1).strip())
                continue
            if in_goal_block:
                goals.append(stripped)
        return goals

    @staticmethod
    def _extract_clinical_narrative(text: str) -> str | None:
        value = LocalDeterministicAI._first_labeled_value(
            text,
            [r"clinical\s+narrative", r"narrative", r"progress\s+note"],
        )
        if value:
            return value
        return text.strip() or None

    @staticmethod
    def _has_provider_signature(text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in SIGNATURE_KEYWORDS)

    @staticmethod
    def _extract_dla20_scores(text: str) -> dict[str, int]:
        scores: dict[str, int] = {}
        for area in DLA_AREAS:
            pattern = rf"\b{re.escape(area)}\b\s*[:\-]?\s*(?:score\s*)?([0-9]|10)\b"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                scores[area.replace(" ", "_")] = int(match.group(1))
        return scores

    @staticmethod
    def _extract_dla20_deficiency_areas(text: str, scores: dict[str, int]) -> list[str]:
        deficiencies = {area for area, score in scores.items() if score <= 3}
        for match in re.finditer(
            r"\bdeficien(?:cy|cies|t)\s+(?:area|areas)?\s*[:\-]\s*([^\n\r]+)",
            text,
            flags=re.IGNORECASE,
        ):
            for item in re.split(r"[,;]", match.group(1)):
                cleaned = item.strip().lower().replace(" ", "_")
                if cleaned:
                    deficiencies.add(cleaned)
        return sorted(deficiencies)


LocalAIClient = LocalDeterministicAI
