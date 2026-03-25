"""Wire JSON envelope shapes (before business payload extraction)."""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from birdrecord_cli.i18n import _schema_txt


class StandardApiEnvelope(BaseModel):
    """Wire JSON for most JSON POST APIs (adcode, taxon, charts, reports, point, record/summary)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": _schema_txt(
                "Business payload in data/result; may be base64 ciphertext (see field + hasNeedEncrypt).",
                "业务数据在 data/result；可能为 Base64 密文（见 field 与 hasNeedEncrypt）。",
            ),
        },
    )

    advice: Optional[Any] = Field(
        default=None, description=_schema_txt("Hint.", "提示。")
    )
    code: Optional[int] = Field(
        default=None,
        description=_schema_txt(
            "App code; 0 = ok when set.",
            "业务 code；有值时 0 表示成功。",
        ),
    )
    count: Optional[int] = Field(
        default=None,
        description=_schema_txt("Row count hint.", "行数提示。"),
    )
    data: Optional[Union[str, list[Any], dict[str, Any]]] = Field(
        default=None,
        description=_schema_txt("JSON or ciphertext.", "JSON 或密文。"),
    )
    errorCode: Optional[Any] = Field(
        default=None, description=_schema_txt("Error id.", "错误码。")
    )
    field: Optional[str] = Field(
        default=None,
        description=_schema_txt("Key for ciphertext.", "密文字段名。"),
    )
    hasNeedEncrypt: Optional[bool] = Field(
        default=None,
        description=_schema_txt(
            "If true, decrypt envelope[field].",
            "为 true 时解密 envelope[field]。",
        ),
    )
    logId: Optional[Any] = Field(
        default=None, description=_schema_txt("Log id.", "日志 ID。")
    )
    msg: Optional[Any] = Field(
        default=None, description=_schema_txt("Message.", "消息。")
    )
    result: Optional[Union[str, list[Any], dict[str, Any]]] = Field(
        default=None,
        description=_schema_txt("Alt payload / ciphertext.", "备用载荷或密文。"),
    )
    sign: Optional[str] = Field(
        default=None, description=_schema_txt("Digest.", "签名摘要。")
    )
    success: Optional[Any] = Field(
        default=None,
        description=_schema_txt("Success flag.", "成功标记。"),
    )
    timestamp: Optional[int] = Field(
        default=None,
        description=_schema_txt("Server unix time (s).", "服务器 Unix 时间（秒）。"),
    )
    trace: Optional[Any] = Field(
        default=None, description=_schema_txt("Trace id.", "追踪 ID。")
    )


class CommonGetApiEnvelope(BaseModel):
    """Wire JSON for common/get, common/list, common/page (often paginated + ciphertext in result)."""

    model_config = ConfigDict(extra="allow")

    advice: Optional[Any] = None
    code: Optional[int] = None
    count: Optional[int] = None
    data: Optional[Union[str, list[Any], dict[str, Any]]] = None
    errorCode: Optional[Any] = None
    field: Optional[str] = None
    hasNeedEncrypt: Optional[bool] = None
    logId: Optional[Any] = None
    msg: Optional[Any] = None
    page: Optional[int] = None
    result: Optional[Union[str, list[Any], dict[str, Any]]] = None
    sign: Optional[str] = None
    size: Optional[int] = None
    success: Optional[bool] = None
    timestamp: Optional[int] = None
    total: Optional[int] = None
    trace: Optional[Any] = None


class MemberGetApiEnvelope(BaseModel):
    """Wire JSON for member/get (minimal; encrypted data)."""

    model_config = ConfigDict(extra="allow")

    data: Optional[Union[str, list[Any], dict[str, Any]]] = None
    field: Optional[str] = None
    hasNeedEncrypt: Optional[bool] = None
    sign: Optional[str] = None
    success: Optional[bool] = None
    timestamp: Optional[int] = None
