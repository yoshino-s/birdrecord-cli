"""
Integration-style tests against the live API.

Run: uv run pytest tests/test_birdrecord_client.py -v
TLS: set verify=False on the client if certificate verification fails locally.
"""

from __future__ import annotations

import pytest

from birdrecord_cli.client import BirdrecordClient
from birdrecord_cli.constants import DEFAULT_TAXON_VERSION
from birdrecord_cli.models import (
    AdcodeCityRequest,
    AdcodeProvinceRequest,
    ChartActivityReportRow,
    ChartActivityTaxonRow,
    CityRow,
    CommonChartBundleGrouped,
    CommonListActivityTaxonRequest,
    CommonPageActivityRequest,
    DubiousAccurateCounts,
    MemberProfilePayload,
    MonthSearchEntry,
    ProvinceRow,
    RegionChartRequest,
    ReportBundleResult,
    ReportDetailPayload,
    ReportGetRequest,
    RecordSummaryPayload,
    RecordSummaryRequest,
    SearchStatisticResult,
    StandardApiEnvelope,
    TaxonMonthSlice,
    TaxonRow,
    TaxonSearchRequest,
    UnifiedSearchRequest,
    _load_taxon_search_disk,
    _save_taxon_search_disk,
    build_common_list_taxon_request,
    build_common_page_activity_request,
    coerce_common_activity_request,
    coerce_unified_search_request,
    filter_region_rows_by_query,
    filter_taxon_rows_by_query,
    unified_search_to_common_activity,
    unified_search_to_region_chart,
)


@pytest.fixture
def client() -> BirdrecordClient:
    return BirdrecordClient(token="share", verify=False)


def test_common_activity_body_builds_sqlid_requests():
    raw = {
        "taxonname": "",
        "startTime": "2026-03-22",
        "endTime": "2026-03-24",
        "province": "北京市",
        "taxon_month": "03",
        "outside_type": 0,
    }
    base = coerce_common_activity_request(raw)
    lt = build_common_list_taxon_request(base)
    assert lt.sqlid == "searchChartActivityTaxon"
    pg = build_common_page_activity_request(base)
    assert pg.sqlid == "searchChartActivity"
    assert pg.start == 1
    assert pg.limit == 50
    assert pg.report_month == ""
    pg2 = build_common_page_activity_request(base, report_month="03")
    assert pg2.report_month == "03"


def test_unified_search_request_month_fields() -> None:
    u = coerce_unified_search_request(
        {
            "startTime": "2025-01-01",
            "endTime": "2026-12-31",
            "province": "河北省",
            "taxon_month": "03",
            "report_month": "03",
            "taxonid": 4148,
        }
    )
    assert isinstance(u, UnifiedSearchRequest)
    rc = unified_search_to_region_chart(u)
    assert "taxon_month" not in rc.model_dump()
    assert rc.taxonid == 4148
    act = unified_search_to_common_activity(u)
    assert act.taxon_month == "03"
    assert act.taxonid == "4148"
    assert "report_month" not in act.model_dump()


def test_request_models_serialize():
    assert AdcodeProvinceRequest().model_dump() == {}
    assert AdcodeCityRequest(province_code="130000").model_dump() == {
        "province_code": "130000"
    }
    assert TaxonSearchRequest().version == DEFAULT_TAXON_VERSION
    assert "version" in TaxonSearchRequest().model_dump()


def test_adcode_provinces(client: BirdrecordClient) -> None:
    out = client.adcode_provinces()
    assert isinstance(out.envelope, StandardApiEnvelope)
    assert out.envelope.code == 0
    assert len(out.payload) >= 1
    assert out.payload[0].province_code
    assert out.payload[0].province_name


def test_adcode_cities(client: BirdrecordClient) -> None:
    out = client.adcode_cities("110000")
    assert out.envelope.code == 0
    assert len(out.payload) >= 1
    assert out.payload[0].city_code.startswith("110")


