from __future__ import annotations

import random
from typing import Dict
from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(tags=["system"])


class LoginQuoteResponse(BaseModel):
    quote: str
    author: str


_LOGIN_QUOTES: tuple[LoginQuoteResponse, ...] = (
    LoginQuoteResponse(
        quote="Discipline is choosing between what you want now and what you want most.",
        author="Abraham Lincoln",
    ),
    LoginQuoteResponse(
        quote="Risk comes from not knowing what you're doing.",
        author="Warren Buffett",
    ),
    LoginQuoteResponse(
        quote="The first rule is not to lose. The second rule is not to forget the first rule.",
        author="Warren Buffett",
    ),
    LoginQuoteResponse(
        quote="In investing, what is comfortable is rarely profitable.",
        author="Robert Arnott",
    ),
)


@router.get("/health")
def health (request: Request) -> Dict[str, str] :
    """
    Health check endpoint to verify that the server is running and responsive.
    """
    settings = request.app.state.settings
    response = {

        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "persistence_backend": settings.resolved_persistence_backend,

    }
    
    return response


@router.get("/login-quote", response_model=LoginQuoteResponse)
def get_login_quote() -> LoginQuoteResponse:
    return random.choice(_LOGIN_QUOTES)
