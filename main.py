#! /usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click>=8.1.0",
#   "httpx>=0.28.1",
#   "pycryptodome>=3.21.0",
#   "pydantic>=2.10.0",
#   "pypinyin>=0.53.0",
# ]
# ///

"""
Birdrecord / 观鸟记录 — portal https://www.birdreport.cn/ ; API default host ``weixin.birdrecord.cn``. Typed HTTP client + ``birdrecord-cli`` CLI.

Business JSON often lives under envelope ``data`` / ``result`` and may be AES-CBC (see ``parse_encrypted_envelope``).
"""

from __future__ import annotations

import base64
import functools
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    Literal,
    Mapping,
    Optional,
    Type,
    TypeAlias,
    TypeVar,
    Union,
)

import click
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pypinyin import Style, lazy_pinyin

AES_KEY = b"3583ec0257e2f4c8195eec7410ff1619"
AES_IV = b"d93c0d5ec6352f20"

BASE_URL = "https://weixin.birdrecord.cn"

# Default taxon/search version from captured traffic.
DEFAULT_TAXON_VERSION = "Z4-67FA07177A544FBD96006A7CC7489D25"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 "
    "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Mac "
    "MacWechat/WMPF MacWechat/3.8.7(0x13080712) UnifiedPCMacWechat(0xf264181d) XWEB/19024"
)

DEFAULT_REFERER = "https://servicewechat.com/wx9ebf8f0d26aa0240/91/page-frame.html"


def _cli_use_zh_cn() -> bool:
    """True when BIRDRECORD_CLI_CN is set to a truthy value (0/false/no/off disable)."""
    raw = os.environ.get("BIRDRECORD_CLI_CN")
    if raw is None:
        return False
    s = raw.strip().lower()
    if s in ("0", "false", "no", "off"):
        return False
    return bool(s)


def _cli_txt(en: str, cn: str) -> str:
    return cn if _cli_use_zh_cn() else en


# Bilingual schema text only for models re-exported in ``birdrecord_client`` or emitted
# via CLI ``--schema`` (see ``json_schema_text`` / ``json_schema_text_object``).
_schema_txt = _cli_txt


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AdcodeProvinceRequest(BaseModel):
    """POST adcode/province — body ``{}``."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": _schema_txt("Empty JSON object.", "空 JSON 对象。"),
        },
    )


class AdcodeCityRequest(BaseModel):
    """POST adcode/city — cities under one province."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Province adcode for city list.",
                "省级行政区划代码，用于获取下属城市列表。",
            ),
        },
    )

    province_code: str = Field(
        ...,
        description=_schema_txt(
            "6-digit province adcode (e.g. 110000).",
            "6 位省级行政区划代码（如 110000）。",
        ),
        examples=["110000", "130000"],
    )


class TaxonSearchRequest(BaseModel):
    """POST taxon/search — full checklist for a build version."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Checklist build token (must match server).",
                "清单构建令牌（须与服务器一致）。",
            ),
        },
    )

    version: str = Field(
        default=DEFAULT_TAXON_VERSION,
        description=_schema_txt("Checklist version string.", "清单版本字符串。"),
    )


class RegionChartQueryBody(BaseModel):
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


def coerce_region_chart_body(
    body: RegionChartQueryBody | Mapping[str, Any] | None,
) -> RegionChartQueryBody:
    """Coerce to ``RegionChartQueryBody``."""
    if body is None:
        return RegionChartQueryBody()
    if isinstance(body, RegionChartQueryBody):
        return body
    return RegionChartQueryBody.model_validate(body)


def build_common_get_chart_payload(
    filters: RegionChartQueryBody, *, sqlid: str
) -> dict[str, Any]:
    """common/get body: filters + ``sqlid`` (replaces any existing ``sqlid``)."""
    payload = dict(filters.model_dump())
    payload.pop("sqlid", None)
    payload["sqlid"] = sqlid
    return payload


class ChartStatisticsReportsRequest(RegionChartQueryBody):
    """POST chart/record/statistics/reports — monthly report counts."""

    sqlid: Literal["selectchartQueryReport"] = Field(
        default="selectchartQueryReport",
    )


class ChartStatisticsTaxonRequest(ChartStatisticsReportsRequest):
    """POST chart/record/statistics/taxon — same body shape as reports in traffic."""


class CommonActivityQueryBody(BaseModel):
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


class CommonListActivityTaxonRequest(CommonActivityQueryBody):
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


class CommonPageActivityRequest(CommonActivityQueryBody):
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
        default=15,
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


def coerce_common_activity_body(
    body: CommonActivityQueryBody | Mapping[str, Any] | None,
) -> CommonActivityQueryBody:
    """Normalize CLI / caller input to ``CommonActivityQueryBody``."""
    if body is None:
        return CommonActivityQueryBody()
    if isinstance(body, CommonActivityQueryBody):
        return body
    return CommonActivityQueryBody.model_validate(body)


def build_common_list_taxon_request(
    base: CommonActivityQueryBody,
) -> CommonListActivityTaxonRequest:
    """Attach ``searchChartActivityTaxon`` sqlid to shared activity filters."""
    return CommonListActivityTaxonRequest.model_validate(base.model_dump())


def build_common_page_activity_request(
    base: CommonActivityQueryBody,
) -> CommonPageActivityRequest:
    """Attach ``searchChartActivity`` sqlid and page defaults to shared activity filters."""
    return CommonPageActivityRequest.model_validate(base.model_dump())


class ReportGetRequest(BaseModel):
    """POST reports/get — one report by id."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Request id is string; payload id is numeric.",
                "请求里 id 为字符串；载荷里 id 为数字。",
            ),
        },
    )

    id: str = Field(
        ...,
        description=_schema_txt("Report id string.", "记录 ID 字符串。"),
        examples=["1948816"],
    )


class MemberGetRequest(BaseModel):
    """POST member/get — form-urlencoded (not JSON)."""

    userid: int = Field(..., examples=[89963])


class PointGetRequest(BaseModel):
    """POST point/get — hotspot detail."""

    point_id: int = Field(..., examples=[125887])


class RecordSummaryRequest(BaseModel):
    """POST record/summary — taxon counts for one activity."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": _schema_txt(
                "Same id string as reports/get.",
                "与 reports/get 相同的 id 字符串。",
            ),
        },
    )

    activity_id: str = Field(
        ...,
        description=_schema_txt(
            "Report / activity id string.",
            "记录/活动 ID 字符串。",
        ),
        examples=["1948816"],
    )


# ---------------------------------------------------------------------------
# Response envelope models (raw HTTP JSON before business JSON is extracted)
# ---------------------------------------------------------------------------


class StandardApiEnvelope(BaseModel):
    """Wire JSON for most JSON POST APIs (adcode, taxon, charts, reports, point, record/summary)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Business payload in data/result; may be base64 ciphertext (see field + hasNeedEncrypt).",
                "业务数据在 data/result；可能为 Base64 密文（见 field 与 hasNeedEncrypt）。",
            ),
        },
    )

    advice: Optional[Any] = Field(
        default=None, description=_schema_txt("Hint.", "提示。")
    )
    code: Optional[int] = Field(
        default=None,
        description=_schema_txt(
            "App code; 0 = ok when set.",
            "业务 code；有值时 0 表示成功。",
        ),
    )
    count: Optional[int] = Field(
        default=None,
        description=_schema_txt("Row count hint.", "行数提示。"),
    )
    data: Optional[Union[str, list[Any], dict[str, Any]]] = Field(
        default=None,
        description=_schema_txt("JSON or ciphertext.", "JSON 或密文。"),
    )
    errorCode: Optional[Any] = Field(
        default=None, description=_schema_txt("Error id.", "错误码。")
    )
    field: Optional[str] = Field(
        default=None,
        description=_schema_txt("Key for ciphertext.", "密文字段名。"),
    )
    hasNeedEncrypt: Optional[bool] = Field(
        default=None,
        description=_schema_txt(
            "If true, decrypt envelope[field].",
            "为 true 时解密 envelope[field]。",
        ),
    )
    logId: Optional[Any] = Field(
        default=None, description=_schema_txt("Log id.", "日志 ID。")
    )
    msg: Optional[Any] = Field(
        default=None, description=_schema_txt("Message.", "消息。")
    )
    result: Optional[Union[str, list[Any], dict[str, Any]]] = Field(
        default=None,
        description=_schema_txt("Alt payload / ciphertext.", "备用载荷或密文。"),
    )
    sign: Optional[str] = Field(
        default=None, description=_schema_txt("Digest.", "签名摘要。")
    )
    success: Optional[Any] = Field(
        default=None,
        description=_schema_txt("Success flag.", "成功标记。"),
    )
    timestamp: Optional[int] = Field(
        default=None,
        description=_schema_txt("Server unix time (s).", "服务器 Unix 时间（秒）。"),
    )
    trace: Optional[Any] = Field(
        default=None, description=_schema_txt("Trace id.", "追踪 ID。")
    )


