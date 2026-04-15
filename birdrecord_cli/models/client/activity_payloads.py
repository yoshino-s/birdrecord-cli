"""Decrypted common/list and common/page activity rows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


class ChartActivityTaxonRow(BaseModel):
    """common/list activity taxon row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Taxon + count for chart month.",
                "图表月份内的鸟种及记录数。",
            ),
        },
    )

    taxon_id: int = Field(..., description=_schema_txt("Taxon id.", "鸟种 ID。"))
    taxonname: str = Field(..., description=_schema_txt("Chinese name.", "中文名。"))
    latinname: str = Field(..., description=_schema_txt("Latin name.", "拉丁名。"))
    englishname: str = Field(
        default="",
        description=_schema_txt("English name.", "英文名。"),
    )
    recordcount: int = Field(
        ...,
        description=_schema_txt("Record count.", "记录数量。"),
    )
    taxonordername: str = Field(
        default="",
        description=_schema_txt("Order (Chinese).", "目名（中文）。"),
    )
    taxonfamilyname: str = Field(
        default="",
        description=_schema_txt("Family (Chinese).", "科名（中文）。"),
    )


class ChartActivityReportRow(BaseModel):
    """common/page activity report row."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt("One report card.", "一条记录卡片。"),
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
    username: str = Field(
        default="",
        description=_schema_txt("Submitter.", "提交者。"),
    )
    userid: int = Field(
        default=0,
        description=_schema_txt("User id.", "用户 ID。"),
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
    point_name: str = Field(
        default="",
        description=_schema_txt("Point.", "观鸟点。"),
    )
    address: str = Field(
        default="",
        description=_schema_txt("Address.", "地址。"),
    )
    location: str = Field(
        default="",
        description=_schema_txt("Coords.", "坐标。"),
    )
    start_time: str = Field(
        default="",
        description=_schema_txt("Start time.", "开始时间。"),
    )
    end_time: str = Field(
        default="",
        description=_schema_txt("End time.", "结束时间。"),
    )
    ctime: str = Field(
        default="",
        description=_schema_txt("Created.", "创建时间。"),
    )
    version: str = Field(
        default="",
        description=_schema_txt("Protocol tag.", "协议标记。"),
    )
    state: int = Field(
        default=0,
        description=_schema_txt("State.", "状态。"),
    )
    taxoncount: int = Field(
        default=0,
        description=_schema_txt("Taxon count.", "鸟种数。"),
    )
    family_count: int = Field(
        default=0,
        description=_schema_txt("Family count.", "科数。"),
    )
    order_count: int = Field(
        default=0,
        description=_schema_txt("Order count.", "目数。"),
    )
    outside_count: int = Field(
        default=0,
        description=_schema_txt("Outside count.", "境外计数。"),
    )
    request_id: str = Field(
        default="",
        description=_schema_txt("Request id.", "请求 ID。"),
    )
