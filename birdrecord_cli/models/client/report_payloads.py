"""Decrypted report bundle and related entity payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


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
