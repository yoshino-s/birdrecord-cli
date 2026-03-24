---
name: birdrecord-search
description: >-
  Run birdrecord-cli via uvx with a pinned version: `uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli …`.
  Chart `search` (per-month aggregates, rolled-up totals, optional `--taxon` / `--report`).
  Before `search`: validate region with `provinces` / `cities`; if missing, tell the user; ask user to confirm params first.
  Use for observation statistics, chart filters, 记录统计、按月统计、图表检索、活动下钻. Zheng 4 / 郑四.
---

# Birdrecord: chart search (`search`)

## When to use

Use for **chart-level statistics** (same filters as the mini-program chart search). Add **`--taxon`** and/or **`--report`** only for **activity drill-down**. If neither flag is set, the CLI does **not** call those endpoints.

**Taxonomy**: `taxonname` / `taxonid` follow **郑四** (Zheng 4th ed.), same as the app.

## Region and parameters (required workflow)

1. **Validate geography before `search`**  
   Chart filters use **Chinese labels** for `province`, `city`, and `district` (see request table). Those strings must match what Birdrecord’s adcode APIs return — not free text.  
   - Run **`birdrecord-cli provinces`** (optional **`-q` / `--query`**: Chinese, pinyin, or initials) and confirm the user’s province appears (exact **`province_name`** you will put in JSON).  
   - If the search body includes **`city`**, take the province’s **`province_code`**, run **`birdrecord-cli cities --province-code <code>`** (optional **`-q`**), and confirm the city exists (**`city_name`** must match).  
   - If you use **`district`**, only proceed when you have a reliable way to match it to app data; when unsure, **do not guess** — say so and ask the user.

2. **When validation fails**  
   If **`provinces`** / **`cities`** (with or without `-q`) shows **no row** that matches what the user asked for, **stop** and **tell the user clearly** that the place does not appear in Birdrecord’s region list (or the spelling/filter does not match). **Do not** run **`search`** with unverified `province` / `city` / `district` and pretend the result is valid.

3. **User confirmation before query**  
   Before the first **`search`** call (and before heavy drill-down with **`--taxon`** / **`--report`**), **summarize the intended parameters** (date range, province/city/district as validated, species / `taxonid` if any, other filters) and **ask the user to confirm** they are correct. Only run **`search`** after confirmation (or if the user already stated them explicitly as final in the same turn and nothing ambiguous remains).

## How to run (agents)

**Always use `uvx`** with a **pinned** package version so runs stay reproducible. The pin must match the released line in this skill (`birdrecord-cli==0.1.0`); it is updated on each release.

```bash
# Statistics only: stdout is { "by_month", "total" }
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --body-json '<JSON>' [--pretty] [--envelope]

# Plus activity APIs (combine as needed)
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --taxon --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --report --body-json '<JSON>' [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search --taxon --report --body-json '<JSON>' [--pretty]
```

- **`--body-json`**: Filter object aligned with the app chart search; `{}` or omit still hits the API with coerced defaults.
- **`--schema`**: JSON Schemas only (no HTTP).
- **`BIRDRECORD_CLI_CN`**: Truthy (not `0` / `false` / `no` / `off`) → Chinese schema descriptions.

Do **not** default to `uv run main.py` from a random checkout unless the user explicitly works inside this repository; prefer **`uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli …`** as above.

**Region lookup** (same pin):

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli provinces [-q '<filter>'] [--pretty]
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli cities --province-code '<6-digit>' [-q '<filter>'] [--pretty]
```

## Output shape

| Mode | stdout JSON |
|------|-------------|
| No `--taxon` / `--report` | Top-level **`by_month`** and **`total`**. |
| With `--taxon` and/or `--report` | **`statistic`** plus optional **`taxon`** / **`report`** arrays. |

With **`--envelope`**, activity envelopes appear under `taxon` / `report` keys alongside chart envelopes.

## Request fields (chart)

Coerced to **`RegionChartQueryBody`**; with activity flags, same JSON also becomes **`CommonActivityQueryBody`** (`taxonid` string on that path).

| Field | Notes |
|-------|--------|
| `taxonname` | Species name filter. |
| `startTime`, `endTime` | `YYYY-MM-DD`. |
| `province`, `city`, `district` | Chinese labels. |
| `pointname` | Hotspot substring. |
| `taxonid` | Int in chart filters (`0` = unset); string in activity APIs. |
| `serial_id`, `ctime`, `username`, `version` | As in app traffic; `version` default `CH4`. |

Do not set `sqlid` manually — the client overwrites it per request.

## Example

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli search \
  --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' \
  --pretty
```

## Related

- Region lists (`provinces` / `cities`): same CLI; see **Region and parameters** above.
- Species ids: [birdrecord-taxon-search](../birdrecord-taxon-search/SKILL.md).
- Single report: [birdrecord-report-detail](../birdrecord-report-detail/SKILL.md).
- Docs: `docs/CLI.md`, `docs/CLI.zh-CN.md`.
