"""Custom exception hierarchy and global FastAPI exception handlers."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api.schemas.common import APIResponse

logger = structlog.get_logger(__name__)


# ── Exception hierarchy ────────────────────────────────────────────────────


class AppError(Exception):
    """Base application error with structured HTTP response."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} '{identifier}' not found",
            status_code=404,
            error_code="NOT_FOUND",
        )


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR")


class ExternalServiceError(AppError):
    def __init__(self, service: str, detail: str) -> None:
        super().__init__(
            message=f"External service '{service}' error: {detail}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
        )


# ── Handler registration ──────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                success=False,
                error=exc.message,
                error_code=exc.error_code,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        messages = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        logger.warning("validation_error", path=request.url.path, detail=messages)
        return JSONResponse(
            status_code=422,
            content=APIResponse(
                success=False,
                error=messages,
                error_code="VALIDATION_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content=APIResponse(
                success=False,
                error="Internal server error",
                error_code="INTERNAL_ERROR",
            ).model_dump(),
        )
