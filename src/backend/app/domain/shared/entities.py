from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuoteRecord:
    """Domain record for a login quote"""
    id: int
    domain : str
    author: str
    quote: str
