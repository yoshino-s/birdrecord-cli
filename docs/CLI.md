# CLI reference

Help text below is copied from the real program (`birdrecord-cli` / `uv run main.py`, Click). Run `birdrecord-cli <command> --help` locally if your version differs.

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
  --body-json TEXT  Filter fields as JSON (chart statistic; activity drill-
                    down uses the same object, coerced per API).
  --schema          Print JSON Schemas for filters and responses only (no
                    HTTP).
  --envelope        Include wire envelope(s) in JSON output.
  --pretty          Pretty-print JSON.
  --timeout FLOAT   HTTP timeout (seconds).  [default: 60.0]
  --no-verify       Skip TLS certificate verification.
  --base-url TEXT   API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT      Bearer token (e.g. share or JWT).  [default: share]
  -h, --help        Show this message and exit.
```

### `search` output (JSON)

- **No `--taxon` / `--report`**: The printed object is the chart statistic only: top-level `by_month` and `total` (same as the former `search-statistic` command).
- **With `--taxon` and/or `--report`**: The object has `statistic` (that same chart payload nested), plus `taxon` and/or `report` arrays only for the flags you passed.
- **`--envelope`**: Statistic calls use the existing multi-key envelope; activity calls add `taxon` / `report` envelope entries when those flags are set.

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
