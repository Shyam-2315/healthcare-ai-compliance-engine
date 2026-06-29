from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from time import perf_counter
from typing import Any, Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.ai_routes import router as ai_router
from app.config import get_settings
from app.utils.exceptions import AppError
from app.utils.logging_utils import (
    REQUEST_ID_HEADER,
    configure_logging,
    get_logger,
    log_event,
    request_log_fields,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = get_settings()
    configure_logging(app.state.settings.log_level)
    yield


settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger()

app = FastAPI(
    title="Healthcare Compliance AI Service",
    version=settings.app_version,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "AI",
            "description": "OCR, AI extraction, validation, scoring, and findings endpoints.",
        }
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()

    log_event(
        logger,
        level=logging.INFO,
        message="request_started",
        **request_log_fields(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
        ),
    )

    response = await call_next(request)
    processing_time_ms = int((perf_counter() - started_at) * 1000)
    request.state.processing_time_ms = processing_time_ms
    response.headers[REQUEST_ID_HEADER] = request_id
    log_event(
        logger,
        level=logging.INFO,
        message="request_completed",
        **request_log_fields(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            processing_time_ms=processing_time_ms,
        ),
    )
    return response


app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    log_event(
        logger,
        level=logging.ERROR,
        message="app_error",
        **request_log_fields(
            request_id=_request_id(request),
            endpoint=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            processing_time_ms=getattr(request.state, "processing_time_ms", None),
            error_code=exc.error_code,
            error_type=type(exc).__name__,
        ),
    )
    return _build_error_response(
        request,
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = {"errors": _json_safe(exc.errors()), "path": request.url.path}
    log_event(
        logger,
        level=logging.ERROR,
        message="validation_error",
        **request_log_fields(
            request_id=_request_id(request),
            endpoint=request.url.path,
            method=request.method,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            processing_time_ms=getattr(request.state, "processing_time_ms", None),
            error_code="VALIDATION_ERROR",
            error_type=type(exc).__name__,
        ),
    )
    return _build_error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed.",
        details=details,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    details: dict[str, Any] = exc.detail if isinstance(exc.detail, dict) else {}
    log_event(
        logger,
        level=logging.ERROR,
        message="http_error",
        **request_log_fields(
            request_id=_request_id(request),
            endpoint=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            processing_time_ms=getattr(request.state, "processing_time_ms", None),
            error_code="HTTP_ERROR",
            error_type=type(exc).__name__,
        ),
    )
    return _build_error_response(
        request,
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
        message=message,
        details=_json_safe(details),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log_event(
        logger,
        level=logging.ERROR,
        message="unexpected_error",
        **request_log_fields(
            request_id=_request_id(request),
            endpoint=request.url.path,
            method=request.method,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            processing_time_ms=getattr(request.state, "processing_time_ms", None),
            error_code="INTERNAL_ERROR",
            error_type=type(exc).__name__,
        ),
    )
    return _build_error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
        details={},
    )


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}


def create_app() -> FastAPI:
    return app


def _build_error_response(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "request_id": _request_id(request),
            "error_code": error_code,
            "message": message,
            "details": _json_safe(details),
        },
    )
    response.headers[REQUEST_ID_HEADER] = _request_id(request)
    return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Exception):
        return str(value)
    return value
