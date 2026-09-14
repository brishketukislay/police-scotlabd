"""Compatibility exports for the canonical XP ledger.

IMPORTANT:
This module deliberately contains no SQLAlchemy model definitions.
The authoritative XPTransaction lives in app.db.models.core.
"""

from app.db.models.core import XPTransaction

from app.models import XPTransactionType

__all__ = [
    "XPTransaction",
    "XPTransactionType",
]
