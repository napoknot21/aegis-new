from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.bootstrap.container import Container
from app.domain.data_snapshots.service import DataSnapshotApplicationService
from app.domain.identity.entities import AuthenticatedPrincipal
from app.domain.reference.service import ReferenceApplicationService
from app.domain.shared.service import QuotesApplicationService
from app.domain.trades.service import TradeApplicationService
from app.infrastructure.identity import EntraTokenValidator, TokenValidationError
from app.infrastructure.persistence.postgres.identity import load_org_access_by_entra_oid


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_trade_service(container: ContainerDep) -> TradeApplicationService:
    return container.trade_service


TradeServiceDep = Annotated[TradeApplicationService, Depends(get_trade_service)]


def get_data_snapshot_service(container: ContainerDep) -> DataSnapshotApplicationService:
    return container.data_snapshot_service


DataSnapshotServiceDep = Annotated[
    DataSnapshotApplicationService,
    Depends(get_data_snapshot_service),
]


def get_reference_service(container: ContainerDep) -> ReferenceApplicationService:
    return container.reference_service


ReferenceServiceDep = Annotated[ReferenceApplicationService, Depends(get_reference_service)]


def get_quotes_service(container: ContainerDep) -> QuotesApplicationService:
    return container.quotes_service


QuotesServiceDep = Annotated[QuotesApplicationService, Depends(get_quotes_service)]


def get_token_validator(request: Request) -> EntraTokenValidator | None:
    return getattr(request.app.state, "token_validator", None)


TokenValidatorDep = Annotated[EntraTokenValidator | None, Depends(get_token_validator)]


def _extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be a Bearer token.",
        )

    return value.strip()


def get_current_principal(request: Request, token_validator: TokenValidatorDep) -> AuthenticatedPrincipal | None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return None

    if token_validator is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is enabled but the token validator is not configured.",
        )

    token = _extract_bearer_token(request)

    try:
        claims = token_validator.validate_access_token(token)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    org_access = []
    if settings.database_url:
        org_access = load_org_access_by_entra_oid(settings.database_url, claims["oid"])

    return AuthenticatedPrincipal(
        oid=claims["oid"],
        tenant_id=claims.get("tid", ""),
        email=claims.get("email"),
        preferred_username=claims.get("preferred_username"),
        display_name=claims.get("name"),
        claims=claims,
        org_access=org_access,
    )


PrincipalDep = Annotated[AuthenticatedPrincipal | None, Depends(get_current_principal)]


def assert_org_access(id_org: int, principal: AuthenticatedPrincipal | None, request: Request) -> None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return

    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required for this endpoint.",
        )

    if not principal.has_org_access(id_org):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to access organisation {id_org}.",
        )


def resolve_id_org(
    *,
    id_org: int | None,
    principal: AuthenticatedPrincipal | None,
    request: Request,
) -> int:
    settings = request.app.state.settings

    if not settings.auth_enabled:
        if id_org is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="id_org is required when authentication is disabled.",
            )
        return id_org

    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required for this endpoint.",
        )

    if id_org is not None:
        assert_org_access(id_org=id_org, principal=principal, request=request)
        return id_org

    if principal.default_org_id is not None:
        return principal.default_org_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Multiple organisations are available. Select one explicitly.",
    )


def get_accessible_fund_scope(
    *,
    id_org: int,
    principal: AuthenticatedPrincipal | None,
    request: Request,
) -> list[int] | None:
    settings = request.app.state.settings
    if not settings.auth_enabled or principal is None:
        return None

    admin_role_codes = set(settings.auth_admin_role_codes)
    if principal.is_admin_for_org(id_org, admin_role_codes):
        return None

    return principal.accessible_fund_ids_for_org(id_org)


def assert_fund_access(
    *,
    id_org: int,
    id_f: int,
    principal: AuthenticatedPrincipal | None,
    request: Request,
) -> None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return

    assert_org_access(id_org=id_org, principal=principal, request=request)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required for this endpoint.",
        )

    admin_role_codes = set(settings.auth_admin_role_codes)
    if principal.is_admin_for_org(id_org, admin_role_codes):
        return

    accessible_fund_ids = set(principal.accessible_fund_ids_for_org(id_org))
    if id_f not in accessible_fund_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not authorized to access fund {id_f} in organisation {id_org}.",
        )
