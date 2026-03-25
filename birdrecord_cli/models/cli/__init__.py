"""CLI-only Pydantic models (unified search filter, stdout aggregates)."""

from __future__ import annotations

from birdrecord_cli.models.cli.stdout import UnifiedSearchResult
from birdrecord_cli.models.cli.unified_search import (
    UnifiedSearchRequest,
    coerce_unified_search_request,
    unified_search_to_common_activity,
    unified_search_to_region_chart,
)

__all__ = [
    "UnifiedSearchRequest",
    "UnifiedSearchResult",
    "coerce_unified_search_request",
    "unified_search_to_common_activity",
    "unified_search_to_region_chart",
]
