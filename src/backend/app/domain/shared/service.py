from __future__ import annotations

from app.domain.shared.entities import QuoteRecord
from app.infrastructure.persistence.postgres.reference import PostgresReferenceUnitOfWork


class QuotesApplicationService:
    """Application service for managing login quotes"""

    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    def get_random_quote(self) -> QuoteRecord | None:
        """Get a random active quote for the login page"""
        with self._uow_factory() as uow:
            return uow.get_random_quote()