def test_taxon_disk_cache_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("BIRDRECORD_CACHE_DIR", str(tmp_path))

    rows = [
        TaxonRow(
            id=1,
            name="大山雀",
            latinname="Parus minor",
        ),
    ]
    env = {"code": 0, "count": 1}
    _save_taxon_search_disk("test-version-xyz", env, rows)
    loaded = _load_taxon_search_disk("test-version-xyz")
    assert loaded is not None
    env2, rows2 = loaded
    assert env2["code"] == 0
    assert len(rows2) == 1
    assert rows2[0].id == 1
    assert rows2[0].name == "大山雀"


def test_filter_taxon_rows_by_query() -> None:
    rows = [
        TaxonRow(
            id=1,
            name="大山雀",
            latinname="Parus minor",
            englishname="",
            pinyin="dashanque",
            szm="DSQ",
        ),
        TaxonRow(
            id=2,
            name="麻雀",
            latinname="Passer montanus",
            englishname="Eurasian Tree Sparrow",
            pinyin="maque",
            szm="MQ",
        ),
    ]
    assert len(filter_taxon_rows_by_query(rows, None)) == 2
    assert len(filter_taxon_rows_by_query(rows, "")) == 2
    assert len(filter_taxon_rows_by_query(rows, "  ")) == 2
    assert {r.id for r in filter_taxon_rows_by_query(rows, "parus")} == {1}
    assert {r.id for r in filter_taxon_rows_by_query(rows, "PASSER")} == {2}
    assert {r.id for r in filter_taxon_rows_by_query(rows, "eurasian")} == {2}
    assert {r.id for r in filter_taxon_rows_by_query(rows, "maque")} == {2}
    assert {r.id for r in filter_taxon_rows_by_query(rows, "mq")} == {2}
    assert {r.id for r in filter_taxon_rows_by_query(rows, "大山")} == {1}
    assert len(filter_taxon_rows_by_query(rows, "zzz")) == 0


def test_filter_region_rows_by_query() -> None:
    provinces = [
        ProvinceRow(province_code="110000", province_name="北京市"),
        ProvinceRow(province_code="130000", province_name="河北省"),
    ]
    assert (
        len(filter_region_rows_by_query(provinces, None, label_attr="province_name"))
        == 2
    )
    assert (
        len(filter_region_rows_by_query(provinces, "", label_attr="province_name")) == 2
    )
    assert (
        len(filter_region_rows_by_query(provinces, "  ", label_attr="province_name"))
        == 2
    )
    assert {
        r.province_code
        for r in filter_region_rows_by_query(
            provinces, "河北", label_attr="province_name"
        )
    } == {"130000"}
    assert {
        r.province_code
        for r in filter_region_rows_by_query(
            provinces, "hebei", label_attr="province_name"
        )
    } == {"130000"}
    assert {
        r.province_code
        for r in filter_region_rows_by_query(
            provinces, "HEBEI", label_attr="province_name"
        )
    } == {"130000"}
    assert {
        r.province_code
        for r in filter_region_rows_by_query(
            provinces, "hb", label_attr="province_name"
        )
    } == {"130000"}
    cities = [
        CityRow(city_code="110100", city_name="市辖区"),
        CityRow(city_code="110200", city_name="县"),
    ]
    assert len(filter_region_rows_by_query(cities, "辖区", label_attr="city_name")) == 1
    assert (
        len(filter_region_rows_by_query(cities, "xiaqu", label_attr="city_name")) == 1
    )
    assert (
        len(filter_region_rows_by_query(provinces, "zzz", label_attr="province_name"))
        == 0
    )


def test_taxon_search_uses_default_version(client: BirdrecordClient) -> None:
    out_default = client.taxon_search()
    assert len(out_default.payload) >= 100
    assert out_default.payload[0].id is not None

    out_explicit = client.taxon_search(version=DEFAULT_TAXON_VERSION)
    assert len(out_explicit.payload) == len(out_default.payload)


