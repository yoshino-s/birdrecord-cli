"""Pydantic models for the HTTP API client (requests, envelopes, decrypted payloads)."""

from __future__ import annotations

from birdrecord_cli.models.client.activity_payloads import (
    ChartActivityReportRow,
    ChartActivityTaxonRow,
)
from birdrecord_cli.models.client.activity_requests import (
    CommonActivityRequest,
    CommonListActivityTaxonRequest,
    CommonPageActivityRequest,
    build_common_list_taxon_request,
    build_common_page_activity_request,
    coerce_common_activity_request,
)
from birdrecord_cli.models.client.adcode import (
    AdcodeCityRequest,
    AdcodeProvinceRequest,
    CityRow,
    ProvinceRow,
    filter_region_rows_by_query,
)
from birdrecord_cli.models.client.chart_payloads import (
    ChartQueryReportPayload,
    ChartRecordSummaryPayload,
    ChartReportMonthRow,
    ChartTaxonStatisticsRow,
    CommonChartBundleFetch,
    CommonChartBundleGrouped,
    CommonChartBundleResult,
    DubiousAccurateCounts,
    MonthSearchEntry,
    SearchStatisticFetch,
    SearchStatisticResult,
    TaxonMonthSlice,
)
from birdrecord_cli.models.client.chart_requests import (
    COMMON_GET_SQLID_CHART_QUERY_REPORT,
    COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
    ChartStatisticsReportsRequest,
    ChartStatisticsTaxonRequest,
    RegionChartRequest,
    build_common_get_chart_payload,
    coerce_region_chart_request,
)
from birdrecord_cli.models.client.envelopes import (
    CommonGetApiEnvelope,
    MemberGetApiEnvelope,
    StandardApiEnvelope,
)
from birdrecord_cli.models.client.report_payloads import (
    MemberProfilePayload,
    PointDetailPayload,
    RecordSummaryPayload,
    ReportBundleFetch,
    ReportBundleResult,
    ReportDetailPayload,
)
from birdrecord_cli.models.client.report_requests import (
    MemberGetRequest,
    PointGetRequest,
    RecordSummaryRequest,
    ReportGetRequest,
)
from birdrecord_cli.models.client.taxon import (
    TAXON_SEARCH_QUERY_FIELDS,
    TaxonRow,
    TaxonSearchRequest,
    filter_taxon_rows_by_query,
    _load_taxon_search_disk,
    _save_taxon_search_disk,
    _taxon_search_cache,
)

__all__ = [
    "COMMON_GET_SQLID_CHART_QUERY_REPORT",
    "COMMON_GET_SQLID_CHART_RECORD_SUMMARY",
    "AdcodeCityRequest",
    "AdcodeProvinceRequest",
    "ChartActivityReportRow",
    "ChartActivityTaxonRow",
    "ChartQueryReportPayload",
    "ChartRecordSummaryPayload",
    "ChartReportMonthRow",
    "ChartStatisticsReportsRequest",
    "ChartStatisticsTaxonRequest",
    "ChartTaxonStatisticsRow",
    "CityRow",
    "CommonActivityRequest",
    "CommonChartBundleFetch",
    "CommonChartBundleGrouped",
    "CommonChartBundleResult",
    "CommonGetApiEnvelope",
    "CommonListActivityTaxonRequest",
    "CommonPageActivityRequest",
    "DubiousAccurateCounts",
    "MemberGetApiEnvelope",
    "MemberGetRequest",
    "MemberProfilePayload",
    "MonthSearchEntry",
    "PointDetailPayload",
    "PointGetRequest",
    "ProvinceRow",
    "RecordSummaryPayload",
    "RecordSummaryRequest",
    "RegionChartRequest",
    "ReportBundleFetch",
    "ReportBundleResult",
    "ReportDetailPayload",
    "ReportGetRequest",
    "SearchStatisticFetch",
    "SearchStatisticResult",
    "StandardApiEnvelope",
    "TAXON_SEARCH_QUERY_FIELDS",
    "TaxonMonthSlice",
    "TaxonRow",
    "TaxonSearchRequest",
    "_load_taxon_search_disk",
    "_save_taxon_search_disk",
    "_taxon_search_cache",
    "build_common_get_chart_payload",
    "build_common_list_taxon_request",
    "build_common_page_activity_request",
    "coerce_common_activity_request",
    "coerce_region_chart_request",
    "filter_region_rows_by_query",
    "filter_taxon_rows_by_query",
]
