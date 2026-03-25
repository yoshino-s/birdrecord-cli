# CLI reference

Help text below is copied from the real program (`birdrecord-cli`, Click). Run `birdrecord-cli <command> --help` locally if your version differs.

## Top level

```text
Usage: birdrecord-cli [OPTIONS] COMMAND [ARGS]...

  Birdrecord mini-program API CLI.

Options:
  -h, --help  Show this message and exit.

Commands:
  cities            List cities under one province.
  provinces         List provinces for the region picker.
  report            One observation report: detail, species summary,...
  search            Chart search statistic; optional activity --taxon / --report.
  taxon             Download & cache full taxon checklist; optional -q filter.
```

## `provinces`

```text
Usage: birdrecord-cli provinces [OPTIONS]

  List provinces for the region picker.

Options:
  --schema         Print request JSON Schema only (no HTTP).
  --envelope       Include wire envelope(s) in JSON output.
  --pretty         Pretty-print JSON.
  --timeout FLOAT  HTTP timeout (seconds).  [default: 60.0]
  --no-verify      Skip TLS certificate verification.
  --base-url TEXT  API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT     Bearer token (e.g. share or JWT).  [default: share]
  -h, --help       Show this message and exit.
```

## `cities`

```text
Usage: birdrecord-cli cities [OPTIONS]

  List cities under one province.

Options:
  --province-code TEXT  6-digit province code, e.g. 110000.  [required]
  --schema              Print request JSON Schema only (no HTTP).
  --envelope            Include wire envelope(s) in JSON output.
  --pretty              Pretty-print JSON.
  --timeout FLOAT       HTTP timeout (seconds).  [default: 60.0]
  --no-verify           Skip TLS certificate verification.
  --base-url TEXT       API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT          Bearer token (e.g. share or JWT).  [default: share]
  -h, --help            Show this message and exit.
```

## `taxon`

```text
Usage: birdrecord-cli taxon [OPTIONS]

  Download the full species checklist for a build version. Results are cached
  in memory and on disk (override dir with BIRDRECORD_CACHE_DIR); --refresh
  refetches. -q filters Chinese/Latin/English name, pinyin, or initials.

Options:
  --version TEXT    Checklist version (default
                    Z4-67FA07177A544FBD96006A7CC7489D25).
  -q, --query TEXT  Case-insensitive substring on name, latinname,
                    englishname, pinyin, szm.
  --refresh         Ignore cache and refetch (updates cache for this version).
  --schema          Print request JSON Schema only (no HTTP).
  --envelope        Include wire envelope(s) in JSON output.
  --pretty          Pretty-print JSON.
  --timeout FLOAT   HTTP timeout (seconds).  [default: 60.0]
  --no-verify       Skip TLS certificate verification.
  --base-url TEXT   API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT      Bearer token (e.g. share or JWT).  [default: share]
  -h, --help        Show this message and exit.
```

## `report`

```text
Usage: birdrecord-cli report [OPTIONS]

  One observation report: detail, species summary, author profile, linked
  hotspot when set.

Options:
  --id TEXT        Report id string.  [required]
  --schema         Print result JSON Schema only (no HTTP).
  --envelope       Include wire envelope(s) in JSON output.
  --pretty         Pretty-print JSON.
  --timeout FLOAT  HTTP timeout (seconds).  [default: 60.0]
  --no-verify      Skip TLS certificate verification.
  --base-url TEXT  API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT     Bearer token (e.g. share or JWT).  [default: share]
  -h, --help       Show this message and exit.
```

## `search`

```text
Usage: birdrecord-cli search [OPTIONS]

  Chart search: per-month breakdown and rolled-up totals (--body-json). Add
  --taxon for species ranking and/or --report for paged cards; omit both to
  skip those calls.

Options:
  --taxon           Include per-species record counts for the chart month
                    (common/list).
  --report          Include paged observation report cards (common/page).
  --body-json TEXT  Unified filter JSON (UnifiedSearchRequest): chart fields plus
                    optional taxon_month, report_month, outside_type for
                    drill-down.
  --schema          Print JSON Schemas for request (UnifiedSearchRequest) and
                    response (UnifiedSearchResult) only (no HTTP).
  --envelope        Include wire envelope(s) in JSON output.
  --pretty          Pretty-print JSON.
  --timeout FLOAT   HTTP timeout (seconds).  [default: 60.0]
  --no-verify       Skip TLS certificate verification.
  --base-url TEXT   API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT      Bearer token (e.g. share or JWT).  [default: share]
  -h, --help        Show this message and exit.
```

### `search` output (JSON)

Always one shape: **`statistic`** (with **`by_month`** and **`total`** for the full `startTime`–`endTime` range), **`taxon`**, **`report`**.

- **`taxon`**: `null` if `--taxon` was not passed; otherwise an array (possibly empty) of species ranking rows.
- **`report`**: `null` if `--report` was not passed; otherwise an array of paged report cards.
- **`--envelope`**: Same keys as before under `envelope`; the merged payload is still `statistic` + `taxon` + `report` as above.

### `search` body JSON (`UnifiedSearchRequest`)

Extends chart filters (`RegionChartRequest`) with optional drill-down-only fields:

| Field | When it matters |
|-------|-----------------|
| `taxon_month` | Only with **`--taxon`**. Two-digit month (`01`–`12`, e.g. `03`): restrict the species list to records in that calendar month inside the range; empty = every month in the range. **Does not** change `statistic.by_month` / `statistic.total`. |
| `report_month` | Only with **`--report`**. Same idea for paged report cards; align with `taxon_month` when using both flags. **Does not** change chart statistics. |
| `outside_type` | Passed to activity APIs when drilling down; default `0` matches captured traffic. |

Omit `taxon_month` / `report_month` (or leave them `""`) when you only need chart statistics or full-range lists without pinning to one month.

## Shared HTTP / output flags

These appear on every subcommand that calls the API:

| Option | Role |
|--------|------|
| `--token` | Bearer token (`share` or JWT). |
| `--base-url` | API root (default `https://weixin.birdrecord.cn` — mini-program backend; [portal site](https://www.birdreport.cn/) is separate). |
| `--no-verify` | Disable TLS verification. |
| `--timeout` | HTTP timeout in seconds. |
| `--pretty` | Indent JSON on stdout. |
| `--envelope` | Include raw API envelope(s) in the printed JSON. |

## Environment variables

| Variable | Role |
|----------|------|
| `BIRDRECORD_CACHE_DIR` | Optional root for on-disk taxon checklist cache; files are under `that_dir/taxon`. |
| `XDG_CACHE_HOME` | When `BIRDRECORD_CACHE_DIR` is unset, cache path is `$XDG_CACHE_HOME/birdrecord/taxon` if this is set. |
| `BIRDRECORD_CLI_CN` | Any truthy value (not `0`, `false`, `no`, `off`) uses Chinese text in JSON Schema descriptions (e.g. `--schema`). |

---

**中文说明**：[CLI.zh-CN.md](./CLI.zh-CN.md)
