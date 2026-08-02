"""Domain exception hierarchy and FastAPI exception handlers.

Services raise these instead of HTTP-specific exceptions, keeping the
service layer free of any FastAPI/Starlette import. Handlers are registered
once in ``main.py`` and translate them to HTTP responses at the edge.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base class for all application-raised errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Requested entity does not exist."""


class ValidationError(DomainError):
    """Input failed a business-rule check (distinct from Pydantic schema validation)."""


class ConflictError(DomainError):
    """Request conflicts with current state (e.g. duplicate VIN, referenced entity)."""


class ExternalServiceError(DomainError):
    """A dependency outside our control (e.g. vPIC) failed or is unavailable."""


_STATUS_BY_EXCEPTION: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    ConflictError: 409,
    ExternalServiceError: 502,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code = _STATUS_BY_EXCEPTION.get(type(exc), 400)
        return JSONResponse(status_code=status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing %s %s", request.method, request.url)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
