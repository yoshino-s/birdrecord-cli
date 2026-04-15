"""Generate Baidu report-map HTML from common/page activity rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from birdrecord_cli.models.client import ChartActivityReportRow

BAIDU_AK = "rN63jsl7xBONLrQFzzqjCx0kdds5BJa7"
UPLOAD_URL = "https://htmlbin.yoshino-s.workers.dev/create"


def _parse_location(location: str) -> tuple[float, float] | None:
    raw = (location or "").strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 2:
        return None
    try:
        lng = float(parts[0])
        lat = float(parts[1])
    except ValueError:
        return None
    if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
        return None
    return lng, lat


def build_report_map_points(rows: list[ChartActivityReportRow]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        loc = _parse_location(row.location)
        if loc is None:
            continue
        lng, lat = loc
        out.append(
            {
                "id": row.id,
                "title": row.name or row.serial_id or f"report-{row.id}",
                "username": row.username,
                "province_name": row.province_name,
                "city_name": row.city_name,
                "district_name": row.district_name,
                "point_name": row.point_name,
                "address": row.address,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "taxoncount": row.taxoncount,
                "family_count": row.family_count,
                "order_count": row.order_count,
                "lng": lng,
                "lat": lat,
            }
        )
    return out


def _html_template(region_label: str, reports: list[dict[str, Any]]) -> str:
    region_json = json.dumps(region_label, ensure_ascii=False)
    report_json = json.dumps(reports, ensure_ascii=False)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>REPORT MAP</title>
  <style>
    :root {{
      --bg: #f4f6f9;
      --card: rgba(255, 255, 255, 0.92);
      --line: #d6dde8;
      --text: #102339;
      --muted: #5f7085;
      --accent: #0c79f2;
      --accent-strong: #0058ba;
    }}

    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; height: 100%; font-family: "SF Mono", "Menlo", monospace; background: radial-gradient(circle at 20% 10%, #e7efff 0%, #f4f6f9 40%, #eef3f8 100%); color: var(--text); }}

    .layout {{
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      height: 100vh;
      gap: 10px;
      padding: 10px;
    }}

    .panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      backdrop-filter: blur(6px);
      box-shadow: 0 10px 28px rgba(16, 35, 57, 0.12);
      display: flex;
      flex-direction: column;
    }}

    .panel-header {{ padding: 14px 14px 10px; border-bottom: 1px solid var(--line); }}
    .title {{ margin: 0; font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; }}
    .meta {{ margin-top: 8px; color: var(--muted); font-size: 12px; line-height: 1.4; }}

    .summary {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; padding: 12px 14px; border-bottom: 1px solid var(--line); }}
    .stat {{ border: 1px solid var(--line); border-radius: 10px; padding: 8px; background: #fff; }}
    .stat .k {{ color: var(--muted); font-size: 11px; }}
    .stat .v {{ margin-top: 4px; font-size: 18px; font-weight: 600; }}

    .filter-wrap {{ padding: 10px 14px; border-bottom: 1px solid var(--line); }}
    .filter-wrap input {{ width: 100%; border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; font-family: inherit; font-size: 12px; outline: none; }}
    .filter-wrap input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 2px rgba(12, 121, 242, 0.15); }}

    .list {{ overflow: auto; padding: 8px; display: grid; gap: 8px; }}
    .item {{ border: 1px solid var(--line); border-radius: 10px; padding: 8px; background: #fff; cursor: pointer; transition: transform 120ms ease, border-color 120ms ease; }}
    .item:hover {{ transform: translateY(-1px); border-color: var(--accent); }}
    .item.active {{ border-color: var(--accent-strong); box-shadow: 0 0 0 2px rgba(0, 88, 186, 0.16); }}
    .item-title {{ font-size: 12px; font-weight: 700; line-height: 1.4; }}
    .item-sub {{ margin-top: 4px; font-size: 11px; color: var(--muted); line-height: 1.35; }}

    .map-wrap {{
      border: 1px solid var(--line);
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 10px 28px rgba(16, 35, 57, 0.12);
      background: #dfe7f2;
      position: relative;
      min-height: 420px;
    }}
    #map {{ width: 100%; height: 100%; min-height: 420px; }}

    .hint {{
      position: absolute;
      right: 10px;
      bottom: 10px;
      z-index: 2;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.92);
      padding: 8px 10px;
      font-size: 11px;
      color: var(--muted);
      backdrop-filter: blur(4px);
    }}

    @media (max-width: 980px) {{
      .layout {{
        grid-template-columns: 1fr;
        grid-template-rows: minmax(320px, 48vh) minmax(0, 1fr);
      }}
      .panel {{ order: 2; }}
      .map-wrap {{ order: 1; min-height: 320px; }}
      #map {{ min-height: 320px; }}
    }}
  </style>
</head>
<body>
  <div class=\"layout\">
    <aside class=\"panel\">
      <div class=\"panel-header\">
        <h1 class=\"title\">REPORT MAP</h1>
        <div class=\"meta\" id=\"regionMeta\"></div>
      </div>
      <div class=\"summary\">
        <div class=\"stat\"><div class=\"k\">Total Reports</div><div class=\"v\" id=\"totalReports\">0</div></div>
        <div class=\"stat\"><div class=\"k\">Plotted Points</div><div class=\"v\" id=\"plottedReports\">0</div></div>
      </div>
      <div class=\"filter-wrap\">
        <input id=\"filterInput\" type=\"text\" placeholder=\"filter by title / point / district\" />
      </div>
      <div class=\"list\" id=\"reportList\"></div>
    </aside>

    <section class=\"map-wrap\">
      <div id=\"map\"></div>
      <div class=\"hint\">click list item to locate marker</div>
    </section>
  </div>

  <script src=\"https://api.map.baidu.com/api?v=3.0&ak={BAIDU_AK}\"></script>
  <script>
    const REGION_LABEL = {region_json};
    const REPORTS = {report_json};

    const totalReportsEl = document.getElementById("totalReports");
    const plottedReportsEl = document.getElementById("plottedReports");
    const regionMetaEl = document.getElementById("regionMeta");
    const reportListEl = document.getElementById("reportList");
    const filterInputEl = document.getElementById("filterInput");

    const map = new BMap.Map("map");
    map.enableScrollWheelZoom(true);
    map.enableKeyboard();
    map.addControl(new BMap.NavigationControl());
    map.addControl(new BMap.ScaleControl());

    const markerById = new Map();
    const reportById = new Map(REPORTS.map((r) => [r.id, r]));
    let activeId = null;

    function escapeHtml(text) {{
      return String(text || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function itemSearchText(item) {{
      return [item.title, item.point_name, item.district_name, item.address].join(" ").toLowerCase();
    }}

    function markerPageUrl(item) {{
      const title = item.title || `report-${{item.id}}`;
      const content = [
        item.point_name || "",
        item.address || "",
        [item.province_name, item.city_name, item.district_name].filter(Boolean).join("/"),
      ].filter(Boolean).join("|");
      const params = new URLSearchParams({{
        location: `${{item.lat}},${{item.lng}}`,
        title,
        content,
        output: "html",
        src: "webapp.baidu.openAPIdemo",
      }});
      return `http://api.map.baidu.com/marker?${{params.toString()}}`;
    }}

    function openMarkerPageById(id) {{
      const item = reportById.get(id);
      if (!item) return;
      window.open(markerPageUrl(item), "_blank", "noopener,noreferrer");
    }}

    function popupHtml(item) {{
      return `
        <div style=\"font-family: Menlo, Monaco, monospace; font-size: 12px; line-height: 1.4; max-width: 280px;\">
          <div style=\"font-weight: 700; margin-bottom: 6px;\">${{escapeHtml(item.title)}}</div>
          <div><b>ID</b>: ${{item.id}}</div>
          <div><b>User</b>: ${{escapeHtml(item.username)}}</div>
          <div><b>Region</b>: ${{escapeHtml([item.province_name, item.city_name, item.district_name].filter(Boolean).join("/"))}}</div>
          <div><b>Point</b>: ${{escapeHtml(item.point_name)}}</div>
          <div><b>Address</b>: ${{escapeHtml(item.address)}}</div>
          <div><b>Time</b>: ${{escapeHtml(item.start_time)}} ~ ${{escapeHtml(item.end_time)}}</div>
          <div><b>Taxon</b>: ${{item.taxoncount}} | <b>Family</b>: ${{item.family_count}} | <b>Order</b>: ${{item.order_count}}</div>
          <div style=\"margin-top: 8px;\">
            <button type=\"button\" onclick=\"openMarkerPageById(${{item.id}})\" style=\"border: 1px solid #d6dde8; background: #0c79f2; color: #fff; border-radius: 6px; padding: 4px 8px; font-family: Menlo, Monaco, monospace; font-size: 12px; cursor: pointer;\">Open Baidu Marker</button>
          </div>
        </div>
      `;
    }}

    function setActiveItem(id) {{
      activeId = id;
      for (const el of reportListEl.querySelectorAll(".item")) {{
        if (Number(el.dataset.id) === id) {{
          el.classList.add("active");
          el.scrollIntoView({{ block: "nearest" }});
        }} else {{
          el.classList.remove("active");
        }}
      }}
    }}

    function focusReport(item) {{
      const marker = markerById.get(item.id);
      if (!marker) return;
      setActiveItem(item.id);
      map.panTo(new BMap.Point(item.lng, item.lat));
      map.openInfoWindow(new BMap.InfoWindow(popupHtml(item), {{ width: 320, title: escapeHtml(item.title) }}), marker.getPosition());
    }}

    function renderList(filtered) {{
      reportListEl.innerHTML = "";
      if (!filtered.length) {{
        const empty = document.createElement("div");
        empty.className = "item";
        empty.style.cursor = "default";
        empty.textContent = "No rows match current filter";
        reportListEl.appendChild(empty);
        return;
      }}

      for (const item of filtered) {{
        const row = document.createElement("div");
        row.className = "item";
        row.dataset.id = String(item.id);
        row.innerHTML = `
          <div class=\"item-title\">${{escapeHtml(item.title)}}</div>
          <div class=\"item-sub\">${{escapeHtml(item.point_name || item.address || "(no place)")}}</div>
          <div class=\"item-sub\">${{escapeHtml(item.start_time)}} | taxon=${{item.taxoncount}}</div>
        `;
        row.addEventListener("click", () => focusReport(item));
        reportListEl.appendChild(row);
      }}
      if (activeId !== null) {{
        setActiveItem(activeId);
      }}
    }}

    function init() {{
      totalReportsEl.textContent = String(REPORTS.length);
      plottedReportsEl.textContent = String(REPORTS.length);
      regionMetaEl.textContent = REGION_LABEL || "region metadata not provided";

      const points = [];
      for (const item of REPORTS) {{
        const point = new BMap.Point(item.lng, item.lat);
        points.push(point);

        const marker = new BMap.Marker(point);
        markerById.set(item.id, marker);
        map.addOverlay(marker);

        marker.addEventListener("click", () => {{
          setActiveItem(item.id);
          map.openInfoWindow(new BMap.InfoWindow(popupHtml(item), {{ width: 320, title: escapeHtml(item.title) }}), point);
        }});
      }}

      if (points.length) {{
        const viewport = map.getViewport(points);
        map.centerAndZoom(viewport.center, Math.max(viewport.zoom - 1, 6));
      }} else if (REGION_LABEL) {{
        const geocoder = new BMap.Geocoder();
        geocoder.getPoint(REGION_LABEL, (pt) => {{
          if (pt) {{
            map.centerAndZoom(pt, 10);
          }} else {{
            map.centerAndZoom(new BMap.Point(116.404, 39.915), 5);
          }}
        }});
      }} else {{
        map.centerAndZoom(new BMap.Point(116.404, 39.915), 5);
      }}

      renderList(REPORTS);

      filterInputEl.addEventListener("input", () => {{
        const q = filterInputEl.value.trim().toLowerCase();
        if (!q) {{
          renderList(REPORTS);
          return;
        }}
        const filtered = REPORTS.filter((r) => itemSearchText(r).includes(q));
        renderList(filtered);
      }});
    }}

    init();
  </script>
</body>
</html>
"""


