"""Decrypted chart statistics and common/get chart bundle payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from birdrecord_cli.i18n import _schema_txt


class ChartReportMonthRow(BaseModel):
    """chart/record/statistics/reports — one month."""

    model_config = ConfigDict(extra="allow")

    taxon_month: int
    report_num: int
    report_num_dubious: int


class ChartTaxonStatisticsRow(BaseModel):
    """chart/record/statistics/taxon — one month."""

    model_config = ConfigDict(extra="allow")

    taxon_month: int
    taxon_num: int = 0
    taxon_count: int = 0
    taxon_num_dubious: int = 0

    @field_validator("taxon_month", mode="before")
    @classmethod
    def _coerce_taxon_month(cls, v: Any) -> int:
        if isinstance(v, float):
            return int(v)
        return int(v)


class ChartRecordSummaryPayload(BaseModel):
    """common/get selectChartRecordSummary — aggregates."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Record/taxon/report rollups.",
                "record/taxon/report 三类汇总。",
            ),
        },
    )

    record_num_dubious: int = Field(
        default=0,
        description=_schema_txt("Dubious records.", "存疑记录数。"),
    )
    taxon_num: int = Field(
        default=0,
        description=_schema_txt("Taxa.", "鸟种数。"),
    )
    taxon_num_dubious: int = Field(
        default=0,
        description=_schema_txt("Dubious taxa.", "存疑鸟种数。"),
    )
    report_num: int = Field(
        default=0,
        description=_schema_txt("Reports.", "记录条数。"),
    )
    record_num: int = Field(
        default=0,
        description=_schema_txt("Records.", "观测记录数。"),
    )


class ChartQueryReportPayload(BaseModel):
    """common/get selectchartQueryReport — report rollup."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Report counts only.",
                "仅记录相关计数。",
            ),
        },
    )

    report_num_dubious: int = Field(
        default=0,
        description=_schema_txt("Dubious reports.", "存疑记录数。"),
    )
    report_num: int = Field(
        default=0,
        description=_schema_txt("Reports.", "记录条数。"),
    )


class DubiousAccurateCounts(BaseModel):
    """dubious + accurate pair (chart naming)."""

    model_config = ConfigDict(extra="forbid")

    dubious: int = Field(
        default=0,
        description=_schema_txt("Dubious count.", "存疑侧计数。"),
    )
    accurate: int = Field(
        default=0,
        description=_schema_txt(
            "Accurate / primary count.",
            "非存疑/主计数。",
        ),
    )


class CommonChartBundleGrouped(BaseModel):
    """common/get chart bundle as record / taxon / report pairs."""

    model_config = ConfigDict(extra="forbid")

    record: DubiousAccurateCounts = Field(
        ...,
        description=_schema_txt(
            "From summary record_*.",
            "来自汇总 record_*。",
        ),
    )
    taxon: DubiousAccurateCounts = Field(
        ...,
        description=_schema_txt(
            "From summary taxon_*.",
            "来自汇总 taxon_*。",
        ),
    )
    report: DubiousAccurateCounts = Field(
        ...,
        description=_schema_txt(
            "From query_report report_*.",
            "来自 query_report 的 report_*。",
        ),
    )


class CommonChartBundleResult(BaseModel):
    """Both chart sqlids for one filter."""

    model_config = ConfigDict(extra="forbid")

    summary: ChartRecordSummaryPayload
    query_report: ChartQueryReportPayload

    def as_grouped(self) -> CommonChartBundleGrouped:
        """``{record, taxon, report}`` with dubious/accurate each."""
        s, q = self.summary, self.query_report
        return CommonChartBundleGrouped(
            record=DubiousAccurateCounts(
                dubious=s.record_num_dubious, accurate=s.record_num
            ),
            taxon=DubiousAccurateCounts(
                dubious=s.taxon_num_dubious, accurate=s.taxon_num
            ),
            report=DubiousAccurateCounts(
                dubious=q.report_num_dubious, accurate=q.report_num
            ),
        )


@dataclass(frozen=True)
class CommonChartBundleFetch:
    """``fetch_common_chart_bundle`` result + optional envelopes."""

    bundle: CommonChartBundleResult
    envelopes: dict[str, Any]


class TaxonMonthSlice(BaseModel):
    """Per-month taxon slice (dubious + accurate)."""

    model_config = ConfigDict(extra="forbid")

    dubious: int = Field(
        default=0,
        description=_schema_txt("taxon_num_dubious.", "对应 taxon_num_dubious。"),
    )
    accurate: int = Field(
        default=0,
        description=_schema_txt("taxon_num.", "对应 taxon_num。"),
    )


class MonthSearchEntry(BaseModel):
    """One month: report chart + taxon chart."""

    model_config = ConfigDict(extra="forbid")

    report: DubiousAccurateCounts = Field(
        ...,
        description=_schema_txt(
            "From statistics/reports.",
            "来自 statistics/reports。",
        ),
    )
    taxon: TaxonMonthSlice = Field(
        ...,
        description=_schema_txt(
            "From statistics/taxon.",
            "来自 statistics/taxon。",
        ),
    )


class SearchStatisticResult(BaseModel):
    """by_month = chart reports + taxon per month; total = common/get chart pair."""

    model_config = ConfigDict(extra="forbid")

    by_month: dict[str, MonthSearchEntry] = Field(
        ...,
        description=_schema_txt(
            'Month key string (e.g. "3").',
            '月份键字符串（如 "3"）。',
        ),
    )
    total: CommonChartBundleGrouped = Field(
        ...,
        description=_schema_txt(
            "Grouped common/get totals.",
            "common/get 图表对的汇总分组。",
        ),
    )


@dataclass(frozen=True)
class SearchStatisticFetch:
    """``fetch_search_statistic`` result + optional envelopes."""

    result: SearchStatisticResult
    envelopes: dict[str, Any]