class CommonGetApiEnvelope(BaseModel):
    """Wire JSON for common/get, common/list, common/page (often paginated + ciphertext in result)."""

    model_config = ConfigDict(extra="allow")

    advice: Optional[Any] = None
    code: Optional[int] = None
    count: Optional[int] = None
    data: Optional[Union[str, list[Any], dict[str, Any]]] = None
    errorCode: Optional[Any] = None
    field: Optional[str] = None
    hasNeedEncrypt: Optional[bool] = None
    logId: Optional[Any] = None
    msg: Optional[Any] = None
    page: Optional[int] = None
    result: Optional[Union[str, list[Any], dict[str, Any]]] = None
    sign: Optional[str] = None
    size: Optional[int] = None
    success: Optional[bool] = None
    timestamp: Optional[int] = None
    total: Optional[int] = None
    trace: Optional[Any] = None


class MemberGetApiEnvelope(BaseModel):
    """Wire JSON for member/get (minimal; encrypted data)."""

    model_config = ConfigDict(extra="allow")

    data: Optional[Union[str, list[Any], dict[str, Any]]] = None
    field: Optional[str] = None
    hasNeedEncrypt: Optional[bool] = None
    sign: Optional[str] = None
    success: Optional[bool] = None
    timestamp: Optional[int] = None


# ---------------------------------------------------------------------------
# Decrypted payload models (business data)
# ---------------------------------------------------------------------------


class ProvinceRow(BaseModel):
    """Decrypted adcode/province row."""

    model_config = ConfigDict(extra="allow")

    province_code: str
    province_name: str


class CityRow(BaseModel):
    """Decrypted adcode/city row."""

    model_config = ConfigDict(extra="allow")

    city_name: str
    city_code: str


class TaxonRow(BaseModel):
    """taxon/search checklist row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt("One species.", "一个鸟种。"),
        },
    )

    id: int = Field(..., description=_schema_txt("Taxon id.", "鸟种 ID。"))
    taxonorderid: Optional[int] = Field(
        default=None, description=_schema_txt("Order id.", "目 ID。")
    )
    taxonfamilyid: Optional[int] = Field(
        default=None, description=_schema_txt("Family id.", "科 ID。")
    )
    name: Optional[str] = Field(
        default=None, description=_schema_txt("Chinese name.", "中文名。")
    )
    latinname: Optional[str] = Field(
        default=None, description=_schema_txt("Latin name.", "拉丁名。")
    )
    englishname: Optional[str] = Field(
        default=None, description=_schema_txt("English name.", "英文名。")
    )
    pinyin: Optional[str] = Field(
        default=None, description=_schema_txt("Pinyin.", "拼音。")
    )
    guidebooksn: Optional[Any] = Field(
        default=None,
        description=_schema_txt("Field guide ref.", "图鉴/手册编号。"),
    )
    szm: Optional[str] = Field(
        default=None, description=_schema_txt("Initials.", "首字母。")
    )
    subspecies: Optional[Any] = Field(
        default=None, description=_schema_txt("Subspecies.", "亚种。")
    )
    taxonordername: Optional[str] = Field(
        default=None,
        description=_schema_txt("Order (Chinese).", "目名（中文）。"),
    )
    taxonfamilyname: Optional[str] = Field(
        default=None,
        description=_schema_txt("Family (Chinese).", "科名（中文）。"),
    )
    uuid: Optional[Any] = Field(
        default=None, description=_schema_txt("Uuid.", "UUID。")
    )
    serial_id: Optional[Any] = Field(
        default=None, description=_schema_txt("Serial.", "流水号。")
    )
    message: Optional[Any] = Field(
        default=None, description=_schema_txt("Message.", "消息。")
    )
    version: Optional[str] = Field(
        default=None,
        description=_schema_txt("Checklist version.", "清单版本。"),
    )


# Fields scanned by ``filter_taxon_rows_by_query`` (case-insensitive substring, OR).
TAXON_SEARCH_QUERY_FIELDS: tuple[str, ...] = (
    "name",
    "latinname",
    "englishname",
    "pinyin",
    "szm",
)


def filter_taxon_rows_by_query(
    rows: list[TaxonRow], query: str | None
) -> list[TaxonRow]:
    """Keep rows where ``query`` is a case-insensitive substring of any of the name fields."""
    q = (query or "").strip()
    if not q:
        return rows
    q_fold = q.casefold()

    def texts(row: TaxonRow) -> list[str]:
        out: list[str] = []
        for attr in TAXON_SEARCH_QUERY_FIELDS:
            v = getattr(row, attr, None)
            if v is None:
                continue
            s = v if isinstance(v, str) else str(v)
            if s:
                out.append(s)
        return out

    return [r for r in rows if any(q_fold in t.casefold() for t in texts(r))]


def _region_label_search_texts(label: str) -> list[str]:
    """Chinese label plus toneless pinyin and initials for substring matching."""
    s = (label or "").strip()
    if not s:
        return []
    parts = lazy_pinyin(s, style=Style.NORMAL, errors="ignore")
    out: list[str] = [s]
    if parts:
        joined = "".join(parts)
        if joined:
            out.append(joined)
        initials = "".join(p[0] for p in parts if p)
        if initials:
            out.append(initials)
    return out


def filter_region_rows_by_query(
    rows: list[Any],
    query: str | None,
    *,
    label_attr: str,
) -> list[Any]:
    """Keep rows where ``query`` matches province/city name (case-insensitive), pinyin, or initials."""
    q = (query or "").strip()
    if not q:
        return rows
    q_fold = q.casefold()

    def matches(row: Any) -> bool:
        v = getattr(row, label_attr, None)
        if v is None:
            return False
        text = v if isinstance(v, str) else str(v)
        return any(q_fold in t.casefold() for t in _region_label_search_texts(text))

    return [r for r in rows if matches(r)]


# Process-local full checklist per version (CLI taxon command).
_taxon_search_cache: dict[str, tuple[dict[str, Any], list[TaxonRow]]] = {}


def _taxon_search_cache_dir() -> Path:
    """Directory for on-disk taxon/search JSON caches."""
    override = os.environ.get("BIRDRECORD_CACHE_DIR")
    if override:
        return Path(override) / "taxon"
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "birdrecord" / "taxon"
    return Path.home() / ".cache" / "birdrecord" / "taxon"


def _taxon_search_cache_path(version: str) -> Path:
    h = hashlib.sha256(version.encode("utf-8")).hexdigest()
    return _taxon_search_cache_dir() / f"{h}.json"


def _load_taxon_search_disk(version: str) -> tuple[dict[str, Any], list[TaxonRow]] | None:
    path = _taxon_search_cache_path(version)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if doc.get("version") != version:
        return None
    env = doc.get("envelope")
    rows_j = doc.get("rows")
    if not isinstance(env, dict) or not isinstance(rows_j, list):
        return None
    try:
        rows = [TaxonRow.model_validate(x) for x in rows_j]
    except Exception:
        return None
    return env, rows


def _save_taxon_search_disk(
    version: str, env_dump: dict[str, Any], rows: list[TaxonRow]
) -> None:
    path = _taxon_search_cache_path(version)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    payload = {
        "version": version,
        "envelope": env_dump,
        "rows": [r.model_dump(mode="json") for r in rows],
    }
    try:
        text = json.dumps(payload, ensure_ascii=False)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


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


class ChartActivityTaxonRow(BaseModel):
    """common/list activity taxon row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Taxon + count for chart month.",
                "图表月份内的鸟种及记录数。",
            ),
        },
    )

    taxon_id: int = Field(..., description=_schema_txt("Taxon id.", "鸟种 ID。"))
    taxonname: str = Field(
        ..., description=_schema_txt("Chinese name.", "中文名。")
    )
    latinname: str = Field(
        ..., description=_schema_txt("Latin name.", "拉丁名。")
    )
    englishname: str = Field(
        default="",
        description=_schema_txt("English name.", "英文名。"),
    )
    recordcount: int = Field(
        ...,
        description=_schema_txt("Record count.", "记录数量。"),
    )
    taxonordername: str = Field(
        default="",
        description=_schema_txt("Order (Chinese).", "目名（中文）。"),
    )
    taxonfamilyname: str = Field(
        default="",
        description=_schema_txt("Family (Chinese).", "科名（中文）。"),
    )