def test_fetch_search_statistic(client: BirdrecordClient) -> None:
    body = RegionChartRequest(
        taxonname="",
        startTime="2026-02-24",
        endTime="2026-03-24",
        province="河北省",
        city="石家庄市",
        district="井陉矿区",
        pointname="园",
        username="user",
        serial_id="1111",
        ctime="2026-03-24",
        taxonid=4148,
        version="CH4",
    )
    fetch = client.fetch_search_statistic(body, collect_envelopes=True)
    assert isinstance(fetch.result, SearchStatisticResult)
    assert isinstance(fetch.result.total, CommonChartBundleGrouped)
    for _k, v in fetch.result.by_month.items():
        assert isinstance(v, MonthSearchEntry)
        assert isinstance(v.report, DubiousAccurateCounts)
        assert isinstance(v.taxon, TaxonMonthSlice)
    assert "chart_record_statistics_reports" in fetch.envelopes
    assert "chart_record_statistics_taxon" in fetch.envelopes
    assert "common_get" in fetch.envelopes
    cg = fetch.envelopes["common_get"]
    assert "selectChartRecordSummary" in cg
    assert "selectchartQueryReport" in cg


def test_common_list_activity_taxon(client: BirdrecordClient) -> None:
    body = CommonListActivityTaxonRequest(
        taxonname="",
        startTime="2026-03-22",
        endTime="2026-03-24",
        province="北京市",
        city="",
        district="",
        pointname="",
        username="",
        serial_id="",
        ctime="",
        taxonid="",
        version="CH4",
        taxon_month="03",
        outside_type=0,
    )
    out = client.common_list_activity_taxon(body)
    assert out.envelope.success is True
    assert len(out.payload) >= 1
    assert isinstance(out.payload[0], ChartActivityTaxonRow)
    assert out.payload[0].taxon_id is not None


def test_common_page_activity(client: BirdrecordClient) -> None:
    body = CommonPageActivityRequest(
        start=1,
        limit=15,
        taxonname="",
        startTime="2026-03-22",
        endTime="2026-03-24",
        province="北京市",
        city="",
        district="",
        pointname="",
        username="",
        serial_id="",
        ctime="",
        taxonid="",
        version="CH4",
        taxon_month="03",
        outside_type=0,
        report_month="03",
    )
    out = client.common_page_activity(body)
    assert out.envelope.success is True
    assert len(out.payload) >= 1
    assert isinstance(out.payload[0], ChartActivityReportRow)
    assert out.payload[0].id is not None


def test_reports_get(client: BirdrecordClient) -> None:
    out = client.reports_get(ReportGetRequest(id="1948816"))
    assert out.envelope.code == 0
    assert isinstance(out.payload, ReportDetailPayload)
    assert out.payload.id == 1948816
    assert out.payload.serial_id


def test_record_summary(client: BirdrecordClient) -> None:
    out = client.record_summary(RecordSummaryRequest(activity_id="1948816"))
    assert out.envelope.code == 0
    assert isinstance(out.payload, RecordSummaryPayload)
    assert out.payload.taxon_count >= 0


def test_fetch_report_bundle(client: BirdrecordClient) -> None:
    fetch = client.fetch_report_bundle("1948816", collect_envelopes=True)
    assert isinstance(fetch.bundle, ReportBundleResult)
    assert fetch.bundle.report_id == "1948816"
    assert fetch.bundle.report.id == 1948816
    assert isinstance(fetch.bundle.record_summary, RecordSummaryPayload)
    assert "reports_get" in fetch.envelopes
    assert "record_summary" in fetch.envelopes
    if fetch.bundle.report.member_id:
        assert fetch.bundle.member is not None
        assert isinstance(fetch.bundle.member, MemberProfilePayload)
        assert fetch.bundle.member.id == fetch.bundle.report.member_id
        assert "member_get" in fetch.envelopes
    if fetch.bundle.point is not None:
        assert "point_get" in fetch.envelopes
