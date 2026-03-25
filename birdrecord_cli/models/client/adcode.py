"""Adcode API request bodies and decrypted region rows."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pypinyin import Style, lazy_pinyin

from birdrecord_cli.i18n import _schema_txt


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