class ChartActivityReportRow(BaseModel):
    """common/page activity report row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt("One report card.", "一条记录卡片。"),
        },
    )

    id: int = Field(..., description=_schema_txt("Report id.", "记录 ID。"))
    serial_id: str = Field(
        default="",
        description=_schema_txt("Serial.", "流水号。"),
    )
    name: str = Field(
        default="",
        description=_schema_txt("Title.", "标题。"),
    )
    username: str = Field(
        default="",
        description=_schema_txt("Submitter.", "提交者。"),
    )
    userid: int = Field(
        default=0,
        description=_schema_txt("User id.", "用户 ID。"),
    )
    province_name: str = Field(
        default="",
        description=_schema_txt("Province.", "省。"),
    )
    city_name: str = Field(
        default="",
        description=_schema_txt("City.", "市。"),
    )
    district_name: str = Field(
        default="",
        description=_schema_txt("District.", "区县。"),
    )
    point_name: str = Field(
        default="",
        description=_schema_txt("Point.", "观鸟点。"),
    )
    address: str = Field(
        default="",
        description=_schema_txt("Address.", "地址。"),
    )
    location: str = Field(
        default="",
        description=_schema_txt("Coords.", "坐标。"),
    )
    start_time: str = Field(
        default="",
        description=_schema_txt("Start time.", "开始时间。"),
    )
    end_time: str = Field(
        default="",
        description=_schema_txt("End time.", "结束时间。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt("Created.", "创建时间。"),
    )
    version: str = Field(
        default="",
        description=_schema_txt("Protocol tag.", "协议标记。"),
    )
    state: int = Field(
        default=0,
        description=_schema_txt("State.", "状态。"),
    )
    taxoncount: int = Field(
        default=0,
        description=_schema_txt("Taxon count.", "鸟种数。"),
    )
    family_count: int = Field(
        default=0,
        description=_schema_txt("Family count.", "科数。"),
    )
    order_count: int = Field(
        default=0,
        description=_schema_txt("Order count.", "目数。"),
    )
    outside_count: int = Field(
        default=0,
        description=_schema_txt("Outside count.", "境外计数。"),
    )
    request_id: str = Field(
        default="",
        description=_schema_txt("Request id.", "请求 ID。"),
    )


class SearchCliMergedResult(BaseModel):
    """``search`` output when ``--taxon`` and/or ``--report`` is set (includes chart statistic)."""

    model_config = ConfigDict(extra="forbid")

    statistic: SearchStatisticResult
    taxon: list[ChartActivityTaxonRow] = Field(default_factory=list)
    report: list[ChartActivityReportRow] = Field(default_factory=list)


class ReportDetailPayload(BaseModel):
    """reports/get — report header (not full line list)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Core metadata; common/page rows add location detail.",
                "核心元数据；common/page 行含更多地点细节。",
            ),
        },
    )

    id: int = Field(..., description=_schema_txt("Report id.", "记录 ID。"))
    serial_id: str = Field(
        default="",
        description=_schema_txt("Serial.", "流水号。"),
    )
    name: str = Field(
        default="",
        description=_schema_txt("Title.", "标题。"),
    )
    member_id: int = Field(
        default=0,
        description=_schema_txt("Owner userid.", "所有者用户 ID。"),
    )
    point_id: int = Field(
        default=0,
        description=_schema_txt("Linked point id.", "关联观鸟点 ID。"),
    )
    state: int = Field(
        default=0,
        description=_schema_txt("State.", "状态。"),
    )
    status_type: int = Field(
        default=0,
        description=_schema_txt("Status type.", "状态类型。"),
    )
    domain_type: int = Field(
        default=0,
        description=_schema_txt("Domain type.", "领域类型。"),
    )
    watch_type: int = Field(
        default=0,
        description=_schema_txt("Watch type.", "观察类型。"),
    )
    show_copy: int = Field(
        default=0,
        description=_schema_txt("Copy UI flag.", "复制相关 UI 标记。"),
    )
    version: str = Field(
        default="",
        description=_schema_txt("Protocol tag.", "协议标记。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt("Created.", "创建时间。"),
    )
    update_time: str = Field(
        default="",
        description=_schema_txt("Updated.", "更新时间。"),
    )
    start_time: str = Field(
        default="",
        description=_schema_txt("Obs start.", "观察开始时间。"),
    )
    end_time: str = Field(
        default="",
        description=_schema_txt("Obs end.", "观察结束时间。"),
    )
    effective_hours: str = Field(
        default="",
        description=_schema_txt("Duration string.", "有效时长字符串。"),
    )
    real_quantity: str = Field(
        default="",
        description=_schema_txt("Quantity string.", "数量字符串。"),
    )
    eye_all_birds: str = Field(
        default="",
        description=_schema_txt(
            "All-birds flag string.",
            "是否见全鸟种标记字符串。",
        ),
    )


class MemberProfilePayload(BaseModel):
    """member/get — profile (PII; treat password as secret)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Sensitive; password often hash-like — do not log.",
                "敏感信息；password 常为类哈希字段——勿写入日志。",
            ),
        },
    )

    id: int = Field(
        ...,
        description=_schema_txt(
            "Member id (= request userid).",
            "会员 ID（等于请求的 userid）。",
        ),
    )
    account: str = Field(
        default="",
        description=_schema_txt("Account.", "账号。"),
    )
    username: str = Field(
        default="",
        description=_schema_txt("Display name.", "显示名。"),
    )
    email: str = Field(
        default="",
        description=_schema_txt("Email.", "邮箱。"),
    )
    phone: str = Field(
        default="",
        description=_schema_txt("Phone.", "手机。"),
    )
    membertype: int = Field(
        default=0,
        description=_schema_txt("Tier / role.", "等级/角色。"),
    )
    isactived: int = Field(
        default=0,
        description=_schema_txt("Active flag.", "是否激活。"),
    )
    timecreated: str = Field(
        default="",
        description=_schema_txt("Created.", "创建时间。"),
    )
    wxopenid: str = Field(
        default="",
        description=_schema_txt("WeChat OpenID.", "微信 OpenID。"),
    )
    wxunionid: str = Field(
        default="",
        description=_schema_txt("WeChat UnionID.", "微信 UnionID。"),
    )
    password: str = Field(
        default="",
        description=_schema_txt(
            "Server secret field.",
            "服务端敏感字段。",
        ),
    )


class PointDetailPayload(BaseModel):
    """point/get — hotspot."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Point + admin + coords.",
                "观鸟点、行政区划与坐标。",
            ),
        },
    )

    point_id: int = Field(
        ...,
        description=_schema_txt("Point id.", "观鸟点 ID。"),
    )
    point_name: str = Field(
        default="",
        description=_schema_txt("Name.", "名称。"),
    )
    member_id: int = Field(
        default=0,
        description=_schema_txt("Creator id.", "创建者 ID。"),
    )
    province_name: str = Field(
        default="",
        description=_schema_txt("Province.", "省。"),
    )
    city_name: str = Field(
        default="",
        description=_schema_txt("City.", "市。"),
    )
    district_name: str = Field(
        default="",
        description=_schema_txt("District.", "区县。"),
    )
    adcode: int = Field(
        default=0,
        description=_schema_txt("Adcode.", "行政区划代码。"),
    )
    latitude: float = Field(
        default=0.0,
        description=_schema_txt("Lat.", "纬度。"),
    )
    longitude: float = Field(
        default=0.0,
        description=_schema_txt("Lon.", "经度。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt("Created.", "创建时间。"),
    )
    state: int = Field(
        default=0,
        description=_schema_txt("State.", "状态。"),
    )
    isopen: int = Field(
        default=0,
        description=_schema_txt("Public flag.", "是否公开。"),
    )
    is_hot: int = Field(
        default=0,
        description=_schema_txt("Hot flag.", "是否热门。"),
    )


class RecordSummaryPayload(BaseModel):
    """record/summary — taxon / family / order counts."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Diversity counts for one activity.",
                "单条活动下的多样性计数。",
            ),
        },
    )

    taxon_count: int = Field(
        default=0,
        description=_schema_txt("Species count.", "鸟种数。"),
    )
    taxon_family_count: int = Field(
        default=0,
        description=_schema_txt("Family count.", "科数。"),
    )
    taxon_order_count: int = Field(
        default=0,
        description=_schema_txt("Order count.", "目数。"),
    )


class ReportBundleResult(BaseModel):
    """One report: reports/get + record/summary + optional member + point."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(
        ...,
        description=_schema_txt(
            "Id string for get/summary.",
            "用于 get/summary 的 ID 字符串。",
        ),
    )
    report: ReportDetailPayload = Field(
        ...,
        description=_schema_txt("reports/get.", "reports/get 载荷。"),
    )
    record_summary: RecordSummaryPayload = Field(
        ...,
        description=_schema_txt("record/summary.", "record/summary 载荷。"),
    )
    member: Optional[MemberProfilePayload] = Field(
        default=None,
        description=_schema_txt(
            "member/get if owner id ≠ 0.",
            "所有者 ID 非 0 时来自 member/get。",
        ),
    )
    point: Optional[PointDetailPayload] = Field(
        default=None,
        description=_schema_txt(
            "point/get if point_id ≠ 0.",
            "point_id 非 0 时来自 point/get。",
        ),
    )


