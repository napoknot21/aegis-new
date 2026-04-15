from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.shared.errors import ConflictError, DomainError, NotFoundError


def register_error_handlers (app : FastAPI) -> None :
    """
    Register global error handlers for the application to convert domain exceptions
    into appropriate HTTP responses.
    """
    @app.exception_handler(NotFoundError)
    async def handle_not_found(_ : Request, exc : NotFoundError) -> JSONResponse :
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def handle_conflict( _ : Request, exc : ConflictError) -> JSONResponse :
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def handle_domain_error( _ : Request, exc : DomainError) -> JSONResponse :
        return JSONResponse(status_code=400, content={"detail": str(exc)})
