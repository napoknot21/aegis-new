from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain/application layer failures."""


class NotFoundError(DomainError):
    """Raised when a requested domain object does not exist."""


class ConflictError(DomainError):
    """Raised when a command would violate a business invariant."""