@dataclass(frozen=True)
class ReportBundleFetch:
    """``fetch_report_bundle`` + optional envelopes."""

    bundle: ReportBundleResult
    envelopes: dict[str, Any]


EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)
PayloadT = TypeVar("PayloadT")
DictPayloadT = TypeVar("DictPayloadT", bound=BaseModel)
RowModelT = TypeVar("RowModelT", bound=BaseModel)


class BirdrecordApiError(Exception):
    def __init__(
        self, message: str, *, code: Any = None, envelope: Optional[dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.envelope = envelope


def _require_list(inner: Any, err_msg: str, envelope: dict[str, Any]) -> list[Any]:
    if not isinstance(inner, list):
        raise BirdrecordApiError(err_msg, envelope=envelope)
    return inner


def _require_dict(inner: Any, err_msg: str, envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(inner, dict):
        raise BirdrecordApiError(err_msg, envelope=envelope)
    return inner


def _request_body_mapping(body: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    return body.model_dump() if isinstance(body, BaseModel) else dict(body)


def decrypt_aes_cbc_b64(ciphertext_b64: str) -> bytes:
    raw = base64.b64decode(ciphertext_b64)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return unpad(cipher.decrypt(raw), AES.block_size)


def parse_encrypted_envelope(envelope: Mapping[str, Any]) -> Any:
    """Decrypt ``envelope[field]`` when encrypted; else first non-null of ``data`` / ``result``."""
    if envelope.get("hasNeedEncrypt") and envelope.get("field"):
        field = envelope["field"]
        blob = envelope.get(field)
        if isinstance(blob, str):
            plain = decrypt_aes_cbc_b64(blob)
            return json.loads(plain.decode("utf-8"))
    if envelope.get("data") is not None:
        return envelope["data"]
    if envelope.get("result") is not None:
        return envelope["result"]
    return None


def _check_standard_envelope(envelope: dict) -> None:
    code = envelope.get("code")
    if code is not None and code != 0:
        msg = envelope.get("msg") or envelope.get("errorCode") or "API error"
        raise BirdrecordApiError(str(msg), code=code, envelope=envelope)


def _check_common_envelope(envelope: dict) -> None:
    if envelope.get("success") is False:
        msg = envelope.get("msg") or "API error"
        raise BirdrecordApiError(str(msg), code=envelope.get("code"), envelope=envelope)
    code = envelope.get("code")
    if code is not None and code != 0:
        msg = envelope.get("msg") or envelope.get("errorCode") or "API error"
        raise BirdrecordApiError(str(msg), code=code, envelope=envelope)


def _check_member_get_envelope(envelope: dict) -> None:
    if envelope.get("success") is False:
        msg = envelope.get("msg") or "API error"
        raise BirdrecordApiError(str(msg), code=envelope.get("code"), envelope=envelope)


@dataclass(frozen=True)
class BirdrecordCall(Generic[EnvelopeT, PayloadT]):
    envelope: EnvelopeT
    payload: PayloadT


def _taxon_call_for_emit(
    env_dump: dict[str, Any],
    full_rows: list[TaxonRow],
    *,
    query: str | None,
) -> BirdrecordCall[StandardApiEnvelope, list[TaxonRow]]:
    filtered = filter_taxon_rows_by_query(full_rows, query)
    env_d = dict(env_dump)
    if (query or "").strip():
        env_d["count"] = len(filtered)
    return BirdrecordCall(
        envelope=StandardApiEnvelope.model_validate(env_d),
        payload=filtered,
    )


def _standard_list_call_after_query_filter[T](
    raw: BirdrecordCall[StandardApiEnvelope, list[T]],
    filtered: list[T],
    *,
    query: str | None,
) -> BirdrecordCall[StandardApiEnvelope, list[T]]:
    env_d = dict(raw.envelope.model_dump())
    if (query or "").strip():
        env_d["count"] = len(filtered)
    return BirdrecordCall(
        envelope=StandardApiEnvelope.model_validate(env_d),
        payload=filtered,
    )


@dataclass
class BirdrecordResponse:
    """Raw envelope dict + extracted payload (untyped)."""

    envelope: dict[str, Any]
    payload: Any

    @property
    def code(self) -> Any:
        return self.envelope.get("code")


ChartStatisticsPayload: TypeAlias = list[ChartReportMonthRow]
ChartTaxonStatisticsPayload: TypeAlias = list[ChartTaxonStatisticsRow]
ChartActivityTaxonListPayload: TypeAlias = list[ChartActivityTaxonRow]
ChartActivityReportListPayload: TypeAlias = list[ChartActivityReportRow]

MEMBER_GET_PATH = "/api/weixin/member/get"
POINT_GET_PATH = "/api/weixin/point/get"
RECORD_SUMMARY_PATH = "/api/weixin/record/summary"
CHART_STATISTICS_REPORTS_PATH = "/api/weixin/chart/record/statistics/reports"
CHART_STATISTICS_TAXON_PATH = "/api/weixin/chart/record/statistics/taxon"


class BirdrecordClient:
    def __init__(
        self,
        token: str = "share",
        *,
        base_url: str = BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        referer: str = DEFAULT_REFERER,
        verify: bool = True,
        timeout: float = 60.0,
    ) -> None:
        self._token = token
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            verify=verify,
            headers={
                "User-Agent": user_agent,
                "Content-Type": "application/json",
                "xweb_xhr": "1",
                "Referer": referer,
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BirdrecordClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def _headers(self) -> dict[str, str]:
        return {
            "timestamp": str(int(time.time() * 1000)),
            "token": self._token,
        }

    def post(
        self, path: str, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST JSON; raw envelope + parsed payload."""
        path = path if path.startswith("/") else f"/{path}"
        r = self._client.post(path, json=dict(body), headers=self._headers())
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_standard_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def _post_common(
        self, subpath: str, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST common/{subpath}; validates common envelope."""
        sub = subpath.removeprefix("/")
        path = f"/api/weixin/common/{sub}"
        r = self._client.post(path, json=dict(body), headers=self._headers())
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_common_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def post_common_get(
        self, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST common/get."""
        return self._post_common("get", body, check=check)

    def _post_member_get_form(
        self, form: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST member/get (form body)."""
        path = MEMBER_GET_PATH
        headers = {
            **self._headers(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r = self._client.post(path, data=dict(form), headers=headers)
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_member_get_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def _post_standard_list(
        self,
        path: str,
        body: dict[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, list[RowModelT]]:
        raw = self.post(path, body, check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    def _post_standard_dict(
        self,
        path: str,
        body: dict[str, Any],
        *,
        payload_model: type[DictPayloadT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, DictPayloadT]:
        raw = self.post(path, body, check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(raw.payload, err_msg, raw.envelope)
        parsed = payload_model.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def _post_common_list(
        self,
        subpath: str,
        body: dict[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[CommonGetApiEnvelope, list[RowModelT]]:
        raw = self._post_common(subpath, body, check=True)
        env = CommonGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    def _post_common_get_chart(
        self,
        filters: RegionChartQueryBody,
        *,
        sqlid: str,
        err_msg: str,
        payload_model: type[DictPayloadT],
    ) -> BirdrecordCall[CommonGetApiEnvelope, DictPayloadT]:
        payload = build_common_get_chart_payload(filters, sqlid=sqlid)
        raw = self.post_common_get(payload, check=True)
        env = CommonGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(raw.payload, err_msg, raw.envelope)
        parsed = payload_model.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def _post_chart_statistics_rows(
        self,
        path: str,
        payload: Mapping[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, list[RowModelT]]:
        raw = self.post(path, dict(payload), check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    # --- typed endpoints ---

    def adcode_provinces(
        self,
    ) -> BirdrecordCall[StandardApiEnvelope, list[ProvinceRow]]:
        return self._post_standard_list(
            "/api/weixin/adcode/province",
            _request_body_mapping(AdcodeProvinceRequest()),
            row_model=ProvinceRow,
            err_msg="Expected list payload for provinces",
        )

    def adcode_cities(
        self, province_code: str
    ) -> BirdrecordCall[StandardApiEnvelope, list[CityRow]]:
        return self._post_standard_list(
            "/api/weixin/adcode/city",
            _request_body_mapping(AdcodeCityRequest(province_code=province_code)),
            row_model=CityRow,
            err_msg="Expected list payload for cities",
        )

    def taxon_search(
        self, version: Optional[str] = None
    ) -> BirdrecordCall[StandardApiEnvelope, list[TaxonRow]]:
        return self._post_standard_list(
            "/api/weixin/taxon/search",
            _request_body_mapping(
                TaxonSearchRequest(version=version or DEFAULT_TAXON_VERSION)
            ),
            row_model=TaxonRow,
            err_msg="Expected list payload for taxon search",
        )

    def chart_record_statistics_reports(
        self, body: ChartStatisticsReportsRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[StandardApiEnvelope, ChartStatisticsPayload]:
        if body is None:
            body = ChartStatisticsReportsRequest()
        return self._post_chart_statistics_rows(
            CHART_STATISTICS_REPORTS_PATH,
            _request_body_mapping(body),
            row_model=ChartReportMonthRow,
            err_msg="Expected list payload for statistics reports",
        )

    def chart_record_statistics_taxon(
        self,
        body: ChartStatisticsTaxonRequest
        | ChartStatisticsReportsRequest
        | Mapping[str, Any]
        | None = None,
    ) -> BirdrecordCall[StandardApiEnvelope, ChartTaxonStatisticsPayload]:
        if body is None:
            body = ChartStatisticsTaxonRequest()
        return self._post_chart_statistics_rows(
            CHART_STATISTICS_TAXON_PATH,
            _request_body_mapping(body),
            row_model=ChartTaxonStatisticsRow,
            err_msg="Expected list payload for chart/record/statistics/taxon",
        )

    def common_get_chart_summary(
        self, body: RegionChartQueryBody | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartRecordSummaryPayload]:
        return self._post_common_get_chart(
            coerce_region_chart_body(body),
            sqlid=COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
            err_msg="Expected dict payload for chart summary",
            payload_model=ChartRecordSummaryPayload,
        )

    def common_get_chart_query_report(
        self, body: RegionChartQueryBody | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartQueryReportPayload]:
        return self._post_common_get_chart(
            coerce_region_chart_body(body),
            sqlid=COMMON_GET_SQLID_CHART_QUERY_REPORT,
            err_msg="Expected dict payload for chart query report",
            payload_model=ChartQueryReportPayload,
        )

    def fetch_common_chart_bundle(
        self,
        body: RegionChartQueryBody | Mapping[str, Any] | None = None,
        *,
        collect_envelopes: bool = False,
    ) -> CommonChartBundleFetch:
        """Two common/get calls (both chart sqlids) for one filter."""
        filters = coerce_region_chart_body(body)
        c_summary = self._post_common_get_chart(
            filters,
            sqlid=COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
            err_msg="Expected dict payload for chart summary",
            payload_model=ChartRecordSummaryPayload,
        )
        c_query = self._post_common_get_chart(
            filters,
            sqlid=COMMON_GET_SQLID_CHART_QUERY_REPORT,
            err_msg="Expected dict payload for chart query report",
            payload_model=ChartQueryReportPayload,
        )
        bundle = CommonChartBundleResult(
            summary=c_summary.payload, query_report=c_query.payload
        )
        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes[COMMON_GET_SQLID_CHART_RECORD_SUMMARY] = (
                c_summary.envelope.model_dump()
            )
            envelopes[COMMON_GET_SQLID_CHART_QUERY_REPORT] = (
                c_query.envelope.model_dump()
            )
        return CommonChartBundleFetch(bundle=bundle, envelopes=envelopes)

    def fetch_search_statistic(
        self,
        body: RegionChartQueryBody | Mapping[str, Any] | None = None,
        *,
        collect_envelopes: bool = False,
    ) -> SearchStatisticFetch:
        """Chart reports + taxon + common/get pair → ``by_month`` + ``total``."""
        filters = coerce_region_chart_body(body)
        fd = filters.model_dump()
        chart_body = ChartStatisticsReportsRequest.model_validate(fd)
        taxon_body = ChartStatisticsTaxonRequest.model_validate(fd)
        rep_call = self.chart_record_statistics_reports(chart_body)
        tax_call = self.chart_record_statistics_taxon(taxon_body)
        common_fetch = self.fetch_common_chart_bundle(
            filters, collect_envelopes=collect_envelopes
        )
        grouped = common_fetch.bundle.as_grouped()
        reports_by_m = {str(int(r.taxon_month)): r for r in rep_call.payload}
        taxon_by_m = {str(int(r.taxon_month)): r for r in tax_call.payload}
        month_keys = sorted(set(reports_by_m) | set(taxon_by_m), key=lambda k: int(k))
        by_month: dict[str, MonthSearchEntry] = {}
        for m in month_keys:
            rr = reports_by_m.get(m)
            tt = taxon_by_m.get(m)
            by_month[m] = MonthSearchEntry(
                report=DubiousAccurateCounts(
                    dubious=rr.report_num_dubious if rr else 0,
                    accurate=rr.report_num if rr else 0,
                ),
                taxon=TaxonMonthSlice(
                    dubious=tt.taxon_num_dubious if tt else 0,
                    accurate=tt.taxon_num if tt else 0,
                ),
            )
        result = SearchStatisticResult(by_month=by_month, total=grouped)
        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes["chart_record_statistics_reports"] = (
                rep_call.envelope.model_dump()
            )
            envelopes["chart_record_statistics_taxon"] = tax_call.envelope.model_dump()
            envelopes["common_get"] = dict(common_fetch.envelopes)
        return SearchStatisticFetch(result=result, envelopes=envelopes)

    def common_list_activity_taxon(
        self, body: CommonListActivityTaxonRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartActivityTaxonListPayload]:
        if body is None:
            body = CommonListActivityTaxonRequest()
        return self._post_common_list(
            "list",
            _request_body_mapping(body),
            row_model=ChartActivityTaxonRow,
            err_msg="Expected list payload for common/list activity taxon",
        )

    def common_page_activity(
        self, body: CommonPageActivityRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartActivityReportListPayload]:
        if body is None:
            body = CommonPageActivityRequest()
        return self._post_common_list(
            "page",
            _request_body_mapping(body),
            row_model=ChartActivityReportRow,
            err_msg="Expected list payload for common/page activity",
        )

    def reports_get(
        self,
        body: ReportGetRequest | Mapping[str, Any] | None = None,
        *,
        report_id: Optional[str] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, ReportDetailPayload]:
        if body is None:
            if report_id is None:
                body = ReportGetRequest(id="1948816")
            else:
                body = ReportGetRequest(id=str(report_id))
        return self._post_standard_dict(
            "/api/weixin/reports/get",
            _request_body_mapping(body),
            payload_model=ReportDetailPayload,
            err_msg="Expected dict payload for reports/get",
        )

    def member_get(
        self,
        body: MemberGetRequest | Mapping[str, Any] | None = None,
        *,
        userid: Optional[int] = None,
    ) -> BirdrecordCall[MemberGetApiEnvelope, MemberProfilePayload]:
        if body is None:
            uid = 89963 if userid is None else userid
            body = MemberGetRequest(userid=uid)
        form = _request_body_mapping(body)
        raw = self._post_member_get_form(form, check=True)
        env = MemberGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(
            raw.payload, "Expected dict payload for member/get", raw.envelope
        )
        parsed = MemberProfilePayload.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def point_get(
        self,
        body: PointGetRequest | Mapping[str, Any] | None = None,
        *,
        point_id: Optional[int] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, PointDetailPayload]:
        if body is None:
            pid = 125887 if point_id is None else point_id
            body = PointGetRequest(point_id=pid)
        return self._post_standard_dict(
            POINT_GET_PATH,
            _request_body_mapping(body),
            payload_model=PointDetailPayload,
            err_msg="Expected dict payload for point/get",
        )

    def record_summary(
        self,
        body: RecordSummaryRequest | Mapping[str, Any] | None = None,
        *,
        activity_id: Optional[str] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, RecordSummaryPayload]:
        if body is None:
            aid = "1948816" if activity_id is None else str(activity_id)
            body = RecordSummaryRequest(activity_id=aid)
        return self._post_standard_dict(
            RECORD_SUMMARY_PATH,
            _request_body_mapping(body),
            payload_model=RecordSummaryPayload,
            err_msg="Expected dict payload for record/summary",
        )

    def fetch_report_bundle(
        self,
        report_id: str,
        *,
        member_id: Optional[int] = None,
        collect_envelopes: bool = False,
    ) -> ReportBundleFetch:
        """reports/get + record/summary + member/get (if owner) + point/get (if point).

        When ``member_id`` is set, use it for member/get instead of ``report.member_id``.
        """
        rid = str(report_id)
        rg = self.reports_get(report_id=rid)
        rep = rg.payload
        mid_eff = int(member_id) if member_id is not None else int(rep.member_id)

        rs = self.record_summary(activity_id=rid)

        mg_call: Optional[
            BirdrecordCall[MemberGetApiEnvelope, MemberProfilePayload]
        ] = None
        member_payload: Optional[MemberProfilePayload] = None
        if mid_eff:
            mg_call = self.member_get(userid=mid_eff)
            member_payload = mg_call.payload

        pg_call: Optional[BirdrecordCall[StandardApiEnvelope, PointDetailPayload]] = (
            None
        )
        point_payload: Optional[PointDetailPayload] = None
        pid = int(rep.point_id) if getattr(rep, "point_id", 0) else 0
        if pid:
            pg_call = self.point_get(point_id=pid)
            point_payload = pg_call.payload

        bundle = ReportBundleResult(
            report_id=rid,
            report=rep,
            record_summary=rs.payload,
            member=member_payload,
            point=point_payload,
        )

        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes["reports_get"] = rg.envelope.model_dump()
            envelopes["record_summary"] = rs.envelope.model_dump()
            if mg_call is not None:
                envelopes["member_get"] = mg_call.envelope.model_dump()
            if pg_call is not None:
                envelopes["point_get"] = pg_call.envelope.model_dump()

        return ReportBundleFetch(bundle=bundle, envelopes=envelopes)


# ---------------------------------------------------------------------------
# CLI (``birdrecord-cli`` console script / ``uv run main.py``) — Click
# ---------------------------------------------------------------------------


def strip_json_schema_titles(obj: Any) -> Any:
    """Drop ``title`` keys from a JSON Schema tree."""
    if isinstance(obj, dict):
        return {k: strip_json_schema_titles(v) for k, v in obj.items() if k != "title"}
    if isinstance(obj, list):
        return [strip_json_schema_titles(x) for x in obj]
    return obj


def json_schema_text(model: Type[BaseModel]) -> str:
    """Pretty JSON Schema for one model (no titles)."""
    raw = model.model_json_schema()
    return json.dumps(strip_json_schema_titles(raw), ensure_ascii=False, indent=2)


def json_schema_text_object(schemas: Mapping[str, Type[BaseModel]]) -> str:
    """Pretty JSON object of named schemas (no titles)."""
    out: dict[str, Any] = {}
    for name, m in schemas.items():
        out[name] = strip_json_schema_titles(m.model_json_schema())
    return json.dumps(out, ensure_ascii=False, indent=2)


@dataclass
class CliConfig:
    token: str
    base_url: str
    verify: bool
    timeout: float
    pretty: bool
    envelope: bool


def _payload_to_jsonable(payload: Any) -> Any:
    if isinstance(payload, BaseModel):
        return payload.model_dump()
    if isinstance(payload, list):
        if payload and isinstance(payload[0], BaseModel):
            return [x.model_dump() for x in payload]
        return payload
    return payload


def _emit_json(data: Any, *, pretty: bool) -> None:
    indent = 2 if pretty else None
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def _emit_call(cfg: CliConfig, call: BirdrecordCall[Any, Any]) -> None:
    if cfg.envelope:
        _emit_json(
            {
                "envelope": call.envelope.model_dump(),
                "payload": _payload_to_jsonable(call.payload),
            },
            pretty=cfg.pretty,
        )
    else:
        _emit_json(_payload_to_jsonable(call.payload), pretty=cfg.pretty)


def _emit_enveloped_model(
    cfg: CliConfig, core: BaseModel, envelopes: dict[str, Any]
) -> None:
    """Print model dump, optionally wrapped with multi-call envelopes."""
    data = core.model_dump()
    if cfg.envelope:
        _emit_json({"envelope": envelopes, "payload": data}, pretty=cfg.pretty)
    else:
        _emit_json(data, pretty=cfg.pretty)


def _client_from_cfg(cfg: CliConfig) -> BirdrecordClient:
    return BirdrecordClient(
        token=cfg.token,
        base_url=cfg.base_url,
        verify=cfg.verify,
        timeout=cfg.timeout,
    )


def _parse_cli_body_json(body_json: str | None) -> dict[str, Any] | None:
    if body_json:
        return json.loads(body_json)
    return None


class BirdrecordGroup(click.Group):
    """API errors → exit 1; HTTP errors → exit 2."""

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except BirdrecordApiError as e:
            click.echo(
                f"{_cli_txt('API error:', 'API 错误：')} {e}",
                err=True,
            )
            cfg = ctx.obj
            pretty = cfg.pretty if isinstance(cfg, CliConfig) else False
            if e.envelope is not None:
                _emit_json(e.envelope, pretty=pretty)
            raise click.exceptions.Exit(1) from e
        except httpx.HTTPError as e:
            click.echo(
                f"{_cli_txt('HTTP error:', 'HTTP 错误：')} {e}",
                err=True,
            )
            raise click.exceptions.Exit(2) from e


def with_client_config(f: Callable[..., Any]) -> Callable[..., Any]:
    """Shared auth, HTTP, and JSON output flags."""

    @click.option(
        "--envelope",
        is_flag=True,
        help=_cli_txt(
            "Include wire envelope(s) in JSON output.",
            "在 JSON 输出中包含原始响应信封（envelope）。",
        ),
    )
    @click.option(
        "--pretty",
        is_flag=True,
        help=_cli_txt("Pretty-print JSON.", "格式化缩进输出 JSON。"),
    )
    @click.option(
        "--timeout",
        default=60.0,
        show_default=True,
        type=float,
        help=_cli_txt("HTTP timeout (seconds).", "HTTP 超时（秒）。"),
    )
    @click.option(
        "--no-verify",
        is_flag=True,
        help=_cli_txt(
            "Skip TLS certificate verification.",
            "跳过 TLS 证书校验。",
        ),
    )
    @click.option(
        "--base-url",
        default=BASE_URL,
        show_default=True,
        help=_cli_txt("API base URL.", "API 根地址。"),
    )
    @click.option(
        "--token",
        default="share",
        show_default=True,
        help=_cli_txt(
            "Bearer token (e.g. share or JWT).",
            "Bearer 令牌（如 share 或 JWT）。",
        ),
    )
    @functools.wraps(f)
    def wrapped(
        ctx: click.Context,
        token: str,
        base_url: str,
        no_verify: bool,
        timeout: float,
        pretty: bool,
        envelope: bool,
        **kwargs: Any,
    ) -> Any:
        ctx.obj = CliConfig(
            token=token,
            base_url=base_url,
            verify=not no_verify,
            timeout=timeout,
            pretty=pretty,
            envelope=envelope,
        )
        return f(ctx, **kwargs)

    return wrapped


@click.group(
    cls=BirdrecordGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=_cli_txt(
        "Birdrecord mini-program API CLI.",
        "Birdrecord 小程序 API 命令行工具。",
    ),
)
def cli() -> None:
    pass


@cli.command(
    "provinces",
    short_help=_cli_txt(
        "List provinces; optional -q filter by Chinese / pinyin / initials.",
        "列出省份；可用 -q 按中文/拼音/首字母过滤。",
    ),
    help=_cli_txt(
        (
            "List provinces for the region picker. "
            "-q filters by case-insensitive substring on Chinese name, toneless pinyin, or initials."
        ),
        (
            "列出地区选择器用的省份列表。"
            "-q 按不区分大小写的子串匹配中文名、无声调全拼或首字母。"
        ),
    ),
)
@click.option(
    "-q",
    "--query",
    default=None,
    help=_cli_txt(
        "Filter by Chinese name, pinyin, or initials (substring, case-insensitive).",
        "按中文名、全拼或首字母子串过滤（不区分大小写）。",
    ),
)
@click.option(
    "--schema",
    is_flag=True,
    help=_cli_txt(
        "Print request JSON Schema only (no HTTP).",
        "仅打印请求 JSON Schema（不发起 HTTP）。",
    ),
)
@click.pass_context
@with_client_config
def cmd_provinces(ctx: click.Context, query: str | None, schema: bool) -> None:
    if schema:
        click.echo(json_schema_text(AdcodeProvinceRequest))
        return
    cfg = ctx.obj
    assert isinstance(cfg, CliConfig)
    with _client_from_cfg(cfg) as client:
        raw = client.adcode_provinces()
        filtered = filter_region_rows_by_query(
            list(raw.payload), query, label_attr="province_name"
        )
        _emit_call(cfg, _standard_list_call_after_query_filter(raw, filtered, query=query))


@cli.command(
    "cities",
    short_help=_cli_txt(
        "List cities under a province; optional -q filter by Chinese / pinyin / initials.",
        "列出省份下城市；可用 -q 按中文/拼音/首字母过滤。",
    ),
    help=_cli_txt(
        (
            "List cities under one province. "
            "-q filters by case-insensitive substring on Chinese name, toneless pinyin, or initials."
        ),
        (
            "列出指定省份下的城市。"
            "-q 按不区分大小写的子串匹配中文名、无声调全拼或首字母。"
        ),
    ),
)
@click.option(
    "--province-code",
    required=True,
    help=_cli_txt(
        "6-digit province code, e.g. 110000.",
        "6 位省级行政区划代码，例如 110000。",
    ),
)
@click.option(
    "-q",
    "--query",
    default=None,
    help=_cli_txt(
        "Filter by Chinese name, pinyin, or initials (substring, case-insensitive).",
        "按中文名、全拼或首字母子串过滤（不区分大小写）。",
    ),
)
@click.option(
    "--schema",
    is_flag=True,
    help=_cli_txt(
        "Print request JSON Schema only (no HTTP).",
        "仅打印请求 JSON Schema（不发起 HTTP）。",
    ),
)
@click.pass_context
@with_client_config
def cmd_cities(ctx: click.Context, province_code: str, query: str | None, schema: bool) -> None:
    if schema:
        click.echo(json_schema_text(AdcodeCityRequest))
        return
    cfg = ctx.obj
    assert isinstance(cfg, CliConfig)
    with _client_from_cfg(cfg) as client:
        raw = client.adcode_cities(province_code)
        filtered = filter_region_rows_by_query(
            list(raw.payload), query, label_attr="city_name"
        )
        _emit_call(cfg, _standard_list_call_after_query_filter(raw, filtered, query=query))


def _ensure_taxon_full_list(
    client: BirdrecordClient, version: str, *, refresh: bool
) -> tuple[dict[str, Any], list[TaxonRow]]:
    """Return full checklist: memory → disk → network; persist to disk after fetch."""
    if not refresh and version in _taxon_search_cache:
        return _taxon_search_cache[version]
    if not refresh:
        disk = _load_taxon_search_disk(version)
        if disk is not None:
            _taxon_search_cache[version] = disk
            return disk
    raw = client.taxon_search(version=version)
    env_dump = raw.envelope.model_dump()
    full_rows = list(raw.payload)
    _taxon_search_cache[version] = (env_dump, full_rows)
    _save_taxon_search_disk(version, env_dump, full_rows)
    return env_dump, full_rows


@cli.command(
    "taxon",
    short_help=_cli_txt(
        "Download & cache full taxon checklist; optional -q filter.",
        "下载并缓存完整鸟种清单，可用 -q 过滤。",
    ),
    help=_cli_txt(
        (
            "Download the full species checklist for a build version. "
            "Results are cached in memory and on disk (override dir with BIRDRECORD_CACHE_DIR); "
            "--refresh refetches. -q filters Chinese/Latin/English name, pinyin, or initials."
        ),
        (
            "按构建版本下载完整鸟种清单。"
            "结果缓存在内存与磁盘（可用 BIRDRECORD_CACHE_DIR 覆盖目录）；"
            "--refresh 强制重新拉取。-q 按中文名/拉丁名/英文名/拼音/首字母子串过滤。"
        ),
    ),
)
@click.option(
    "--version",
    default=None,
    help=_cli_txt(
        f"Checklist version (default {DEFAULT_TAXON_VERSION}).",
        f"清单版本（默认 {DEFAULT_TAXON_VERSION}）。",
    ),
)
@click.option(
    "-q",
    "--query",
    default=None,
    help=_cli_txt(
        "Case-insensitive substring on name, latinname, englishname, pinyin, szm.",
        "在中文名、拉丁名、英文名、拼音、首字母（szm）上按不区分大小写的子串过滤。",
    ),
)
@click.option(
    "--refresh",
    is_flag=True,
    help=_cli_txt(
        "Ignore cache and refetch (updates cache for this version).",
        "忽略缓存并重新拉取（会更新该版本的缓存）。",
    ),
)
@click.option(
    "--schema",
    is_flag=True,
    help=_cli_txt(
        "Print request JSON Schema only (no HTTP).",
        "仅打印请求 JSON Schema（不发起 HTTP）。",
    ),
)
@click.pass_context
@with_client_config
def cmd_taxon(
    ctx: click.Context,
    version: str | None,
    query: str | None,
    refresh: bool,
    schema: bool,
) -> None:
    if schema:
        click.echo(json_schema_text(TaxonSearchRequest))
        return
    cfg = ctx.obj
    assert isinstance(cfg, CliConfig)
    ver = version or DEFAULT_TAXON_VERSION
    with _client_from_cfg(cfg) as client:
        env_dump, full_rows = _ensure_taxon_full_list(client, ver, refresh=refresh)
        call = _taxon_call_for_emit(env_dump, full_rows, query=query)
        _emit_call(cfg, call)


@cli.command(
    "report",
    help=_cli_txt(
        "One observation report: detail, species summary, author profile, linked hotspot when set.",
        "单条观鸟记录：详情、鸟种摘要、作者资料、若有则含关联热点。",
    ),
)
@click.option(
    "--id",
    "report_id",
    required=True,
    help=_cli_txt("Report id string.", "记录 ID 字符串。"),
)
@click.option(
    "--schema",
    is_flag=True,
    help=_cli_txt(
        "Print result JSON Schema only (no HTTP).",
        "仅打印结果 JSON Schema（不发起 HTTP）。",
    ),
)
@click.pass_context
@with_client_config
def cmd_report_bundle(
    ctx: click.Context,
    report_id: str,
    schema: bool,
) -> None:
    if schema:
        click.echo(json_schema_text(ReportBundleResult))
        return
    cfg = ctx.obj
    assert isinstance(cfg, CliConfig)
    with _client_from_cfg(cfg) as client:
        fetch = client.fetch_report_bundle(
            report_id,
            collect_envelopes=cfg.envelope,
        )
    _emit_enveloped_model(cfg, fetch.bundle, fetch.envelopes)


@cli.command(
    "search",
    short_help=_cli_txt(
        "Chart search statistic; optional activity --taxon / --report.",
        "图表检索统计；可选活动下钻 --taxon / --report。",
    ),
    help=_cli_txt(
        (
            "Chart search: per-month breakdown and rolled-up totals (--body-json). "
            "Add --taxon for species ranking and/or --report for paged cards; omit both to skip those calls."
        ),
        (
            "图表检索：按月拆分与汇总（--body-json）。"
            "需要活动下钻时加 --taxon（鸟种排行）和/或 --report（分页记录）；两者都不传则不请求这两项。"
        ),
    ),
)
@click.option(
    "--taxon",
    "want_taxon",
    is_flag=True,
    help=_cli_txt(
        "Include per-species record counts for the chart month (common/list).",
        "包含图表月份内各鸟种记录数（common/list）。",
    ),
)
@click.option(
    "--report",
    "want_report",
    is_flag=True,
    help=_cli_txt(
        "Include paged observation report cards (common/page).",
        "包含分页观鸟记录卡片（common/page）。",
    ),
)
@click.option(
    "--body-json",
    default=None,
    help=_cli_txt(
        "Filter fields as JSON (chart statistic; activity drill-down uses the same object, coerced per API).",
        "筛选 JSON（图表统计；活动下钻共用同一对象，按接口分别校验）。",
    ),
)
@click.option(
    "--schema",
    is_flag=True,
    help=_cli_txt(
        "Print JSON Schemas for filters and responses only (no HTTP).",
        "仅打印筛选与多种响应形态的 JSON Schema（不发起 HTTP）。",
    ),
)
@click.pass_context
@with_client_config
def cmd_search(
    ctx: click.Context,
    want_taxon: bool,
    want_report: bool,
    body_json: str | None,
    schema: bool,
) -> None:
    if schema:
        click.echo(
            json_schema_text_object(
                {
                    "request_chart_filters": RegionChartQueryBody,
                    "request_activity_drilldown": CommonActivityQueryBody,
                    "response_statistics_only": SearchStatisticResult,
                    "response_with_taxon_or_report": SearchCliMergedResult,
                }
            )
        )
        return
    cfg = ctx.obj
    assert isinstance(cfg, CliConfig)
    raw_body = _parse_cli_body_json(body_json)
    with _client_from_cfg(cfg) as client:
        stat_fetch = client.fetch_search_statistic(
            raw_body, collect_envelopes=cfg.envelope
        )
        taxon_rows: list[ChartActivityTaxonRow] = []
        report_rows: list[ChartActivityReportRow] = []
        envelopes = dict(stat_fetch.envelopes)
        if want_taxon or want_report:
            base = coerce_common_activity_body(raw_body)
            if want_taxon:
                tcall = client.common_list_activity_taxon(
                    build_common_list_taxon_request(base)
                )
                taxon_rows = tcall.payload
                if cfg.envelope:
                    envelopes["taxon"] = tcall.envelope.model_dump()
            if want_report:
                rcall = client.common_page_activity(
                    build_common_page_activity_request(base)
                )
                report_rows = rcall.payload
                if cfg.envelope:
                    envelopes["report"] = rcall.envelope.model_dump()
    if want_taxon or want_report:
        payload: dict[str, Any] = {
            "statistic": stat_fetch.result.model_dump(mode="json"),
        }
        if want_taxon:
            payload["taxon"] = [r.model_dump(mode="json") for r in taxon_rows]
        if want_report:
            payload["report"] = [r.model_dump(mode="json") for r in report_rows]
        if cfg.envelope:
            _emit_json({"envelope": envelopes, "payload": payload}, pretty=cfg.pretty)
        else:
            _emit_json(payload, pretty=cfg.pretty)
    else:
        _emit_enveloped_model(cfg, stat_fetch.result, stat_fetch.envelopes)


def main() -> None:
    """Entry point for the ``birdrecord-cli`` console script."""
    cli.main(prog_name="birdrecord-cli", standalone_mode=True)


if __name__ == "__main__":
    main()