def _region_label_from_rows_or_filters(
    rows: list[ChartActivityReportRow],
    *,
    province: str,
    city: str,
    district: str,
) -> str:
    from_filters = "/".join(v for v in (province, city, district) if v)
    if from_filters:
        return from_filters
    if rows:
        first = rows[0]
        return "/".join(
            v for v in (first.province_name, first.city_name, first.district_name) if v
        )
    return ""


def render_report_map_html(
    rows: list[ChartActivityReportRow],
    *,
    province: str = "",
    city: str = "",
    district: str = "",
) -> str:
    points = build_report_map_points(rows)
    region_label = _region_label_from_rows_or_filters(
        rows,
        province=province,
        city=city,
        district=district,
    )
    return _html_template(region_label=region_label, reports=points)


def write_report_map_html(
    rows: list[ChartActivityReportRow],
    *,
    output_path: str,
    province: str = "",
    city: str = "",
    district: str = "",
) -> Path:
    html = render_report_map_html(
        rows,
        province=province,
        city=city,
        district=district,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def upload_report_map_html(
    html: str,
    *,
    timeout: float = 60.0,
) -> str:
    resp = requests.post(
        UPLOAD_URL,
        json={"html": html},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    view_url = data.get("viewUrl")
    if not isinstance(view_url, str):
        raise ValueError("online upload response missing viewUrl")
    return view_url
