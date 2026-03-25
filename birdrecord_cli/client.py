"""Typed Birdrecord HTTP client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import (
    Any,
    Generic,
    Mapping,
    Optional,
    TypeAlias,
    TypeVar,
)

import httpx
from pydantic import BaseModel

from birdrecord_cli.constants import (
    BASE_URL,
    DEFAULT_REFERER,
    DEFAULT_TAXON_VERSION,
    DEFAULT_USER_AGENT,
)
from birdrecord_cli.crypto import parse_encrypted_envelope
from birdrecord_cli.models.client import (
    AdcodeCityRequest,
    AdcodeProvinceRequest,
    ChartActivityReportRow,
    ChartActivityTaxonRow,
    COMMON_GET_SQLID_CHART_QUERY_REPORT,
    COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
    ChartQueryReportPayload,
    ChartRecordSummaryPayload,
    ChartReportMonthRow,
    ChartStatisticsReportsRequest,
    ChartStatisticsTaxonRequest,
    ChartTaxonStatisticsRow,
    CityRow,
    CommonChartBundleFetch,
    CommonChartBundleResult,
    CommonGetApiEnvelope,
    CommonListActivityTaxonRequest,
    CommonPageActivityRequest,
    DubiousAccurateCounts,
    MemberGetApiEnvelope,
    MemberGetRequest,
    MemberProfilePayload,
    MonthSearchEntry,
    PointDetailPayload,
    PointGetRequest,
    ProvinceRow,
    RecordSummaryPayload,
    RecordSummaryRequest,
    RegionChartRequest,
    ReportBundleFetch,
    ReportBundleResult,
    ReportDetailPayload,
    ReportGetRequest,
    SearchStatisticFetch,
    SearchStatisticResult,
    StandardApiEnvelope,
    TaxonMonthSlice,
    TaxonRow,
    TaxonSearchRequest,
    build_common_get_chart_payload,
    coerce_region_chart_request,
    filter_taxon_rows_by_query,
)

EnvelopeT = TypeVar("EnvelopeT", bound=BaseModel)
PayloadT = TypeVar("PayloadT")
DictPayloadT = TypeVar("DictPayloadT", bound=BaseModel)
RowModelT = TypeVar("RowModelT", bound=BaseModel)


class BirdrecordApiError(Exception):
    def __init__(
        self, message: str, *, code: Any = None, envelope: Optional[dict] = None
    ):
        super().__init__(message)
        self.code = code
        self.envelope = envelope


def _require_list(inner: Any, err_msg: str, envelope: dict[str, Any]) -> list[Any]:
    if not isinstance(inner, list):
        raise BirdrecordApiError(err_msg, envelope=envelope)
    return inner


def _require_dict(inner: Any, err_msg: str, envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(inner, dict):
        raise BirdrecordApiError(err_msg, envelope=envelope)
    return inner


def _request_body_mapping(body: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
    return body.model_dump() if isinstance(body, BaseModel) else dict(body)


def _check_standard_envelope(envelope: dict) -> None:
    code = envelope.get("code")
    if code is not None and code != 0:
        msg = envelope.get("msg") or envelope.get("errorCode") or "API error"
        raise BirdrecordApiError(str(msg), code=code, envelope=envelope)


def _check_common_envelope(envelope: dict) -> None:
    if envelope.get("success") is False:
        msg = envelope.get("msg") or "API error"
        raise BirdrecordApiError(str(msg), code=envelope.get("code"), envelope=envelope)
    code = envelope.get("code")
    if code is not None and code != 0:
        msg = envelope.get("msg") or envelope.get("errorCode") or "API error"
        raise BirdrecordApiError(str(msg), code=code, envelope=envelope)


def _check_member_get_envelope(envelope: dict) -> None:
    if envelope.get("success") is False:
        msg = envelope.get("msg") or "API error"
        raise BirdrecordApiError(str(msg), code=envelope.get("code"), envelope=envelope)


@dataclass(frozen=True)
class BirdrecordCall(Generic[EnvelopeT, PayloadT]):
    envelope: EnvelopeT
    payload: PayloadT


def _taxon_call_for_emit(
    env_dump: dict[str, Any],
    full_rows: list[TaxonRow],
    *,
    query: str | None,
) -> BirdrecordCall[StandardApiEnvelope, list[TaxonRow]]:
    filtered = filter_taxon_rows_by_query(full_rows, query)
    env_d = dict(env_dump)
    if (query or "").strip():
        env_d["count"] = len(filtered)
    return BirdrecordCall(
        envelope=StandardApiEnvelope.model_validate(env_d),
        payload=filtered,
    )


def _standard_list_call_after_query_filter[T](
    raw: BirdrecordCall[StandardApiEnvelope, list[T]],
    filtered: list[T],
    *,
    query: str | None,
) -> BirdrecordCall[StandardApiEnvelope, list[T]]:
    env_d = dict(raw.envelope.model_dump())
    if (query or "").strip():
        env_d["count"] = len(filtered)
    return BirdrecordCall(
        envelope=StandardApiEnvelope.model_validate(env_d),
        payload=filtered,
    )


@dataclass
class BirdrecordResponse:
    """Raw envelope dict + extracted payload (untyped)."""

    envelope: dict[str, Any]
    payload: Any

    @property
    def code(self) -> Any:
        return self.envelope.get("code")


ChartStatisticsPayload: TypeAlias = list[ChartReportMonthRow]
ChartTaxonStatisticsPayload: TypeAlias = list[ChartTaxonStatisticsRow]
ChartActivityTaxonListPayload: TypeAlias = list[ChartActivityTaxonRow]
ChartActivityReportListPayload: TypeAlias = list[ChartActivityReportRow]

MEMBER_GET_PATH = "/api/weixin/member/get"
POINT_GET_PATH = "/api/weixin/point/get"
RECORD_SUMMARY_PATH = "/api/weixin/record/summary"
CHART_STATISTICS_REPORTS_PATH = "/api/weixin/chart/record/statistics/reports"
CHART_STATISTICS_TAXON_PATH = "/api/weixin/chart/record/statistics/taxon"


class BirdrecordClient:
    def __init__(
        self,
        token: str = "share",
        *,
        base_url: str = BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        referer: str = DEFAULT_REFERER,
        verify: bool = True,
        timeout: float = 60.0,
    ) -> None:
        self._token = token
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            verify=verify,
            headers={
                "User-Agent": user_agent,
                "Content-Type": "application/json",
                "xweb_xhr": "1",
                "Referer": referer,
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> BirdrecordClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def _headers(self) -> dict[str, str]:
        return {
            "timestamp": str(int(time.time() * 1000)),
            "token": self._token,
        }

    def post(
        self, path: str, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST JSON; raw envelope + parsed payload."""
        path = path if path.startswith("/") else f"/{path}"
        r = self._client.post(path, json=dict(body), headers=self._headers())
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_standard_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def _post_common(
        self, subpath: str, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST common/{subpath}; validates common envelope."""
        sub = subpath.removeprefix("/")
        path = f"/api/weixin/common/{sub}"
        r = self._client.post(path, json=dict(body), headers=self._headers())
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_common_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def post_common_get(
        self, body: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST common/get."""
        return self._post_common("get", body, check=check)

    def _post_member_get_form(
        self, form: Mapping[str, Any], *, check: bool = True
    ) -> BirdrecordResponse:
        """POST member/get (form body)."""
        path = MEMBER_GET_PATH
        headers = {
            **self._headers(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r = self._client.post(path, data=dict(form), headers=headers)
        r.raise_for_status()
        envelope = r.json()
        if not isinstance(envelope, dict):
            raise BirdrecordApiError("Expected JSON object body", envelope=None)
        if check:
            _check_member_get_envelope(envelope)
        payload = parse_encrypted_envelope(envelope)
        return BirdrecordResponse(envelope=envelope, payload=payload)

    def _post_standard_list(
        self,
        path: str,
        body: dict[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, list[RowModelT]]:
        raw = self.post(path, body, check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    def _post_standard_dict(
        self,
        path: str,
        body: dict[str, Any],
        *,
        payload_model: type[DictPayloadT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, DictPayloadT]:
        raw = self.post(path, body, check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(raw.payload, err_msg, raw.envelope)
        parsed = payload_model.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def _post_common_list(
        self,
        subpath: str,
        body: dict[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[CommonGetApiEnvelope, list[RowModelT]]:
        raw = self._post_common(subpath, body, check=True)
        env = CommonGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    def _post_common_get_chart(
        self,
        filters: RegionChartRequest,
        *,
        sqlid: str,
        err_msg: str,
        payload_model: type[DictPayloadT],
    ) -> BirdrecordCall[CommonGetApiEnvelope, DictPayloadT]:
        payload = build_common_get_chart_payload(filters, sqlid=sqlid)
        raw = self.post_common_get(payload, check=True)
        env = CommonGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(raw.payload, err_msg, raw.envelope)
        parsed = payload_model.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def _post_chart_statistics_rows(
        self,
        path: str,
        payload: Mapping[str, Any],
        *,
        row_model: type[RowModelT],
        err_msg: str,
    ) -> BirdrecordCall[StandardApiEnvelope, list[RowModelT]]:
        raw = self.post(path, dict(payload), check=True)
        env = StandardApiEnvelope.model_validate(raw.envelope)
        inner = _require_list(raw.payload, err_msg, raw.envelope)
        rows = [row_model.model_validate(x) for x in inner]
        return BirdrecordCall(envelope=env, payload=rows)

    # --- typed endpoints ---

    def adcode_provinces(
        self,
    ) -> BirdrecordCall[StandardApiEnvelope, list[ProvinceRow]]:
        return self._post_standard_list(
            "/api/weixin/adcode/province",
            _request_body_mapping(AdcodeProvinceRequest()),
            row_model=ProvinceRow,
            err_msg="Expected list payload for provinces",
        )

    def adcode_cities(
        self, province_code: str
    ) -> BirdrecordCall[StandardApiEnvelope, list[CityRow]]:
        return self._post_standard_list(
            "/api/weixin/adcode/city",
            _request_body_mapping(AdcodeCityRequest(province_code=province_code)),
            row_model=CityRow,
            err_msg="Expected list payload for cities",
        )

    def taxon_search(
        self, version: Optional[str] = None
    ) -> BirdrecordCall[StandardApiEnvelope, list[TaxonRow]]:
        return self._post_standard_list(
            "/api/weixin/taxon/search",
            _request_body_mapping(
                TaxonSearchRequest(version=version or DEFAULT_TAXON_VERSION)
            ),
            row_model=TaxonRow,
            err_msg="Expected list payload for taxon search",
        )

    def chart_record_statistics_reports(
        self, body: ChartStatisticsReportsRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[StandardApiEnvelope, ChartStatisticsPayload]:
        if body is None:
            body = ChartStatisticsReportsRequest()
        return self._post_chart_statistics_rows(
            CHART_STATISTICS_REPORTS_PATH,
            _request_body_mapping(body),
            row_model=ChartReportMonthRow,
            err_msg="Expected list payload for statistics reports",
        )

    def chart_record_statistics_taxon(
        self,
        body: ChartStatisticsTaxonRequest
        | ChartStatisticsReportsRequest
        | Mapping[str, Any]
        | None = None,
    ) -> BirdrecordCall[StandardApiEnvelope, ChartTaxonStatisticsPayload]:
        if body is None:
            body = ChartStatisticsTaxonRequest()
        return self._post_chart_statistics_rows(
            CHART_STATISTICS_TAXON_PATH,
            _request_body_mapping(body),
            row_model=ChartTaxonStatisticsRow,
            err_msg="Expected list payload for chart/record/statistics/taxon",
        )

    def common_get_chart_summary(
        self, body: RegionChartRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartRecordSummaryPayload]:
        return self._post_common_get_chart(
            coerce_region_chart_request(body),
            sqlid=COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
            err_msg="Expected dict payload for chart summary",
            payload_model=ChartRecordSummaryPayload,
        )

    def common_get_chart_query_report(
        self, body: RegionChartRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartQueryReportPayload]:
        return self._post_common_get_chart(
            coerce_region_chart_request(body),
            sqlid=COMMON_GET_SQLID_CHART_QUERY_REPORT,
            err_msg="Expected dict payload for chart query report",
            payload_model=ChartQueryReportPayload,
        )

    def fetch_common_chart_bundle(
        self,
        body: RegionChartRequest | Mapping[str, Any] | None = None,
        *,
        collect_envelopes: bool = False,
    ) -> CommonChartBundleFetch:
        """Two common/get calls (both chart sqlids) for one filter."""
        filters = coerce_region_chart_request(body)
        c_summary = self._post_common_get_chart(
            filters,
            sqlid=COMMON_GET_SQLID_CHART_RECORD_SUMMARY,
            err_msg="Expected dict payload for chart summary",
            payload_model=ChartRecordSummaryPayload,
        )
        c_query = self._post_common_get_chart(
            filters,
            sqlid=COMMON_GET_SQLID_CHART_QUERY_REPORT,
            err_msg="Expected dict payload for chart query report",
            payload_model=ChartQueryReportPayload,
        )
        bundle = CommonChartBundleResult(
            summary=c_summary.payload, query_report=c_query.payload
        )
        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes[COMMON_GET_SQLID_CHART_RECORD_SUMMARY] = (
                c_summary.envelope.model_dump()
            )
            envelopes[COMMON_GET_SQLID_CHART_QUERY_REPORT] = (
                c_query.envelope.model_dump()
            )
        return CommonChartBundleFetch(bundle=bundle, envelopes=envelopes)

    def fetch_search_statistic(
        self,
        body: RegionChartRequest | Mapping[str, Any] | None = None,
        *,
        collect_envelopes: bool = False,
    ) -> SearchStatisticFetch:
        """Chart reports + taxon + common/get pair → ``by_month`` + ``total``."""
        filters = coerce_region_chart_request(body)
        fd = filters.model_dump()
        chart_body = ChartStatisticsReportsRequest.model_validate(fd)
        taxon_body = ChartStatisticsTaxonRequest.model_validate(fd)
        rep_call = self.chart_record_statistics_reports(chart_body)
        tax_call = self.chart_record_statistics_taxon(taxon_body)
        common_fetch = self.fetch_common_chart_bundle(
            filters, collect_envelopes=collect_envelopes
        )
        grouped = common_fetch.bundle.as_grouped()
        reports_by_m = {str(int(r.taxon_month)): r for r in rep_call.payload}
        taxon_by_m = {str(int(r.taxon_month)): r for r in tax_call.payload}
        month_keys = sorted(set(reports_by_m) | set(taxon_by_m), key=lambda k: int(k))
        by_month: dict[str, MonthSearchEntry] = {}
        for m in month_keys:
            rr = reports_by_m.get(m)
            tt = taxon_by_m.get(m)
            by_month[m] = MonthSearchEntry(
                report=DubiousAccurateCounts(
                    dubious=rr.report_num_dubious if rr else 0,
                    accurate=rr.report_num if rr else 0,
                ),
                taxon=TaxonMonthSlice(
                    dubious=tt.taxon_num_dubious if tt else 0,
                    accurate=tt.taxon_num if tt else 0,
                ),
            )
        result = SearchStatisticResult(by_month=by_month, total=grouped)
        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes["chart_record_statistics_reports"] = (
                rep_call.envelope.model_dump()
            )
            envelopes["chart_record_statistics_taxon"] = tax_call.envelope.model_dump()
            envelopes["common_get"] = dict(common_fetch.envelopes)
        return SearchStatisticFetch(result=result, envelopes=envelopes)

    def common_list_activity_taxon(
        self, body: CommonListActivityTaxonRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartActivityTaxonListPayload]:
        if body is None:
            body = CommonListActivityTaxonRequest()
        return self._post_common_list(
            "list",
            _request_body_mapping(body),
            row_model=ChartActivityTaxonRow,
            err_msg="Expected list payload for common/list activity taxon",
        )

    def common_page_activity(
        self, body: CommonPageActivityRequest | Mapping[str, Any] | None = None
    ) -> BirdrecordCall[CommonGetApiEnvelope, ChartActivityReportListPayload]:
        if body is None:
            body = CommonPageActivityRequest()
        return self._post_common_list(
            "page",
            _request_body_mapping(body),
            row_model=ChartActivityReportRow,
            err_msg="Expected list payload for common/page activity",
        )

    def reports_get(
        self,
        body: ReportGetRequest | Mapping[str, Any] | None = None,
        *,
        report_id: Optional[str] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, ReportDetailPayload]:
        if body is None:
            if report_id is None:
                body = ReportGetRequest(id="1948816")
            else:
                body = ReportGetRequest(id=str(report_id))
        return self._post_standard_dict(
            "/api/weixin/reports/get",
            _request_body_mapping(body),
            payload_model=ReportDetailPayload,
            err_msg="Expected dict payload for reports/get",
        )

    def member_get(
        self,
        body: MemberGetRequest | Mapping[str, Any] | None = None,
        *,
        userid: Optional[int] = None,
    ) -> BirdrecordCall[MemberGetApiEnvelope, MemberProfilePayload]:
        if body is None:
            uid = 89963 if userid is None else userid
            body = MemberGetRequest(userid=uid)
        form = _request_body_mapping(body)
        raw = self._post_member_get_form(form, check=True)
        env = MemberGetApiEnvelope.model_validate(raw.envelope)
        inner = _require_dict(
            raw.payload, "Expected dict payload for member/get", raw.envelope
        )
        parsed = MemberProfilePayload.model_validate(inner)
        return BirdrecordCall(envelope=env, payload=parsed)

    def point_get(
        self,
        body: PointGetRequest | Mapping[str, Any] | None = None,
        *,
        point_id: Optional[int] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, PointDetailPayload]:
        if body is None:
            pid = 125887 if point_id is None else point_id
            body = PointGetRequest(point_id=pid)
        return self._post_standard_dict(
            POINT_GET_PATH,
            _request_body_mapping(body),
            payload_model=PointDetailPayload,
            err_msg="Expected dict payload for point/get",
        )

    def record_summary(
        self,
        body: RecordSummaryRequest | Mapping[str, Any] | None = None,
        *,
        activity_id: Optional[str] = None,
    ) -> BirdrecordCall[StandardApiEnvelope, RecordSummaryPayload]:
        if body is None:
            aid = "1948816" if activity_id is None else str(activity_id)
            body = RecordSummaryRequest(activity_id=aid)
        return self._post_standard_dict(
            RECORD_SUMMARY_PATH,
            _request_body_mapping(body),
            payload_model=RecordSummaryPayload,
            err_msg="Expected dict payload for record/summary",
        )

    def fetch_report_bundle(
        self,
        report_id: str,
        *,
        member_id: Optional[int] = None,
        collect_envelopes: bool = False,
    ) -> ReportBundleFetch:
        """reports/get + record/summary + member/get (if owner) + point/get (if point).

        When ``member_id`` is set, use it for member/get instead of ``report.member_id``.
        """
        rid = str(report_id)
        rg = self.reports_get(report_id=rid)
        rep = rg.payload
        mid_eff = int(member_id) if member_id is not None else int(rep.member_id)

        rs = self.record_summary(activity_id=rid)

        mg_call: Optional[
            BirdrecordCall[MemberGetApiEnvelope, MemberProfilePayload]
        ] = None
        member_payload: Optional[MemberProfilePayload] = None
        if mid_eff:
            mg_call = self.member_get(userid=mid_eff)
            member_payload = mg_call.payload

        pg_call: Optional[BirdrecordCall[StandardApiEnvelope, PointDetailPayload]] = (
            None
        )
        point_payload: Optional[PointDetailPayload] = None
        pid = int(rep.point_id) if getattr(rep, "point_id", 0) else 0
        if pid:
            pg_call = self.point_get(point_id=pid)
            point_payload = pg_call.payload

        bundle = ReportBundleResult(
            report_id=rid,
            report=rep,
            record_summary=rs.payload,
            member=member_payload,
            point=point_payload,
        )

        envelopes: dict[str, Any] = {}
        if collect_envelopes:
            envelopes["reports_get"] = rg.envelope.model_dump()
            envelopes["record_summary"] = rs.envelope.model_dump()
            if mg_call is not None:
                envelopes["member_get"] = mg_call.envelope.model_dump()
            if pg_call is not None:
                envelopes["point_get"] = pg_call.envelope.model_dump()

        return ReportBundleFetch(bundle=bundle, envelopes=envelopes)
