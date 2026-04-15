"""CLI: provinces and cities (adcode)."""

from __future__ import annotations

import click

from birdrecord_cli.client import _standard_list_call_after_query_filter
from birdrecord_cli.cli.core import (
    CliConfig,
    client_from_cfg,
    emit_call,
    json_schema_text,
    with_client_config,
)
from birdrecord_cli.i18n import _cli_txt
from birdrecord_cli.models.client import (
    AdcodeCityRequest,
    AdcodeProvinceRequest,
    filter_region_rows_by_query,
)


def register_adcode_commands(group: click.Group) -> None:
    @group.command(
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
        with client_from_cfg(cfg) as client:
            raw = client.adcode_provinces()
            filtered = filter_region_rows_by_query(
                list(raw.payload), query, label_attr="province_name"
            )
            emit_call(
                cfg, _standard_list_call_after_query_filter(raw, filtered, query=query)
            )

    @group.command(
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
    def cmd_cities(
        ctx: click.Context, province_code: str, query: str | None, schema: bool
    ) -> None:
        if schema:
            click.echo(json_schema_text(AdcodeCityRequest))
            return
        cfg = ctx.obj
        assert isinstance(cfg, CliConfig)
        with client_from_cfg(cfg) as client:
            raw = client.adcode_cities(province_code)
            filtered = filter_region_rows_by_query(
                list(raw.payload), query, label_attr="city_name"
            )
            emit_call(
                cfg, _standard_list_call_after_query_filter(raw, filtered, query=query)
            )
