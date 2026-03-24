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

**Pin:** `birdrecord-cli==0.1.0` (bump each release).

- **Invoke:** `uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli …`
- **Chinese or 中文 `--schema`:** `BIRDRECORD_CLI_CN=1` on the same line (truthy; not `0` / `false` / `no` / `off`).
- **No `uvx`:** `pip install 'birdrecord-cli==0.1.0'` → then `birdrecord-cli …` with the same trailing args; prefer a **venv** if you must not touch system Python.
- **Avoid** `uv run main.py` from random checkouts unless the user develops **birdrecord-cli** itself.

### `search`

```bash
# stdout { by_month, total }
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --body-json '<JSON>' [--pretty] [--envelope]

uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --taxon --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --report --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --taxon --report --body-json '<JSON>' [--pretty]
```

- **`--body-json`:** chart filter object; `{}` / omit still hits API with defaults.
- **`--schema`:** schemas only, no HTTP.

### Region prefetch

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli provinces [-q '<filter>'] [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli cities --province-code '<6-digit>' [-q '<filter>'] [--pretty]
```

## Output shape

| Mode | stdout JSON |
|------|-------------|
| No `--taxon` / `--report` | **`by_month`**, **`total`**. |
| With `--taxon` and/or `--report` | **`statistic`** + optional **`taxon`** / **`report`**. |

With **`--envelope`**, activity envelopes sit under `taxon` / `report` next to chart envelopes.

## Request fields (chart)

Coerced to **`RegionChartQueryBody`**; with activity flags, same JSON is also **`CommonActivityQueryBody`** (`taxonid` string on that path).

| Field | Notes |
|-------|--------|
| `taxonname` | Species name filter. |
| `startTime`, `endTime` | `YYYY-MM-DD`. |
| `province`, `city`, `district` | Chinese labels. |
| `pointname` | Hotspot substring. |
| `taxonid` | Int in chart (`0` = unset); string in activity APIs. |
| `serial_id`, `ctime`, `username`, `version` | As in app; `version` default `CH4`. |

Do not set `sqlid`—the client overwrites it.

## Example

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search \
  --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' \
  --pretty
```

## Related

- Taxon ids: [birdrecord-taxon-search](../birdrecord-taxon-search/SKILL.md).
- Single report: [birdrecord-report-detail](../birdrecord-report-detail/SKILL.md).
- Docs: `docs/CLI.md`, `docs/CLI.zh-CN.md`.
