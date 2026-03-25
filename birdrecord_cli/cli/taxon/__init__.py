"""CLI: taxon checklist download and cache."""

from __future__ import annotations

from typing import Any

import click

from birdrecord_cli.client import BirdrecordClient, _taxon_call_for_emit
from birdrecord_cli.cli.core import CliConfig, client_from_cfg, emit_call, json_schema_text, with_client_config
from birdrecord_cli.constants import DEFAULT_TAXON_VERSION
from birdrecord_cli.i18n import _cli_txt
from birdrecord_cli.models.client import (
    TaxonRow,
    TaxonSearchRequest,
    _load_taxon_search_disk,
    _save_taxon_search_disk,
    _taxon_search_cache,
)


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


def register_taxon_commands(group: click.Group) -> None:
    @group.command(
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
        with client_from_cfg(cfg) as client:
            env_dump, full_rows = _ensure_taxon_full_list(client, ver, refresh=refresh)
            call = _taxon_call_for_emit(env_dump, full_rows, query=query)
            emit_call(cfg, call)
