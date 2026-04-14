from __future__ import annotations

from typing import Dict, Optional
from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health () -> Dict[str, str] :
    """
    Health check endpoint to verify that the server is running and responsive.
    """
    settings = get_settings()
    response = {

        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,

    }
    
    return response
