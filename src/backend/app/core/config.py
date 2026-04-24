from __future__ import annotations
from pathlib import Path
from typing import List, Literal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings) :
    """
    Application configuration settings loaded from environment variables or a .env file.
    """
    app_name : str = "Aegis Backend"
    environment : str = "development"
    debug : bool = True

    api_prefix : str = "/api/v1"
    
    host : str = "0.0.0.0"
    port : int = 8000

    allowed_origins_raw : str = "http://localhost:5173,http://localhost:3000"
    persistence_backend : Literal["auto", "memory", "postgres"] = "auto"
    database_url : str | None = None
    auth_enabled : bool = False
    auth_authority : str | None = None
    auth_tenant_id : str | None = None
    auth_client_id : str | None = None
    auth_allowed_audiences_raw : str = ""
    auth_admin_role_codes_raw : str = "super_admin,org_admin,tech_admin"

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=(".env", _BACKEND_DIR / ".env"),
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> List[str] :
        """
        Parse the allowed_origins_raw string into a list of origins, stripping whitespace.
        """
        return [
            origin.strip()
            for origin in self.allowed_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def resolved_persistence_backend(self) -> Literal["memory", "postgres"]:
        if self.persistence_backend == "auto":
            return "postgres" if self.database_url else "memory"
        return self.persistence_backend

    @property
    def auth_allowed_audiences(self) -> List[str]:
        audiences = [
            audience.strip()
            for audience in self.auth_allowed_audiences_raw.split(",")
            if audience.strip()
        ]

        if audiences:
            return audiences

        if self.auth_client_id:
            return [self.auth_client_id, f"api://{self.auth_client_id}"]

        return []

    @property
    def auth_admin_role_codes(self) -> List[str]:
        return [
            role_code.strip().lower()
            for role_code in self.auth_admin_role_codes_raw.split(",")
            if role_code.strip()
        ]


@lru_cache(maxsize=1)
def get_settings () -> Settings :
    return Settings()
