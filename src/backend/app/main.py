from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.router import router as api_router
from app.bootstrap.container import build_container
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.identity import EntraTokenValidator


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Service-oriented backend for Aegis.",
    )

    app.state.settings = settings
    app.state.container = build_container(settings)
    app.state.token_validator = None

    if settings.auth_enabled:
        if not settings.auth_authority or not settings.auth_tenant_id or not settings.auth_allowed_audiences:
            raise RuntimeError(
                "AEGIS auth is enabled but the authority, tenant ID, or allowed audiences are not configured."
            )

        app.state.token_validator = EntraTokenValidator(
            authority=settings.auth_authority,
            tenant_id=settings.auth_tenant_id,
            allowed_audiences=settings.auth_allowed_audiences,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
        }

    return app


app = create_app()
