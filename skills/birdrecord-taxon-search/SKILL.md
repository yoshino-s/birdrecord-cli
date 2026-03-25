---
name: birdrecord-taxon-search
description: >-
  Birdrecord species checklist lookup and taxonid resolution (郑四). 鸟种、物种清单、taxon.
---

# Birdrecord: species checklist search (`taxon`)

## When to use

**Find or list species** for Birdrecord via the published CLI.

## Taxonomy

**郑四**—*A Checklist of the Birds of China*, 4th ed. Do not assume IOC, eBird/Clements, etc. match `taxonid` or Chinese names.

## How to run (agents)

**Pin:** `birdrecord-cli==0.1.1` (bump each release).

- **Invoke:** `uvx --from 'birdrecord-cli==0.1.1' birdrecord-cli …`
- **Chinese or 中文 `--schema`:** `BIRDRECORD_CLI_CN=1` on the same line (truthy; not `0` / `false` / `no` / `off`).
- **No `uvx`:** `pip install 'birdrecord-cli==0.1.1'` → then `birdrecord-cli …` with the same trailing args; prefer a **venv** if you must not touch system Python.
- **Avoid** ad-hoc repo checkouts unless developing **birdrecord-cli**; prefer **`uvx`** / **`pip`** + **`birdrecord-cli`**.

### `taxon`

```bash
uvx --from 'birdrecord-cli==0.1.1' birdrecord-cli taxon [OPTIONS]
```

| Flag | Role |
|------|------|
| `-q` / `--query` | Case-insensitive substring on `name`, `latinname`, `englishname`, `pinyin`, `szm`. |
| `--version` | Checklist token; omit = CLI default (must match server). |
| `--refresh` | Bypass cache, refetch. |
| `--pretty` | Pretty JSON. |
| `--schema` | Request schema only, no HTTP. |

## Caching

Each `uvx` run is a clean env; cache paths: `BIRDRECORD_CACHE_DIR`, else `$XDG_CACHE_HOME/birdrecord/taxon`, else `~/.cache/birdrecord/taxon` (`docs/CLI*.md`).

## Workflow

1. Skip **`--refresh`** unless you need a fresh server snapshot.
2. **`-q`:** distinctive substring (Chinese, Latin, English, or pinyin).
3. Parse stdout JSON; use **`taxonid`** in `search --body-json` → [birdrecord-search](../birdrecord-search/SKILL.md).

## Related

- Chart search: [birdrecord-search](../birdrecord-search/SKILL.md).
- Docs: `docs/CLI.md`, `docs/CLI.zh-CN.md`.
