from __future__ import annotations

import importlib
import io
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.ocr.base import (
    EmptyFileError,
    OCRProcessingError,
    OCRResult,
    OCRServiceBase,
    UnsupportedFileFormatError,
)
from app.utils.file_utils import validate_file_extension

SUPPORTED_OCR_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}


class LocalOCRService(OCRServiceBase):
    provider_name = "local"

    def extract_text(self, file_path: str, document_type: str) -> OCRResult:
        path = Path(file_path)
        validate_file_extension(path.name, SUPPORTED_OCR_EXTENSIONS)
        if not path.exists() or path.stat().st_size == 0:
            raise EmptyFileError("Uploaded file is empty.")

        extension = path.suffix.lower()
        try:
            if extension == ".pdf":
                return self._extract_pdf(path, document_type)
            if extension == ".docx":
                return self._extract_docx(path, document_type)
            if extension in {".jpg", ".jpeg", ".png"}:
                return self._extract_image(path, document_type)
        except (EmptyFileError, UnsupportedFileFormatError):
            raise
        except Exception as exc:
            raise OCRProcessingError(f"OCR failed for {path.name}: {exc}") from exc

        raise UnsupportedFileFormatError(f"Unsupported file extension: {extension}")

    def _extract_pdf(self, path: Path, document_type: str) -> OCRResult:
        pdfplumber = self._load_dependency("pdfplumber")
        raw_text_parts: list[str] = []
        page_count = 0

        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                raw_text_parts.append(page.extract_text() or "")

        raw_text = "\n".join(part for part in raw_text_parts if part).strip()
        method = "pdfplumber"
        confidence = 1.0 if raw_text else 0.0

        if len(raw_text) < 50:
            fallback_text, fallback_confidence, fallback_pages = self._extract_pdf_with_tesseract(path)
            raw_text = fallback_text
            confidence = fallback_confidence
            page_count = fallback_pages or page_count
            method = "pdfplumber+tesseract"

        return self._build_result(
            document_type=document_type,
            path=path,
            raw_text=raw_text,
            page_count=page_count,
            confidence=confidence,
            metadata={"method": method, "provider": self.provider_name},
        )

    def _extract_pdf_with_tesseract(self, path: Path) -> tuple[str, float, int]:
        fitz = self._load_dependency("fitz")
        image_module = self._load_dependency("PIL.Image")
        pytesseract = self._load_dependency("pytesseract")

        raw_text_parts: list[str] = []
        confidences: list[float] = []
        page_count = 0

        with fitz.open(path) as document:
            page_count = len(document)
            for page in document:
                pixmap = page.get_pixmap(dpi=200)
                image = image_module.open(io.BytesIO(pixmap.tobytes("png")))
                raw_text_parts.append(str(pytesseract.image_to_string(image)).strip())
                confidences.extend(self._image_confidences(pytesseract, image))

        return "\n".join(part for part in raw_text_parts if part).strip(), self._average(confidences), page_count

    def _extract_docx(self, path: Path, document_type: str) -> OCRResult:
        docx = self._load_dependency("docx")
        document = docx.Document(path)
        text_parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text]

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    text_parts.append("\t".join(cells))

        return self._build_result(
            document_type=document_type,
            path=path,
            raw_text="\n".join(text_parts).strip(),
            page_count=1,
            confidence=1.0,
            metadata={"method": "python-docx", "provider": self.provider_name},
        )

    def _extract_image(self, path: Path, document_type: str) -> OCRResult:
        image_module = self._load_dependency("PIL.Image")
        pytesseract = self._load_dependency("pytesseract")

        with image_module.open(path) as image:
            raw_text = str(pytesseract.image_to_string(image)).strip()
            confidence = self._average(self._image_confidences(pytesseract, image))

        return self._build_result(
            document_type=document_type,
            path=path,
            raw_text=raw_text,
            page_count=1,
            confidence=confidence,
            metadata={"method": "tesseract", "provider": self.provider_name},
        )

    def _build_result(
        self,
        *,
        document_type: str,
        path: Path,
        raw_text: str,
        page_count: int,
        confidence: float,
        metadata: dict[str, Any],
    ) -> OCRResult:
        return OCRResult(
            document_id=str(uuid4()),
            document_type=document_type,
            file_name=path.name,
            raw_text=raw_text,
            page_count=page_count,
            confidence=confidence,
            metadata=metadata,
        )

    @staticmethod
    def _image_confidences(pytesseract: Any, image: Any) -> list[float]:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences: list[float] = []
        for value in data.get("conf", []):
            try:
                confidence = float(value)
            except (TypeError, ValueError):
                continue
            if confidence >= 0:
                confidences.append(min(confidence / 100.0, 1.0))
        return confidences

    @staticmethod
    def _average(values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _load_dependency(module_name: str) -> Any:
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            raise OCRProcessingError(
                f"OCR dependency '{module_name}' is not installed."
            ) from exc


LocalOCRClient = LocalOCRService
