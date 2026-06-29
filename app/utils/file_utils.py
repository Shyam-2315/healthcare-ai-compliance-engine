from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from fastapi import HTTPException, UploadFile, status

from app.services.ocr.base import EmptyFileError, UnsupportedFileFormatError


async def read_upload_file(file: UploadFile, max_size_bytes: int = 10 * 1024 * 1024) -> bytes:
    content = await file.read()
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size.",
        )
    return content


def validate_file_extension(file_name: str, allowed_extensions: Iterable[str]) -> str:
    extension = Path(file_name).suffix.lower()
    normalized_extensions = {item.lower() for item in allowed_extensions}
    if extension not in normalized_extensions:
        allowed = ", ".join(sorted(normalized_extensions))
        raise UnsupportedFileFormatError(
            f"Unsupported file extension '{extension or '<none>'}'. Supported extensions: {allowed}."
        )
    return extension


async def save_upload_file_temp(
    file: UploadFile,
    allowed_extensions: Iterable[str],
    max_size_bytes: int = 10 * 1024 * 1024,
) -> str:
    validate_file_extension(file.filename or "", allowed_extensions)
    content = await file.read()
    if not content:
        raise EmptyFileError("Uploaded file is empty.")
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the maximum allowed size.",
        )

    suffix = Path(file.filename or "").suffix.lower()
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        return temp_file.name


def cleanup_temp_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
