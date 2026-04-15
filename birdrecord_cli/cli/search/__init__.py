"""CLI: chart search statistic and optional activity drill-down."""

from __future__ import annotations

from typing import Any, Callable

import click
import requests
from click._utils import FLAG_NEEDS_VALUE

from birdrecord_cli.cli.core import (
    CliConfig,
    client_from_cfg,
    emit_json,
    json_schema_text_object,
    parse_cli_body_json,
    with_client_config,
)
from birdrecord_cli.i18n import _cli_txt
from birdrecord_cli.models.client import (
    ChartActivityReportRow,
    ChartActivityTaxonRow,
    build_common_list_taxon_request,
    build_common_page_activity_request,
)
from birdrecord_cli.models.cli import (
    UnifiedSearchRequest,
    UnifiedSearchResult,
    coerce_unified_search_request,
    unified_search_to_common_activity,
    unified_search_to_region_chart,
)
from birdrecord_cli.cli.search.report_map import (
    render_report_map_html,
    upload_report_map_html,
    write_report_map_html,
)


class OptionalValueFlagOption(click.Option):
    """Flag option that optionally consumes a following value token."""

    _previous_parser_process: Callable[[Any, Any], None]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.optional_value = kwargs.pop("optional_value", None)
        super().__init__(*args, **kwargs)

    def add_to_parser(self, parser: Any, ctx: click.Context) -> None:
        super().add_to_parser(parser, ctx)

        def parser_process(value: Any, state: Any) -> None:
            if value is FLAG_NEEDS_VALUE:
                value = self.optional_value
            self._previous_parser_process(value, state)

        for opt in self.opts:
            option = parser._long_opt.get(opt) or parser._short_opt.get(opt)
            if option is not None:
                self._previous_parser_process = option.process
                option.process = parser_process
                break


def register_search_commands(group: click.Group) -> None:
    @group.command(
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
        "--report-map",
        "report_map",
        cls=OptionalValueFlagOption,
        is_flag=False,
        required=False,
        type=str,
        optional_value="output/report_map.html",
        metavar="[OUTPUT_HTML]",
        help=_cli_txt(
            "Generate REPORT MAP: local HTML path (default output/report_map.html) or ONLINE to upload and return URL.",
            "生成 REPORT MAP：本地 HTML 路径（默认 output/report_map.html）或 ONLINE（上传并返回 URL）。",
        ),
    )
    @click.option(
        "--report-limit",
        "report_limit",
        default=None,
        type=int,
        help=_cli_txt(
            "Max total report rows to fetch across pages (stops paging once reached); default = fetch all pages.",
            "跨分页最多获取的记录条数上限（达到后停止翻页）；默认获取全部分页。",
        ),
    )
    @click.option(
        "--body-json",
        default=None,
        help=_cli_txt(
            "Unified filter JSON (UnifiedSearchRequest): chart fields plus optional taxon_month, report_month, outside_type for drill-down.",
            "统一筛选 JSON（UnifiedSearchRequest）：图表字段 + 下钻可选 taxon_month、report_month、outside_type。",
        ),
    )
    @click.option(
        "--schema",
        is_flag=True,
        help=_cli_txt(
            "Print JSON Schemas for request (UnifiedSearchRequest) and response (UnifiedSearchResult) only (no HTTP).",
            "仅打印请求（UnifiedSearchRequest）与响应（UnifiedSearchResult）的 JSON Schema（不发起 HTTP）。",
        ),
    )
    @click.pass_context
    @with_client_config
    def cmd_search(
        ctx: click.Context,
        want_taxon: bool,
        want_report: bool,
        report_map: str | None,
        report_limit: int | None,
        body_json: str | None,
        schema: bool,
    ) -> None:
        if report_map and not want_report:
            raise click.UsageError(
                _cli_txt(
                    "--report-map requires --report.",
                    "--report-map 需要与 --report 一起使用。",
                )
            )
        if schema:
            click.echo(
                json_schema_text_object(
                    {
                        "request": UnifiedSearchRequest,
                        "response": UnifiedSearchResult,
                    }
                )
            )
            return
        cfg = ctx.obj
        assert isinstance(cfg, CliConfig)
        raw_body = parse_cli_body_json(body_json)
        unified = coerce_unified_search_request(raw_body)
        with client_from_cfg(cfg) as client:
            stat_fetch = client.fetch_search_statistic(
                unified_search_to_region_chart(unified),
                collect_envelopes=cfg.envelope,
            )
            taxon_rows: list[ChartActivityTaxonRow] | None = None
            report_rows: list[ChartActivityReportRow] | None = None
            envelopes = dict(stat_fetch.envelopes)
            if want_taxon or want_report:
                base = unified_search_to_common_activity(unified)
                if want_taxon:
                    tcall = client.common_list_activity_taxon(
                        build_common_list_taxon_request(base)
                    )
                    taxon_rows = tcall.payload
                    if cfg.envelope:
                        envelopes["taxon"] = tcall.envelope.model_dump()
                if want_report:
                    report_rows = []
                    page = 1
                    while True:
                        rcall = client.common_page_activity(
                            build_common_page_activity_request(
                                base,
                                report_month=unified.report_month,
                                start=page,
                            )
                        )
                        batch = rcall.payload or []
                        report_rows.extend(batch)
                        if cfg.envelope:
                            envelopes[f"report_page_{page}"] = (
                                rcall.envelope.model_dump()
                            )
                        # Stop if no rows returned
                        if not batch:
                            break
                        # Stop if reached the limit
                        if (
                            report_limit is not None
                            and len(report_rows) >= report_limit
                        ):
                            report_rows = report_rows[:report_limit]
                            break
                        # Stop if we've consumed all available pages
                        env = rcall.envelope
                        total = getattr(env, "total", None)
                        size = getattr(env, "size", None) or len(batch)
                        if total is not None and len(report_rows) >= total:
                            break
                        if len(batch) < size:
                            break
                        page += 1
        report_map_ref: str | None = None
        if report_map and report_rows is not None:
            if report_map.strip().casefold() == "online":
                html = render_report_map_html(
                    report_rows,
                    province=unified.province,
                    city=unified.city,
                    district=unified.district,
                )
                try:
                    report_map_ref = upload_report_map_html(
                        html,
                        timeout=cfg.timeout,
                    )
                except (requests.RequestException, ValueError) as exc:
                    raise click.ClickException(
                        _cli_txt(
                            f"Failed to upload REPORT MAP ONLINE: {exc}",
                            f"REPORT MAP ONLINE 上传失败：{exc}",
                        )
                    ) from exc
                click.echo(
                    _cli_txt(
                        f"Generated REPORT MAP URL: {report_map_ref}",
                        f"已生成 REPORT MAP URL：{report_map_ref}",
                    ),
                    err=True,
                )
            else:
                out_path = write_report_map_html(
                    report_rows,
                    output_path=report_map,
                    province=unified.province,
                    city=unified.city,
                    district=unified.district,
                )
                report_map_ref = str(out_path)
                click.echo(
                    _cli_txt(
                        f"Generated REPORT MAP HTML: {out_path}",
                        f"已生成 REPORT MAP HTML：{out_path}",
                    ),
                    err=True,
                )
        out = UnifiedSearchResult(
            statistic=stat_fetch.result,
            taxon=taxon_rows,
            report=report_rows,
            report_map=report_map_ref,
        )
        if cfg.envelope:
            emit_json(
                {"envelope": envelopes, "payload": out.model_dump(mode="json")},
                pretty=cfg.pretty,
            )
        else:
            emit_json(out.model_dump(mode="json"), pretty=cfg.pretty)
