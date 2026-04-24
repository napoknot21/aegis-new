from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import PrincipalDep, QuotesServiceDep


router = APIRouter(tags=["system"])


class LoginQuoteResponse(BaseModel):
    quote: str
    author: str


class AccessibleOrganisationResponse(BaseModel):
    id_org: int
    id_user: int
    org_code: str
    org_name: str
    email: str
    display_name: str
    office_ids: list[int]
    office_codes: list[str]
    office_names: list[str]
    primary_office_id: int | None = None
    primary_office_code: str | None = None
    primary_office_name: str | None = None
    role_codes: list[str]
    accessible_fund_ids: list[int]
    is_admin: bool


class CurrentSessionResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    oid: str | None = None
    tenant_id: str | None = None
    email: str | None = None
    preferred_username: str | None = None
    display_name: str | None = None
    default_org_id: int | None = None
    orgs: list[AccessibleOrganisationResponse]


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
def get_login_quote(quotes_service: QuotesServiceDep) -> LoginQuoteResponse:
    """Get a random login quote from the database"""
    quote_record = quotes_service.get_random_quote()

    if not quote_record:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No quotes available"
        )

    return LoginQuoteResponse(
        quote=quote_record.quote,
        author=quote_record.author
    )


@router.get("/me", response_model=CurrentSessionResponse)
def get_current_session(request: Request, principal: PrincipalDep) -> CurrentSessionResponse :

    settings = request.app.state.settings
    admin_role_codes = set(settings.auth_admin_role_codes)

    if not settings.auth_enabled:
        return CurrentSessionResponse(
            auth_enabled=False,
            authenticated=False,
            orgs=[],
        )

    if principal is None:
        return CurrentSessionResponse(
            auth_enabled=True,
            authenticated=False,
            orgs=[],
        )

    return CurrentSessionResponse(
        auth_enabled=True,
        authenticated=True,
        oid=principal.oid,
        tenant_id=principal.tenant_id,
        email=principal.email,
        preferred_username=principal.preferred_username,
        display_name=principal.display_name,
        default_org_id=principal.default_org_id,
        orgs=[
            AccessibleOrganisationResponse(
                id_org=item.id_org,
                id_user=item.id_user,
                org_code=item.org_code,
                org_name=item.org_name,
                email=item.email,
                display_name=item.display_name,
                office_ids=item.office_ids,
                office_codes=item.office_codes,
                office_names=item.office_names,
                primary_office_id=item.primary_office_id,
                primary_office_code=item.primary_office_code,
                primary_office_name=item.primary_office_name,
                role_codes=item.role_codes,
                accessible_fund_ids=item.accessible_fund_ids,
                is_admin=principal.is_admin_for_org(item.id_org, admin_role_codes),
            )
            for item in principal.org_access
        ],
    )
