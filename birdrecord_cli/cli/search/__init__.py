"""CLI: chart search statistic and optional activity drill-down."""

from __future__ import annotations

import click

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
        body_json: str | None,
        schema: bool,
    ) -> None:
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
                    rcall = client.common_page_activity(
                        build_common_page_activity_request(
                            base, report_month=unified.report_month
                        )
                    )
                    report_rows = rcall.payload
                    if cfg.envelope:
                        envelopes["report"] = rcall.envelope.model_dump()
        out = UnifiedSearchResult(
            statistic=stat_fetch.result,
            taxon=taxon_rows,
            report=report_rows,
        )
        if cfg.envelope:
            emit_json(
                {"envelope": envelopes, "payload": out.model_dump(mode="json")},
                pretty=cfg.pretty,
            )
        else:
            emit_json(out.model_dump(mode="json"), pretty=cfg.pretty)
