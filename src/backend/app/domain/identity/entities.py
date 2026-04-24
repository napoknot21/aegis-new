from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class OrgAccessRecord:
    id_org: int
    id_user: int
    org_code: str
    org_name: str
    email: str
    display_name: str
    office_ids: list[int] = field(default_factory=list)
    office_codes: list[str] = field(default_factory=list)
    office_names: list[str] = field(default_factory=list)
    primary_office_id: int | None = None
    primary_office_code: str | None = None
    primary_office_name: str | None = None
    role_codes: list[str] = field(default_factory=list)
    accessible_fund_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class AuthenticatedPrincipal:
    oid: str
    tenant_id: str
    email: str | None
    preferred_username: str | None
    display_name: str | None
    claims: dict[str, Any] = field(repr=False)
    org_access: list[OrgAccessRecord] = field(default_factory=list)

    @property
    def default_org_id(self) -> int | None:
        if len(self.org_access) == 1:
            return self.org_access[0].id_org
        return None

    def org_access_for(self, id_org: int) -> OrgAccessRecord | None:
        for item in self.org_access:
            if item.id_org == id_org:
                return item
        return None

    def has_org_access(self, id_org: int) -> bool:
        return self.org_access_for(id_org) is not None

    def user_id_for_org(self, id_org: int) -> int | None:
        access = self.org_access_for(id_org)
        return access.id_user if access is not None else None

    def office_ids_for_org(self, id_org: int) -> list[int]:
        access = self.org_access_for(id_org)
        return list(access.office_ids) if access is not None else []

    def role_codes_for_org(self, id_org: int) -> list[str]:
        access = self.org_access_for(id_org)
        return list(access.role_codes) if access is not None else []

    def accessible_fund_ids_for_org(self, id_org: int) -> list[int]:
        access = self.org_access_for(id_org)
        return list(access.accessible_fund_ids) if access is not None else []

    def is_admin_for_org(self, id_org: int, admin_role_codes: set[str]) -> bool:
        if not admin_role_codes:
            return False

        role_codes = {code.lower() for code in self.role_codes_for_org(id_org)}
        return bool(role_codes.intersection(admin_role_codes))
