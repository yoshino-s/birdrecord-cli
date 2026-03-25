"""CLI: single observation report bundle."""

from __future__ import annotations

import click

from birdrecord_cli.cli.core import CliConfig, client_from_cfg, emit_enveloped_model, json_schema_text, with_client_config
from birdrecord_cli.i18n import _cli_txt
from birdrecord_cli.models.client import ReportBundleResult


def register_report_commands(group: click.Group) -> None:
    @group.command(
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
        with client_from_cfg(cfg) as client:
            fetch = client.fetch_report_bundle(
                report_id,
                collect_envelopes=cfg.envelope,
            )
        emit_enveloped_model(cfg, fetch.bundle, fetch.envelopes)
