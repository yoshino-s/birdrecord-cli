"""Chart / common/get filter requests and typed statistics request models."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


class RegionChartRequest(BaseModel):
    """Chart filters + common/get chart calls; client sets ``sqlid`` per request (input ``sqlid`` ignored)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Chart/share filters; extra keys allowed.",
                "图表/分享筛选条件；允许额外字段。",
            ),
        },
    )

    taxonname: str = Field(
        default="",
        description=_schema_txt(
            "Species name; empty = no filter.",
            "鸟种名称；空表示不过滤。",
        ),
    )
    startTime: str = Field(
        default="",
        description=_schema_txt(
            "Range start YYYY-MM-DD; empty = omit.",
            "范围起始日期 YYYY-MM-DD；空表示不传。",
        ),
        examples=["2026-02-24"],
    )
    endTime: str = Field(
        default="",
        description=_schema_txt(
            "Range end YYYY-MM-DD; empty = omit.",
            "范围结束日期 YYYY-MM-DD；空表示不传。",
        ),
        examples=["2026-03-24"],
    )
    province: str = Field(
        default="",
        description=_schema_txt(
            "Province label (Chinese); empty = omit.",
            "省份名称（中文）；空表示不传。",
        ),
    )
    city: str = Field(
        default="",
        description=_schema_txt(
            "City label (Chinese); empty = omit.",
            "城市名称（中文）；空表示不传。",
        ),
    )
    district: str = Field(
        default="",
        description=_schema_txt(
            "District label (Chinese); empty = omit.",
            "区县名称（中文）；空表示不传。",
        ),
    )
    pointname: str = Field(
        default="",
        description=_schema_txt(
            "Point / hotspot name substring.",
            "观鸟点/热点名称子串。",
        ),
    )
    username: str = Field(
        default="",
        description=_schema_txt("User context; often empty.", "用户上下文；常为空。"),
    )
    serial_id: str = Field(
        default="",
        description=_schema_txt("Share / session id.", "分享/会话 ID。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt(
            "Context date YYYY-MM-DD; empty = omit.",
            "上下文日期 YYYY-MM-DD；空表示不传。",
        ),
        examples=["2026-03-24"],
    )
    taxonid: int = Field(
        default=0,
        description=_schema_txt("Species id; 0 = unset.", "鸟种 ID；0 表示未设置。"),
        examples=[4148],
    )
    version: str = Field(
        default="CH4",
        description=_schema_txt(
            "Client protocol tag (e.g. CH4).",
            "客户端协议标记（如 CH4）。",
        ),
    )


# POST /api/weixin/common/get — sqlid is the only differing field for chart summary vs query-report.
COMMON_GET_SQLID_CHART_RECORD_SUMMARY = "selectChartRecordSummary"
COMMON_GET_SQLID_CHART_QUERY_REPORT = "selectchartQueryReport"


def coerce_region_chart_request(
    body: RegionChartRequest | Mapping[str, Any] | None,
) -> RegionChartRequest:
    """Coerce to ``RegionChartRequest``."""
    if body is None:
        return RegionChartRequest()
    if isinstance(body, RegionChartRequest):
        return body
    return RegionChartRequest.model_validate(body)


def build_common_get_chart_payload(
    filters: RegionChartRequest, *, sqlid: str
) -> dict[str, Any]:
    """common/get body: filters + ``sqlid`` (replaces any existing ``sqlid``)."""
    payload = dict(filters.model_dump())
    payload.pop("sqlid", None)
    payload["sqlid"] = sqlid
    return payload


class ChartStatisticsReportsRequest(RegionChartRequest):
    """POST chart/record/statistics/reports — monthly report counts."""

    sqlid: Literal["selectchartQueryReport"] = Field(
        default="selectchartQueryReport",
    )


class ChartStatisticsTaxonRequest(ChartStatisticsReportsRequest):
    """POST chart/record/statistics/taxon — same body shape as reports in traffic."""
