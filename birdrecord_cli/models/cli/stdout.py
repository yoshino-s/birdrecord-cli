"""CLI-only stdout result shapes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt
from birdrecord_cli.models.client.activity_payloads import (
    ChartActivityReportRow,
    ChartActivityTaxonRow,
)
from birdrecord_cli.models.client.chart_payloads import SearchStatisticResult


class UnifiedSearchResult(BaseModel):
    """Single stdout JSON shape for ``search``; ``taxon`` / ``report`` are null when flags omitted."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": _schema_txt(
                "search command stdout: statistic always present; taxon/report null unless --taxon/--report.",
                "search 标准输出：statistic 必有；未传 --taxon/--report 时 taxon/report 为 null。",
            ),
        },
    )

    statistic: SearchStatisticResult = Field(
        ...,
        description=_schema_txt(
            "Per-month chart breakdown and rolled-up totals (full date range).",
            "完整日期范围内的按月图表拆分与汇总。",
        ),
    )
    taxon: list[ChartActivityTaxonRow] | None = Field(
        default=None,
        description=_schema_txt(
            "Species ranking when --taxon; null if flag not passed.",
            "传了 --taxon 时为鸟种排行；未传该标志时为 null。",
        ),
    )
    report: list[ChartActivityReportRow] | None = Field(
        default=None,
        description=_schema_txt(
            "Paged report cards when --report; null if flag not passed.",
            "传了 --report 时为分页记录；未传该标志时为 null。",
        ),
    )
