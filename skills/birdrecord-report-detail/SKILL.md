---
name: birdrecord-report-detail
description: >-
  Run birdrecord-cli via uvx with a pinned version: `uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli report --id …`.
  One observation bundle (detail, summary, author, optional hotspot). 报告详情、report id. Zheng 4 / 郑四.
---

# Birdrecord: single report bundle (`report`)

## When to use

Use when the user has a **report id** (观鸟记录 id string) and needs full detail: report payload, species summary, member profile when applicable, and point/hotspot when linked.

**Taxonomy**: **郑四** (Zheng 4th ed.) checklist.

## How to run (agents)

**Always use `uvx`** with a **pinned** `birdrecord-cli==0.1.0` (updated each release).

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli report --id '<REPORT_ID>' [--pretty] [--envelope]
```

| Option | Role |
|--------|------|
| `--id` | **Required.** Report id string. |
| `--pretty` | Pretty-print JSON. |
| `--envelope` | Include API envelope(s). |
| `--schema` | Print result JSON Schema only (no HTTP). |

Shared HTTP flags (`--token`, `--base-url`, `--timeout`, `--no-verify`) work the same; see `docs/CLI.zh-CN.md`.

## Example

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli report --id 1948816 --pretty
```

## Notes

- Output is one aggregated JSON object for “this report”.
- For chart lists / drill-down, use `search --taxon` / `search --report` via [birdrecord-search](../birdrecord-search/SKILL.md).

## Related

- Chart search: [birdrecord-search](../birdrecord-search/SKILL.md).
- Docs: `docs/CLI.zh-CN.md` / `docs/CLI.md`.
