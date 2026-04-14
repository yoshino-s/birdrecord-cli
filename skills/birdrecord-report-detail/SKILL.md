---
name: birdrecord-report-detail
description: >-
  One Birdrecord observation report by id—full bundled detail (郑四). 报告详情.
---

# Birdrecord: single report bundle (`report`)

## When to use

User has a **report id** (观鸟记录 id) and needs the full bundle: report payload, species summary, member profile when present, linked hotspot.

**Taxonomy:** **郑四** (Zheng 4).

## How to run (agents)

**Pin:** `birdrecord-cli==0.1.2` (bump each release).

- **Invoke:** `uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli …`
- **Chinese or 中文 `--schema`:** `BIRDRECORD_CLI_CN=1` on the same line (truthy; not `0` / `false` / `no` / `off`).
- **No `uvx`:** `pip install 'birdrecord-cli==0.1.2'` → then `birdrecord-cli …` with the same trailing args; prefer a **venv** if you must not touch system Python.
- **Avoid** running ad-hoc copies of the repo unless the user is developing **birdrecord-cli** itself; use **`uvx`** / **`pip`** + **`birdrecord-cli`** for normal use.

### `report`

```bash
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli report --id '<REPORT_ID>' [--pretty] [--envelope]
```

| Flag | Role |
|------|------|
| `--id` | **Required.** Report id. |
| `--pretty` | Pretty JSON. |
| `--envelope` | Include API envelope(s). |
| `--schema` | Schema only, no HTTP. |

Shared HTTP flags (`--token`, `--base-url`, `--timeout`, `--no-verify`): `docs/CLI.md` / `docs/CLI.zh-CN.md`.

## Example

```bash
uvx --from 'birdrecord-cli==0.1.2' birdrecord-cli report --id 1948816 --pretty
```

## Notes

- One aggregated JSON object per report.
- Chart / drill-down: [birdrecord-search](../birdrecord-search/SKILL.md) (`search --taxon` / `--report`).

## Related

- Chart search: [birdrecord-search](../birdrecord-search/SKILL.md).
- Docs: `docs/CLI.md`, `docs/CLI.zh-CN.md`.
