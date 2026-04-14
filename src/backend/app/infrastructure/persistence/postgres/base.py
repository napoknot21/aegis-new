from __future__ import annotations

import json
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.domain.shared.errors import ConflictError, DomainError, NotFoundError


def to_jsonb(value: dict[str, Any] | None) -> Jsonb | None:
    if value is None:
        return None
    return Jsonb(value, dumps=lambda item: json.dumps(item, default=str))


def translate_psycopg_error(exc: psycopg.Error, fallback_message: str) -> DomainError:
    detail = getattr(exc.diag, "message_detail", None)
    message = fallback_message if not detail else f"{fallback_message} {detail}"

    if isinstance(exc, psycopg.errors.UniqueViolation):
        return ConflictError(message)
    if isinstance(exc, psycopg.errors.ForeignKeyViolation):
        return NotFoundError(message)
    if isinstance(exc, psycopg.errors.CheckViolation):
        return DomainError(message)
    return DomainError(message)


class PostgresUnitOfWorkBase:
    def __init__(self, database_url: str):
        self._database_url = database_url
        self._connection: psycopg.Connection | None = None
        self._committed = False

    def __enter__(self):
        self._connection = psycopg.connect(self._database_url, row_factory=dict_row)
        self._committed = False
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._connection is None:
            return

        try:
            if exc_type is not None or not self._committed:
                self.rollback()
        finally:
            self._connection.close()
            self._connection = None

    def commit(self) -> None:
        connection = self._connection_or_raise()
        connection.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._connection is None:
            return
        self._connection.rollback()
        self._committed = False

    def _connection_or_raise(self) -> psycopg.Connection:
        if self._connection is None:
            raise RuntimeError("Unit of work not started.")
        return self._connection

    def _next_sequence_value(self, table_name: str, column_name: str) -> int:
        connection = self._connection_or_raise()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(pg_get_serial_sequence(%s, %s)) AS value",
                (table_name, column_name),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError(f"Sequence for {table_name}.{column_name} could not be resolved.")
        return int(row["value"])
