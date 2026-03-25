"""Unified CLI ``search`` filter: maps chart vs activity client requests."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt
from birdrecord_cli.models.client.activity_requests import CommonActivityRequest
from birdrecord_cli.models.client.chart_requests import RegionChartRequest


class UnifiedSearchRequest(RegionChartRequest):
    """Unified ``search --body-json`` filter: chart fields (``RegionChartRequest``) plus optional month pins for activity lists only."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Unified search filters. Chart statistic endpoints use only the inherited chart fields; "
                "they ignore taxon_month / report_month / outside_type. When --taxon or --report is set, "
                "taxon_month (and report_month for --report) may narrow list rows to one calendar month inside startTime–endTime "
                "(e.g. 03 = March only across the whole range). Empty = all months in range. "
                "Statistic.by_month and statistic.total are always computed for the full date range.",
                "search 统一筛选：继承的图表字段用于统计接口；taxon_month / report_month / outside_type 仅在下钻时参与。"
                "taxon_month（及 --report 时的 report_month）用于在 startTime–endTime 内只取某一公历月的鸟种列表/记录列表（如 03 表示每年三月）；"
                "留空则范围内各月都参与列表。全局按月汇总 statistic.by_month 与 statistic.total 始终按完整日期范围，不受月份钉影响。",
            ),
        },
    )

    taxon_month: str = Field(
        default="",
        description=_schema_txt(
            "Two-digit month (01–12), e.g. 03. Only used with --taxon (and should align with --report when both). "
            "Restricts the species list to records in that month within startTime–endTime; empty = all months. "
            "Does not change chart statistics.",
            "两位月份 01–12，如 03。仅在传 --taxon 时生效（与 --report 同时传时建议与 report_month 一致）。"
            "将鸟种排行限制在该月出现在范围内的记录；空表示不按月钉。不改变图表统计结果。",
        ),
        examples=["03"],
    )
    report_month: str = Field(
        default="",
        description=_schema_txt(
            "Same shape as taxon_month. Only used with --report. "
            "Restricts paged report cards to that month inside the range; empty = all months. "
            "Does not change chart statistics.",
            "与 taxon_month 同形。仅在传 --report 时生效。"
            "将分页记录限制在该月；空表示不按月钉。不改变图表统计。",
        ),
        examples=["03"],
    )
    outside_type: int = Field(
        default=0,
        description=_schema_txt(
            "Activity list discriminator (0 in captured traffic). Passed to common/list and common/page only.",
            "活动列表区分字段（抓包中多为 0）。仅随下钻请求传递。",
        ),
    )


def coerce_unified_search_request(
    body: UnifiedSearchRequest | Mapping[str, Any] | None,
) -> UnifiedSearchRequest:
    """Coerce CLI / JSON to ``UnifiedSearchRequest`` (chart fields + optional month pins)."""
    if body is None:
        return UnifiedSearchRequest()
    if isinstance(body, UnifiedSearchRequest):
        return body
    return UnifiedSearchRequest.model_validate(body)


def unified_search_to_region_chart(body: UnifiedSearchRequest) -> RegionChartRequest:
    """Strip activity-only fields for chart/statistics calls."""
    data = body.model_dump(mode="python")
    data.pop("taxon_month", None)
    data.pop("report_month", None)
    data.pop("outside_type", None)
    return RegionChartRequest.model_validate(data)


def unified_search_to_common_activity(body: UnifiedSearchRequest) -> CommonActivityRequest:
    """Map chart taxonid (int) to activity string taxonid; drop report_month (page request adds it)."""
    data = body.model_dump(exclude={"report_month"}, mode="python")
    tid = data.get("taxonid", 0)
    if tid in (None, "", 0):
        data["taxonid"] = ""
    elif isinstance(tid, int):
        data["taxonid"] = str(tid)
    else:
        data["taxonid"] = str(tid)
    return CommonActivityRequest.model_validate(data)
