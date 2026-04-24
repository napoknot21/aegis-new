from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from app.domain.identity.entities import OrgAccessRecord


def load_org_access_by_entra_oid(database_url: str, entra_oid: str) -> list[OrgAccessRecord]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.id_org,
                    u.id_user,
                    o.code AS org_code,
                    COALESCE(o.display_name, o.legal_name) AS org_name,
                    u.email,
                    u.display_name,
                    COALESCE(office_ctx.office_ids, ARRAY[]::BIGINT[]) AS office_ids,
                    COALESCE(office_ctx.office_codes, ARRAY[]::TEXT[]) AS office_codes,
                    COALESCE(office_ctx.office_names, ARRAY[]::TEXT[]) AS office_names,
                    office_ctx.primary_office_id,
                    office_ctx.primary_office_code,
                    office_ctx.primary_office_name,
                    COALESCE(role_ctx.role_codes, ARRAY[]::TEXT[]) AS role_codes,
                    COALESCE(fund_ctx.accessible_fund_ids, ARRAY[]::BIGINT[]) AS accessible_fund_ids
                FROM users AS u
                JOIN organisations AS o
                  ON o.id_org = u.id_org
                LEFT JOIN LATERAL (
                    SELECT
                        ARRAY_AGG(DISTINCT uo.id_off ORDER BY uo.id_off) AS office_ids,
                        ARRAY_AGG(DISTINCT off.code ORDER BY off.code) AS office_codes,
                        ARRAY_AGG(DISTINCT off.name ORDER BY off.name) AS office_names,
                        MAX(uo.id_off) FILTER (WHERE uo.is_primary) AS primary_office_id,
                        MAX(off.code) FILTER (WHERE uo.is_primary) AS primary_office_code,
                        MAX(off.name) FILTER (WHERE uo.is_primary) AS primary_office_name
                    FROM user_offices AS uo
                    JOIN offices AS off
                      ON off.id_org = uo.id_org
                     AND off.id_off = uo.id_off
                    WHERE uo.id_org = u.id_org
                      AND uo.id_user = u.id_user
                      AND uo.is_active = TRUE
                      AND off.is_active = TRUE
                ) AS office_ctx ON TRUE
                LEFT JOIN LATERAL (
                    SELECT ARRAY_AGG(DISTINCT ar.code ORDER BY ar.code) AS role_codes
                    FROM user_access_roles AS uar
                    JOIN access_roles AS ar
                      ON ar.id_org = uar.id_org
                     AND ar.id_role = uar.id_role
                    WHERE uar.id_org = u.id_org
                      AND uar.id_user = u.id_user
                      AND uar.is_active = TRUE
                      AND ar.is_active = TRUE
                ) AS role_ctx ON TRUE
                LEFT JOIN LATERAL (
                    SELECT ARRAY_AGG(DISTINCT foa.id_f ORDER BY foa.id_f) AS accessible_fund_ids
                    FROM user_offices AS uo
                    JOIN offices AS off
                      ON off.id_org = uo.id_org
                     AND off.id_off = uo.id_off
                    JOIN fund_office_access AS foa
                      ON foa.id_org = uo.id_org
                     AND foa.id_off = uo.id_off
                    JOIN funds AS f
                      ON f.id_org = foa.id_org
                     AND f.id_f = foa.id_f
                    WHERE uo.id_org = u.id_org
                      AND uo.id_user = u.id_user
                      AND uo.is_active = TRUE
                      AND off.is_active = TRUE
                      AND foa.is_active = TRUE
                      AND f.is_active = TRUE
                ) AS fund_ctx ON TRUE
                WHERE u.entra_oid = %s
                  AND u.is_active = TRUE
                  AND o.is_active = TRUE
                ORDER BY u.id_org, u.id_user
                """,
                (entra_oid,),
            )
            rows = cursor.fetchall()

    return [
        OrgAccessRecord(
            id_org=int(row["id_org"]),
            id_user=int(row["id_user"]),
            org_code=row["org_code"],
            org_name=row["org_name"],
            email=row["email"],
            display_name=row["display_name"],
            office_ids=[int(value) for value in (row["office_ids"] or [])],
            office_codes=list(row["office_codes"] or []),
            office_names=list(row["office_names"] or []),
            primary_office_id=int(row["primary_office_id"]) if row["primary_office_id"] is not None else None,
            primary_office_code=row["primary_office_code"],
            primary_office_name=row["primary_office_name"],
            role_codes=list(row["role_codes"] or []),
            accessible_fund_ids=[int(value) for value in (row["accessible_fund_ids"] or [])],
        )
        for row in rows
    ]
