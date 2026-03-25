# 命令行参考（CLI）

程序内建的帮助文案是英文（Click）。下面 **「程序原文」** 区块来自本仓库当前版本的真实输出：`birdrecord-cli … --help`。若你本地版本不同，请以本机 `--help` 为准。

## 中文速览

### 全局（入口）

- `birdrecord-cli`：根命令，只接受 `-h` / `--help`；具体能力在子命令上。

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
| `search` | 图表检索：`--body-json` 为统一 **UnifiedSearchRequest**（图表字段 + 可选 `taxon_month` / `report_month` / `outside_type`）；`--taxon` / `--report` 控制下钻。stdout 恒为 **UnifiedSearchResult**：`statistic` + `taxon`（未传 `--taxon` 则为 `null`）+ `report`（未传 `--report` 则为 `null`）。 |

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
  --body-json TEXT  统一筛选 JSON（UnifiedSearchRequest）：图表字段 + 下钻可选
                    taxon_month、report_month、outside_type。
  --schema          仅打印请求（UnifiedSearchRequest）与响应（UnifiedSearchResult）的 JSON
                    Schema（不发起 HTTP）。
  --envelope        Include wire envelope(s) in JSON output.
  --pretty          Pretty-print JSON.
  --timeout FLOAT   HTTP timeout (seconds).  [default: 60.0]
  --no-verify       Skip TLS certificate verification.
  --base-url TEXT   API base URL.  [default: https://weixin.birdrecord.cn]
  --token TEXT      Bearer token (e.g. share or JWT).  [default: share]
  -h, --help        Show this message and exit.
```

### `search` 输出（JSON）

始终同一结构：**`statistic`**（内含完整 `startTime`–`endTime` 的 **`by_month`**、**`total`**）、**`taxon`**、**`report`**。

- **`taxon`**：未传 `--taxon` 时为 **`null`**；传了则为数组（可为空）。
- **`report`**：未传 `--report` 时为 **`null`**；传了则为数组。
- **`--envelope`**：`envelope` 内多键结构照旧；`payload` 仍为上述 `statistic` + `taxon` + `report`。

### `search` 的 `--body-json`（`UnifiedSearchRequest`）

在图表筛选（`RegionChartRequest`）之上增加**仅下钻用**字段：

| 字段 | 何时需要 |
|------|----------|
| `taxon_month` | **仅**在传 **`--taxon`** 时生效。两位月份 `01`–`12`（如 `03`）：在日期范围内只取该公历月的记录参与**鸟种列表**；留空则范围内各月都参与列表。**不改变** `statistic.by_month` / `statistic.total`（全局统计仍按完整区间）。 |
| `report_month` | **仅**在传 **`--report`** 时生效。与 `taxon_month` 同形，用于**分页记录列表**；同时下钻时建议与 `taxon_month` 对齐。**不改变**图表统计。 |
| `outside_type` | 下钻时传给 common/list、common/page；默认 `0` 与抓包一致。 |

**不需要**按月钉死列表时：不传或置空 `taxon_month` / `report_month`（仅要统计、或要全区间列表时不必填）。

---

**English**: [CLI.md](./CLI.md)
