> **⚠️ 声明（非官方）**
>
> **本项目并非** [中国观鸟记录中心](https://www.birdreport.cn/) **的官方项目**，与其无隶属或授权关系。**仅供个人研究使用，禁止滥用。** 数据解释权归中国观鸟记录中心所有。
>
> *This repository is **not** an official project of [中国观鸟记录中心](https://www.birdreport.cn/). **Personal research only; misuse is prohibited.** Interpretation of data belongs to 中国观鸟记录中心.*

---

# Birdrecord CLI

CLI for the [Birdrecord](https://www.birdreport.cn/) / China Bird Record mini-program API. HTTP defaults to API host `https://weixin.birdrecord.cn` (override with `--base-url`); the [portal site](https://www.birdreport.cn/) is separate.

**Species taxonomy**: Checklist entries, names, and `taxonid` values match the app and follow **Zheng 4**—the 4th edition of *A Checklist of the Birds of China* (中国鸟类分类与分布名录·第四版, “郑四”).

> [!TIP]
> ### OpenClaw — TL;DR (Agent Skills)
>
> **Copy-paste into OpenClaw** — it can run the install on your machine:
>
> ```
> Install the Agent Skills from https://github.com/yoshino-s/birdrecord-cli (under skills/) for OpenClaw. Run: npx skills add https://github.com/yoshino-s/birdrecord-cli -a openclaw -y from a suitable directory, then npx skills list to verify. If global install fits my machine better, use -g and say why.
> ```

## Install from PyPI

Requires **Python 3.12+**.

```bash
pip install birdrecord-cli
# or: uv tool install birdrecord-cli
birdrecord-cli --help
```

Package index: [pypi.org/project/birdrecord-cli](https://pypi.org/project/birdrecord-cli/).

## Run with uvx (no prior install)

[uv](https://docs.astral.sh/uv/) downloads the package into an ephemeral environment. Pin the version for reproducible behavior:

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli --help
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli provinces --pretty
```

Use the latest release version from PyPI if it differs from the example above.

## Single-file + uv (no install)

[PEP 723](https://peps.python.org/pep-0723/) script; [uv](https://docs.astral.sh/uv/) installs deps automatically.

```bash
curl -fsSL -o main.py 'https://raw.githubusercontent.com/yoshino-s/birdrecord-cli/main/main.py'
uv run main.py --help
```

For a fork, change `yoshino-s` and/or `main` in the URL.

## Usage

Shared flags: `--token`, `--base-url`, `--no-verify`, `--timeout`, `--pretty`, `--envelope`. Subcommands: `provinces`, `cities`, `taxon`, `report`, `search`; most support `--schema`. `search` accepts optional `--taxon` / `--report` for activity drill-down; stdout JSON shapes are described in [docs/CLI.md](docs/CLI.md) under **`search` output (JSON)**. Full copied `--help` text: [docs/CLI.md](docs/CLI.md).

```bash
birdrecord-cli provinces --pretty
birdrecord-cli report --id 1948816 --pretty
birdrecord-cli search --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' --pretty
```

(With `uv run main.py`, use the same subcommands after `uv run main.py`.)

Environment variables:

- `BIRDRECORD_CACHE_DIR`: optional taxon cache root (`…/taxon`); if unset, `$XDG_CACHE_HOME/birdrecord/taxon` when `XDG_CACHE_HOME` is set, else `~/.cache/birdrecord/taxon`.
- `BIRDRECORD_CLI_CN`: any truthy value (not `0` / `false` / `no` / `off`) uses Chinese JSON Schema descriptions (e.g. `--schema`).

## Agent skills (`npx skills`)

The repo includes [Agent Skills](https://agentskills.io) under [`skills/`](./skills/) (`birdrecord-search`, `birdrecord-report-detail`, `birdrecord-taxon-search`) so agents like **Cursor** know how to call `birdrecord-cli` safely. **OpenClaw:** use the highlighted tip box **above [Install from PyPI](#install-from-pypi)**. Manual install with the [skills CLI](https://github.com/vercel-labs/skills) ([Cursor: Skills](https://cursor.com/docs/context/skills)):

```bash
# Install all skills (CLI detects agents; interactive prompts)
npx skills add yoshino-s/birdrecord-cli

# Preview what would be installed
npx skills add yoshino-s/birdrecord-cli --list

# Cursor only, skip prompts (CI / scripts)
npx skills add yoshino-s/birdrecord-cli -a cursor -y

# One skill only
npx skills add yoshino-s/birdrecord-cli --skill birdrecord-search -a cursor -y
```

For a fork, use `owner/repo` instead of `yoshino-s/birdrecord-cli`, or a direct tree URL, e.g. `https://github.com/yoshino-s/birdrecord-cli/tree/main/skills/birdrecord-search`.

## Demo

![birdrecord-cli demo](https://raw.githubusercontent.com/yoshino-s/birdrecord-cli/main/docs/birdrecord-demo.gif)

## Development

Clone, then `uv sync --group dev && uv run pytest tests/ -v` (some tests hit the live API; some use `verify=False`). Tests import via [`birdrecord_client.py`](./birdrecord_client.py).

## License

MIT — see [LICENSE](LICENSE).

---

**中文说明**：[README.zh-CN.md](./README.zh-CN.md)
