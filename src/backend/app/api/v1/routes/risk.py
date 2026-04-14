from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from psycopg.rows import dict_row


router = APIRouter(tags=["risk"])


class RiskCategoryResponse(BaseModel):
    id_cat: int
    code: str
    name: str
    description: str | None


class ControlDefinitionResponse(BaseModel):
    id_control: int
    id_cat: int
    code: str
    name: str
    unit: str | None
    description: str | None
    is_active: bool
    risk_categories: RiskCategoryResponse | None = None


class ControlLevelResponse(BaseModel):
    id_level: int
    id_control: int
    id_f: int
    level_rank: int
    level_name: str
    lower_bound: float | None
    lower_inclusive: bool
    upper_bound: float | None
    upper_inclusive: bool
    side: str
    is_active: bool
    risk_control_definitions: ControlDefinitionResponse | None = None


@router.get("/controls", response_model=list[ControlLevelResponse])
def list_risk_controls(
    request: Request,
    id_f: int = Query(..., gt=0),
    id_org: int = Query(..., gt=0),
) -> list[ControlLevelResponse]:
    settings = request.app.state.settings
    if settings.resolved_persistence_backend != "postgres" or not settings.database_url:
        return []

    try:
        with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        l.id_level,
                        l.id_control,
                        l.id_f,
                        l.level_rank,
                        l.level_name,
                        l.lower_bound,
                        l.lower_inclusive,
                        l.upper_bound,
                        l.upper_inclusive,
                        l.side,
                        l.is_active AS level_is_active,
                        d.id_cat,
                        d.code AS definition_code,
                        d.name AS definition_name,
                        d.unit,
                        d.description AS definition_description,
                        d.is_active AS definition_is_active,
                        c.code AS category_code,
                        c.name AS category_name,
                        c.description AS category_description
                    FROM risk_control_levels AS l
                    JOIN risk_control_definitions AS d
                      ON d.id_control = l.id_control
                    LEFT JOIN risk_categories AS c
                      ON c.id_cat = d.id_cat
                    WHERE l.id_f = %s
                      AND l.id_org = %s
                      AND l.is_active = TRUE
                    ORDER BY l.level_rank, l.id_level
                    """,
                    (id_f, id_org),
                )
                rows = cursor.fetchall()
    except psycopg.errors.UndefinedTable:
        return []

    return [_build_control_level_response(row) for row in rows]


def _build_control_level_response(row: dict[str, Any]) -> ControlLevelResponse:
    category = None
    if row["id_cat"] is not None:
        category = RiskCategoryResponse(
            id_cat=int(row["id_cat"]),
            code=row["category_code"],
            name=row["category_name"],
            description=row["category_description"],
        )

    definition = ControlDefinitionResponse(
        id_control=int(row["id_control"]),
        id_cat=int(row["id_cat"]) if row["id_cat"] is not None else 0,
        code=row["definition_code"],
        name=row["definition_name"],
        unit=row["unit"],
        description=row["definition_description"],
        is_active=bool(row["definition_is_active"]),
        risk_categories=category,
    )

    return ControlLevelResponse(
        id_level=int(row["id_level"]),
        id_control=int(row["id_control"]),
        id_f=int(row["id_f"]),
        level_rank=int(row["level_rank"]),
        level_name=row["level_name"],
        lower_bound=float(row["lower_bound"]) if row["lower_bound"] is not None else None,
        lower_inclusive=bool(row["lower_inclusive"]),
        upper_bound=float(row["upper_bound"]) if row["upper_bound"] is not None else None,
        upper_inclusive=bool(row["upper_inclusive"]),
        side=row["side"],
        is_active=bool(row["level_is_active"]),
        risk_control_definitions=definition,
    )
