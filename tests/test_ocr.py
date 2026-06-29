from pathlib import Path

import pytest

from app.services.ocr.base import OCRServiceBase, UnsupportedFileFormatError
from app.services.ocr.factory import get_ocr_service
from app.services.ocr.local_ocr import LocalOCRService, SUPPORTED_OCR_EXTENSIONS
from app.utils.file_utils import validate_file_extension


def test_validate_file_extension_rejects_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFileFormatError, match="Unsupported file extension"):
        validate_file_extension("claim.txt", SUPPORTED_OCR_EXTENSIONS)


def test_ocr_service_base_is_abstract() -> None:
    with pytest.raises(TypeError):
        OCRServiceBase()


def test_ocr_factory_returns_local_service_by_default() -> None:
    service = get_ocr_service()

    assert isinstance(service, LocalOCRService)


def test_docx_extraction_with_generated_document(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")
    docx_path = tmp_path / "clinical-note.docx"
    document = docx.Document()
    document.add_paragraph("Claim ID: CLM-2026-00042")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "CPT"
    table.rows[0].cells[1].text = "90837"
    document.save(docx_path)

    result = LocalOCRService().extract_text(str(docx_path), "clinical_notes")

    assert result.document_type == "clinical_notes"
    assert result.file_name == "clinical-note.docx"
    assert "Claim ID: CLM-2026-00042" in result.raw_text
    assert "90837" in result.raw_text
    assert result.page_count == 1
    assert result.confidence == 1.0
    assert result.metadata["method"] == "python-docx"
