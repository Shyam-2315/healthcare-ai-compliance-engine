from typing import Any

from fastapi import status


class AppError(Exception):
    error_code = "APP_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code


class OCRProcessingError(AppError):
    error_code = "OCR_FAILED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AIExtractionError(AppError):
    error_code = "AI_EXTRACTION_FAILED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class RuleValidationError(AppError):
    error_code = "RULE_VALIDATION_FAILED"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class InvalidMasterDataError(AppError):
    error_code = "INVALID_MASTER_DATA"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class UnsupportedFileTypeError(AppError):
    error_code = "UNSUPPORTED_FILE_TYPE"
    status_code = status.HTTP_400_BAD_REQUEST


class EmptyFileError(AppError):
    error_code = "EMPTY_FILE"
    status_code = status.HTTP_400_BAD_REQUEST


class MissingRequiredFilesError(AppError):
    error_code = "MISSING_REQUIRED_FILES"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class FileTooLargeError(AppError):
    error_code = "FILE_TOO_LARGE"
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


UnsupportedFileFormatError = UnsupportedFileTypeError
