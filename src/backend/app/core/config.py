from __future__ import annotations
from typing import List
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=".env",
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


@lru_cache(maxsize=1)
def get_settings () -> Settings :
    return Settings()
