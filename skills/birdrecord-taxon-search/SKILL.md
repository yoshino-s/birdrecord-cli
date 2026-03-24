---
name: birdrecord-taxon-search
description: >-
  Run birdrecord-cli via uvx with a pinned version: `uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli taxon …`.
  Species checklist (Chinese/Latin/English, pinyin, initials). Zheng 4 / 郑四. Use for 鸟种、物种清单、
  拉丁名、拼音、taxon checklist.
---

# Birdrecord: species checklist search (`taxon`)

## When to use

Use to **find or list species** from [观鸟记录](https://www.birdreport.cn/) using the published CLI.

## Taxonomy

Species align with the mini-program: **郑四**—*A Checklist of the Birds of China*, 4th ed. Do not assume IOC, eBird/Clements, or other checklists match `taxonid` or Chinese names.

## How to run (agents)

**Always use `uvx`** with a **pinned** `birdrecord-cli==0.1.0` (updated each release). Do **not** rely on `uv run main.py` unless the user is explicitly developing inside the repo.

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli taxon [OPTIONS]
```

Common options:

| Option | Role |
|--------|------|
| `-q` / `--query` | Case-insensitive substring on `name`, `latinname`, `englishname`, `pinyin`, `szm`. |
| `--version` | Checklist build token; omit for CLI default (must match server). |
| `--refresh` | Ignore cache and refetch. |
| `--pretty` | Pretty-print JSON. |
| `--schema` | Print request JSON Schema only (no HTTP). |

## Caching

`uvx` uses a fresh env each time; taxon cache still respects `BIRDRECORD_CACHE_DIR` and `$XDG_CACHE_HOME/birdrecord/taxon` as in `docs/CLI.zh-CN.md`.

## Workflow

1. Prefer no **`--refresh`** unless a fresh server snapshot is needed.
2. Use `-q` with a distinctive substring (Chinese name, Latin epithet, English name, or pinyin).
3. Parse JSON stdout; use **`taxonid`** when building `--body-json` for `search` (see [birdrecord-search](../birdrecord-search/SKILL.md)).

## Related

- Full flags: `docs/CLI.zh-CN.md` / `docs/CLI.md`.
