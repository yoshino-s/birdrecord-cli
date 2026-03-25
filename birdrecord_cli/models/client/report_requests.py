"""Small JSON bodies for reports, member, point, record/summary."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


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
