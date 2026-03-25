"""Shared Click helpers: config, JSON emit, error group, decorators."""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Type

import click
import httpx
from pydantic import BaseModel

from birdrecord_cli.client import BirdrecordApiError, BirdrecordCall, BirdrecordClient
from birdrecord_cli.constants import BASE_URL
from birdrecord_cli.i18n import _cli_txt


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


def emit_json(data: Any, *, pretty: bool) -> None:
    indent = 2 if pretty else None
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def emit_call(cfg: CliConfig, call: BirdrecordCall[Any, Any]) -> None:
    if cfg.envelope:
        emit_json(
            {
                "envelope": call.envelope.model_dump(),
                "payload": _payload_to_jsonable(call.payload),
            },
            pretty=cfg.pretty,
        )
    else:
        emit_json(_payload_to_jsonable(call.payload), pretty=cfg.pretty)


def emit_enveloped_model(
    cfg: CliConfig, core: BaseModel, envelopes: dict[str, Any]
) -> None:
    """Print model dump, optionally wrapped with multi-call envelopes."""
    data = core.model_dump()
    if cfg.envelope:
        emit_json({"envelope": envelopes, "payload": data}, pretty=cfg.pretty)
    else:
        emit_json(data, pretty=cfg.pretty)


def client_from_cfg(cfg: CliConfig) -> BirdrecordClient:
    return BirdrecordClient(
        token=cfg.token,
        base_url=cfg.base_url,
        verify=cfg.verify,
        timeout=cfg.timeout,
    )


def parse_cli_body_json(body_json: str | None) -> dict[str, Any] | None:
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
                emit_json(e.envelope, pretty=pretty)
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
