"""Activity drill-down requests for common/list and common/page."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


class CommonActivityRequest(BaseModel):
    """Filters for common/list and common/page (activity chart)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Activity chart drill-down; empty strings when unset.",
                "活动图表下钻筛选；未设置时用空字符串。",
            ),
        },
    )

    taxonname: str = Field(
        default="",
        description=_schema_txt("Species name; empty = none.", "鸟种名称；空表示无。"),
    )
    startTime: str = Field(
        default="",
        description=_schema_txt(
            "Start YYYY-MM-DD; empty = omit.",
            "起始日期 YYYY-MM-DD；空表示不传。",
        ),
        examples=["2026-03-22"],
    )
    endTime: str = Field(
        default="",
        description=_schema_txt(
            "End YYYY-MM-DD; empty = omit.",
            "结束日期 YYYY-MM-DD；空表示不传。",
        ),
        examples=["2026-03-24"],
    )
    province: str = Field(
        default="",
        description=_schema_txt(
            "Province (Chinese); empty = omit.",
            "省份（中文）；空表示不传。",
        ),
    )
    city: str = Field(
        default="",
        description=_schema_txt("City; empty = omit.", "城市；空表示不传。"),
    )
    district: str = Field(
        default="",
        description=_schema_txt("District; empty = omit.", "区县；空表示不传。"),
    )
    pointname: str = Field(
        default="",
        description=_schema_txt("Point name substring.", "观鸟点名称子串。"),
    )
    username: str = Field(
        default="",
        description=_schema_txt("User filter; often empty.", "用户筛选；常为空。"),
    )
    serial_id: str = Field(
        default="",
        description=_schema_txt("Share / serial filter.", "分享/流水号筛选。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt(
            "Reference time string; often empty.",
            "参考时间字符串；常为空。",
        ),
    )
    taxonid: str = Field(
        default="",
        description=_schema_txt(
            "Taxon id string; empty = none.",
            "鸟种 ID 字符串；空表示无。",
        ),
    )
    version: str = Field(
        default="CH4",
        description=_schema_txt("Protocol tag.", "协议标记。"),
    )
    taxon_month: str = Field(
        default="",
        description=_schema_txt(
            "Month bucket (e.g. 03); empty = omit.",
            "月份桶（如 03）；空表示不传。",
        ),
        examples=["03"],
    )
    outside_type: int = Field(
        default=0,
        description=_schema_txt(
            "Series discriminator; 0 = default in traffic.",
            "系列区分字段；抓包中 0 为默认。",
        ),
    )


class CommonListActivityTaxonRequest(CommonActivityRequest):
    """POST common/list — taxon ranking for a chart month."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Taxa + counts; envelope may include page/total/size.",
                "鸟种及数量；信封中可能含 page/total/size。",
            ),
        },
    )

    sqlid: Literal["searchChartActivityTaxon"] = Field(
        default="searchChartActivityTaxon",
        description=_schema_txt(
            "sqlid for taxon activity list.",
            "活动鸟种列表的 sqlid。",
        ),
    )


class CommonPageActivityRequest(CommonActivityRequest):
    """POST common/page — paged activity reports."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Paged report cards; align report_month with taxon_month.",
                "分页记录卡片；report_month 与 taxon_month 对齐。",
            ),
        },
    )

    start: int = Field(
        default=1,
        ge=1,
        description=_schema_txt("1-based page.", "从 1 开始的页码。"),
    )
    limit: int = Field(
        default=50,
        ge=1,
        description=_schema_txt("Page size.", "每页条数。"),
    )
    report_month: str = Field(
        default="",
        description=_schema_txt(
            "Month like taxon_month (e.g. 03); empty = omit.",
            "与 taxon_month 同形的月份（如 03）；空表示不传。",
        ),
        examples=["03"],
    )
    sqlid: Literal["searchChartActivity"] = Field(
        default="searchChartActivity",
        description=_schema_txt(
            "sqlid for paged reports.",
            "分页记录的 sqlid。",
        ),
    )


def coerce_common_activity_request(
    body: CommonActivityRequest | Mapping[str, Any] | None,
) -> CommonActivityRequest:
    """Normalize CLI / caller input to ``CommonActivityRequest``."""
    if body is None:
        return CommonActivityRequest()
    if isinstance(body, CommonActivityRequest):
        return body
    return CommonActivityRequest.model_validate(body)


def build_common_list_taxon_request(
    base: CommonActivityRequest,
) -> CommonListActivityTaxonRequest:
    """Attach ``searchChartActivityTaxon`` sqlid to shared activity filters."""
    return CommonListActivityTaxonRequest.model_validate(base.model_dump())


def build_common_page_activity_request(
    base: CommonActivityRequest,
    *,
    report_month: str | None = None,
    start: int = 1,
) -> CommonPageActivityRequest:
    """Attach ``searchChartActivity`` sqlid and page defaults to shared activity filters."""
    d = base.model_dump()
    if report_month is not None:
        d["report_month"] = report_month
    d["start"] = start
    return CommonPageActivityRequest.model_validate(d)
