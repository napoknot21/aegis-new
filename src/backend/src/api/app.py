from __future__ import annotations

"""
app.py
------
FastAPI application factory.
Run with: uvicorn src.api.app:app --reload --port 8000
Or via:   python main.py
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import subred
from src.client.libapi import setup_libapi_path
from src.config.tenant import load_tenant_config
# from src.api.routes import nav, simm, cash, greeks, ...


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup before the server accepts any request.
    This is where we do sys.path.append for LIBAPI — once, cleanly.
    After this, `from libapi.xxx import Xxx` works anywhere in the app.
    """
    config = load_tenant_config()
    setup_libapi_path(config)
    yield
    # shutdown logic here if needed


def create_app() -> FastAPI:

    app = FastAPI(
        title="Aegis API",
        version="1.0.0",
        description="Backend API for Aegis — Risk & Portfolio Management",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",    # Vite dev server
            "http://localhost:3000",    # CRA dev server
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(subred.router)
    # app.include_router(nav.router)
    # app.include_router(simm.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()