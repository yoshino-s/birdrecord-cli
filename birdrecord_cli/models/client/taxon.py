"""Taxon checklist search API and on-disk cache helpers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.constants import DEFAULT_TAXON_VERSION
from birdrecord_cli.i18n import _schema_txt


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


class TaxonRow(BaseModel):
    """taxon/search checklist row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt("One species.", "一个鸟种。"),
        },
    )

    id: int = Field(..., description=_schema_txt("Taxon id.", "鸟种 ID。"))
    taxonorderid: int | None = Field(
        default=None, description=_schema_txt("Order id.", "目 ID。")
    )
    taxonfamilyid: int | None = Field(
        default=None, description=_schema_txt("Family id.", "科 ID。")
    )
    name: str | None = Field(
        default=None, description=_schema_txt("Chinese name.", "中文名。")
    )
    latinname: str | None = Field(
        default=None, description=_schema_txt("Latin name.", "拉丁名。")
    )
    englishname: str | None = Field(
        default=None, description=_schema_txt("English name.", "英文名。")
    )
    pinyin: str | None = Field(
        default=None, description=_schema_txt("Pinyin.", "拼音。")
    )
    guidebooksn: Any | None = Field(
        default=None,
        description=_schema_txt("Field guide ref.", "图鉴/手册编号。"),
    )
    szm: str | None = Field(
        default=None, description=_schema_txt("Initials.", "首字母。")
    )
    subspecies: Any | None = Field(
        default=None, description=_schema_txt("Subspecies.", "亚种。")
    )
    taxonordername: str | None = Field(
        default=None,
        description=_schema_txt("Order (Chinese).", "目名（中文）。"),
    )
    taxonfamilyname: str | None = Field(
        default=None,
        description=_schema_txt("Family (Chinese).", "科名（中文）。"),
    )
    uuid: Any | None = Field(
        default=None, description=_schema_txt("Uuid.", "UUID。")
    )
    serial_id: Any | None = Field(
        default=None, description=_schema_txt("Serial.", "流水号。")
    )
    message: Any | None = Field(
        default=None, description=_schema_txt("Message.", "消息。")
    )
    version: str | None = Field(
        default=None,
        description=_schema_txt("Checklist version.", "清单版本。"),
    )


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
