from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from fastapi import UploadFile

from app.config import get_settings
from app.utils.exceptions import AppError, EmptyFileError, FileTooLargeError, UnsupportedFileTypeError


async def read_upload_file(file: UploadFile, max_size_bytes: int | None = None) -> bytes:
    settings = get_settings()
    max_bytes = max_size_bytes or settings.max_upload_size_bytes
    content = await file.read()
    if len(content) > max_bytes:
        raise FileTooLargeError(
            "Uploaded file exceeds the maximum allowed size.",
            details={"max_upload_size_mb": settings.max_upload_size_mb},
        )
    return content


def validate_file_extension(file_name: str, allowed_extensions: Iterable[str]) -> str:
    extension = Path(file_name).suffix.lower()
    normalized_extensions = {item.lower() for item in allowed_extensions}
    if extension not in normalized_extensions:
        allowed = ", ".join(sorted(normalized_extensions))
        raise UnsupportedFileTypeError(
            f"Unsupported file extension '{extension or '<none>'}'. Supported extensions: {allowed}."
        )
    return extension


async def save_upload_file_temp(
    file: UploadFile,
    allowed_extensions: Iterable[str],
    max_size_bytes: int | None = None,
) -> str:
    settings = get_settings()
    max_bytes = max_size_bytes or settings.max_upload_size_bytes
    validate_file_extension(file.filename or "", allowed_extensions)
    content = await file.read()
    if not content:
        raise EmptyFileError("Uploaded file is empty.")
    if len(content) > max_bytes:
        raise FileTooLargeError(
            "Uploaded file exceeds the maximum allowed size.",
            details={"max_upload_size_mb": settings.max_upload_size_mb},
        )

    temp_dir = settings.temp_upload_path
    temp_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix.lower()
    with NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as temp_file:
        temp_file.write(content)
        return temp_file.name


async def save_upload_files_temp(
    files: list[UploadFile],
    allowed_extensions: Iterable[str],
    max_size_bytes: int | None = None,
) -> list[str]:
    temp_paths: list[str] = []
    try:
        for file in files:
            temp_paths.append(
                await save_upload_file_temp(
                    file,
                    allowed_extensions,
                    max_size_bytes=max_size_bytes,
                )
            )
    except AppError:
        cleanup_temp_files(temp_paths)
        raise
    return temp_paths


def cleanup_temp_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()


def cleanup_temp_files(file_paths: Iterable[str]) -> None:
    for file_path in file_paths:
        cleanup_temp_file(file_path)
