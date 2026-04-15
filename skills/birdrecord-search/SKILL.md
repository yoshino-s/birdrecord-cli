---
name: birdrecord-search
description: >-
  Birdrecord chart observation statistics and filters (郑四); optional activity drill-down. 记录统计、按月统计、图表检索、活动下钻.
---

# Birdrecord: chart search (`search`)

## When to use

**Chart-level statistics** (same filters as the mini-program chart search). Use **`--taxon`** / **`--report`** only for **activity drill-down**; without them, those APIs are not called.

**Taxonomy:** `taxonname` / `taxonid` = **郑四** (Zheng 4), same as the app.

## Region and parameters

1. **Before `search`:** `province` / `city` / `district` must be **exact Chinese labels** from Birdrecord adcode APIs—not free text. Run **`birdrecord-cli provinces`** (optional **`-q`**: Chinese, pinyin, initials); if JSON has **`city`**, run **`birdrecord-cli cities --province-code <code>`** (optional **`-q`**). **`district`:** only if you can match app data; else stop and ask.
2. **No matching row** in `provinces` / `cities` → **stop**; tell the user; do **not** run `search` with guessed names.
3. **Before first `search`** (and before heavy `--taxon` / `--report`): summarize filters and **get user confirmation** unless they already gave a final, unambiguous spec.

## How to run (agents)

**Pin:** `birdrecord-cli==0.1.2` (bump each release).

- **Invoke:** `uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli …`
- **Chinese or 中文 `--schema`:** `BIRDRECORD_CLI_CN=1` on the same line (truthy; not `0` / `false` / `no` / `off`).
- **No `uvx`:** `pip install 'birdrecord-cli==0.1.2'` → then `birdrecord-cli …` with the same trailing args; prefer a **venv** if you must not touch system Python.
- **Avoid** running ad-hoc copies of the repo unless the user is developing **birdrecord-cli** itself; use **`uvx`** / **`pip`** + **`birdrecord-cli`** for normal use.

### `search`

```bash
# stdout: { statistic, taxon, report } — taxon/report null when flags omitted
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search --body-json '<JSON>' [--pretty] [--envelope]

uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search --taxon --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search --report --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search --taxon --report --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search --report --report-map [<OUTPUT_HTML>|ONLINE] --body-json '<JSON>' [--pretty]
```

- **`--body-json`:** single unified object **`UnifiedSearchRequest`** (chart fields + optional `taxon_month`, `report_month`, `outside_type`). See **Month filters** below.
- **`--schema`:** prints **`request`** = `UnifiedSearchRequest`, **`response`** = `UnifiedSearchResult` (no HTTP).
- **`--report-map`:** valid only with `--report`.
  - bare `--report-map` => write local `output/report_map.html`
  - `--report-map <path>` => write local HTML to that path
  - `--report-map ONLINE` => upload to online and return URL in `report_map`

### Default agent behavior for drill-down maps

When user constraints are relatively light, default to enabling both `--report` and `--report-map`:

- Date range is within one calendar month.
- Region scope is no larger than city level (city or district filters; do not default this for province-wide or nationwide scopes).

### Region prefetch

```bash
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli provinces [-q '<filter>'] [--pretty]
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli cities --province-code '<6-digit>' [-q '<filter>'] [--pretty]
```

## Output shape (`UnifiedSearchResult`)

| Key | Meaning |
|-----|---------|
| **`statistic`** | Always set: **`by_month`** + **`total`** for the **full** `startTime`–`endTime` range. |
| **`taxon`** | **`null`** if `--taxon` was **not** passed; else array of species ranking rows (may be empty). |
| **`report`** | **`null`** if `--report` was **not** passed; else array of paged report cards. |

With **`--envelope`**, wire envelopes sit alongside; **`payload`** keeps the same three keys.

## Request body (`UnifiedSearchRequest`)

One JSON object for all modes: inherited chart fields (same names as the app / `RegionChartRequest`) plus:

| Field | Notes |
|-------|--------|
| `taxonname`, `startTime`, `endTime`, `province`, `city`, `district`, `pointname`, `username`, `serial_id`, `ctime`, `taxonid` (int), `version` | Chart filters; `taxonid` `0` = unset. |
| `taxon_month` | **Only when `--taxon` is used.** Two-digit month `01`–`12` (e.g. `03`): species list only includes records in **that calendar month** within the range; **empty** = all months in the range. **Does not** alter `statistic` (global chart stats stay full-range). |
| `report_month` | **Only when `--report` is used.** Same shape for **paged reports**; when both flags are on, **align** with `taxon_month`. **Does not** alter `statistic`. |
| `outside_type` | Drill-down only; default `0`. |

**When to pass `taxon_month` / `report_month`**

- **Omit or `""`:** User wants species list or report list across **every month** in `startTime`–`endTime`, or only needs **`statistic`** (no `--taxon` / `--report` — month fields are ignored for HTTP anyway).
- **Set (e.g. `"03"`):** User explicitly wants “only March within this multi-month window” for **`--taxon`** and/or **`--report`** rows — e.g. year-span query but list only March observations.

Do not set `sqlid`—the client overwrites it.

## Example

```bash
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli search \
  --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' \
  --pretty
```

## Related

- Taxon ids: [birdrecord-taxon-search](../birdrecord-taxon-search/SKILL.md).
- Single report: [birdrecord-report-detail](../birdrecord-report-detail/SKILL.md).
- Docs: `docs/CLI.md`, `docs/CLI.zh-CN.md`.
