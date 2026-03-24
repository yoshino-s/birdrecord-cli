"""
Re-export the Birdrecord client and models from ``main`` for tests and ``import birdrecord_client``.

End users: install from PyPI (``pip install birdrecord-cli``) and run ``birdrecord-cli``; or use the
single-file ``main.py`` workflow with ``uv run``.
"""

from __future__ import annotations

from main import (
    AdcodeCityRequest,
    AdcodeProvinceRequest,
    BirdrecordClient,
    CityRow,
    ChartActivityReportRow,
    ChartActivityTaxonRow,
    CommonChartBundleGrouped,
    CommonListActivityTaxonRequest,
    CommonPageActivityRequest,
    DEFAULT_TAXON_VERSION,
    DubiousAccurateCounts,
    MemberProfilePayload,
    MonthSearchEntry,
    PointDetailPayload,
    ProvinceRow,
    RecordSummaryPayload,
    RecordSummaryRequest,
    RegionChartQueryBody,
    ReportBundleResult,
    ReportDetailPayload,
    ReportGetRequest,
    SearchStatisticResult,
    StandardApiEnvelope,
    TaxonMonthSlice,
    TaxonRow,
    TaxonSearchRequest,
    build_common_list_taxon_request,
    build_common_page_activity_request,
    coerce_common_activity_body,
    filter_region_rows_by_query,
    filter_taxon_rows_by_query,
)

from main import _load_taxon_search_disk as _load_taxon_search_disk
from main import _save_taxon_search_disk as _save_taxon_search_disk

__all__ = [
    "AdcodeCityRequest",
    "AdcodeProvinceRequest",
    "BirdrecordClient",
    "CityRow",
    "ChartActivityReportRow",
    "ChartActivityTaxonRow",
    "CommonChartBundleGrouped",
    "CommonListActivityTaxonRequest",
    "CommonPageActivityRequest",
    "DEFAULT_TAXON_VERSION",
    "DubiousAccurateCounts",
    "MemberProfilePayload",
    "MonthSearchEntry",
    "PointDetailPayload",
    "ProvinceRow",
    "RecordSummaryPayload",
    "RecordSummaryRequest",
    "RegionChartQueryBody",
    "ReportBundleResult",
    "ReportDetailPayload",
    "ReportGetRequest",
    "SearchStatisticResult",
    "StandardApiEnvelope",
    "TaxonMonthSlice",
    "TaxonRow",
    "TaxonSearchRequest",
    "_load_taxon_search_disk",
    "_save_taxon_search_disk",
    "build_common_list_taxon_request",
    "build_common_page_activity_request",
    "coerce_common_activity_body",
    "filter_region_rows_by_query",
    "filter_taxon_rows_by_query",
]
