# 命令行参考（CLI）

程序内建的帮助文案是英文（Click）。下面 **「程序原文」** 区块来自本仓库当前版本的真实输出：`birdrecord-cli … --help`（或 `uv run main.py … --help`）。若你本地版本不同，请以本机 `--help` 为准。

## 中文速览

### 全局（入口）

- `birdrecord-cli`（或 `uv run main.py`）：根命令，只接受 `-h` / `--help`；具体能力在子命令上。

### 多数子命令共用的 HTTP / 输出选项

| 选项 | 含义 |
|------|------|
| `--token` | Bearer 令牌，默认 `share`，也可传小程序 JWT。 |
| `--base-url` | API 根地址，默认 `https://weixin.birdrecord.cn`（小程序后端）；[官网入口](https://www.birdreport.cn/) 与 API 主机不同。 |
| `--no-verify` | 不校验 TLS 证书（调试用）。 |
| `--timeout` | HTTP 超时（秒），默认 `60`。 |
| `--pretty` | 将 JSON 美化输出。 |
| `--envelope` | 在 JSON 里附带接口返回的 envelope。 |
| `--schema` | 只打印 JSON Schema，不发起请求（各子命令语义略有不同，见下文原文）。 |

### 子命令摘要

| 子命令 | 作用 |
|--------|------|
| `provinces` | 省份列表（地区选择器数据）。 |
| `cities` | 某省下属城市；**必填** `--province-code`（6 位行政区划码，如 `110000`）。 |
| `taxon` | 拉取并缓存完整物种表；`--version` 指定清单版本；`-q` / `--query` 按名称/拉丁名/英文名/拼音/首字母过滤；`--refresh` 忽略缓存重拉；缓存目录可用环境变量 `BIRDRECORD_CACHE_DIR`。 |
| `report` | 单条观鸟记录聚合；**必填** `--id`（记录 id 字符串）。 |
| `search` | 图表检索统计（默认仅统计）；活动下钻用 `--taxon`（种排行）和/或 `--report`（分页记录），**不传则不查**；`--body-json` 与小程序图表筛选一致，不要手写 `sqlid`。带下钻时 stdout 为 `{ "statistic", "taxon"?, "report"? }`；仅统计时为顶层 `by_month` / `total`。 |

### 环境变量

| 变量 | 作用 |
|------|------|
| `BIRDRECORD_CACHE_DIR` | 物种表缓存根目录（可选）；实际文件在 `该目录/taxon`。 |
| `XDG_CACHE_HOME` | 未设置 `BIRDRECORD_CACHE_DIR` 时使用 `$XDG_CACHE_HOME/birdrecord/taxon`。 |
| `BIRDRECORD_CLI_CN` | 非空且非 `0` / `false` / `no` / `off` 时，JSON Schema 等描述用中文（如 `--schema`）。 |

---

## 程序原文：顶层

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

## 程序原文：`provinces`

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

## 程序原文：`cities`

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

## 程序原文：`taxon`

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

## 程序原文：`report`

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

## 程序原文：`search`

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

### `search` 输出（JSON）

- **不传 `--taxon` / `--report`**：与旧版 `search-statistic` 相同，顶层为 `by_month`、`total`。
- **传了其一或两者**：根对象含 `statistic`（上述统计嵌套在内），并按所传标志附带 `taxon` / `report` 数组。
- **`--envelope`**：统计相关 envelope 结构不变；活动接口的 envelope 在勾选对应标志时出现在 `taxon` / `report` 键下。

---

**English**: [CLI.md](./CLI.md)
