"""Compatibility exports for the canonical group model."""

from app.db.models.core import YouthGroup

Group = YouthGroup

__all__ = ["Group", "YouthGroup"]
