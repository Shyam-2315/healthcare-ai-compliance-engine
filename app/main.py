from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.ai_routes import router as ai_router
from app.api.schemas.common import ErrorResponse
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = get_settings()
    yield


settings = get_settings()

app = FastAPI(
    title="Healthcare Compliance AI Service",
    version="1.0.0",
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

app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    error = ErrorResponse(
        error="validation_error",
        message="Request validation failed.",
        details={"errors": exc.errors(), "path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error.model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred.",
        details={"path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}


def create_app() -> FastAPI:
    return app
