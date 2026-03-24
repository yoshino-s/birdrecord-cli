> **⚠️ 声明（非官方）**
>
> **本项目并非** [中国观鸟记录中心](https://www.birdreport.cn/) **的官方项目**，与其无隶属或授权关系。**仅供个人研究使用，禁止滥用。** 数据解释权归中国观鸟记录中心所有。
>
> *This repository is **not** an official project of [中国观鸟记录中心](https://www.birdreport.cn/). **Personal research only; misuse is prohibited.** Interpretation of data belongs to 中国观鸟记录中心.*

---

# Birdrecord CLI

[观鸟记录](https://www.birdreport.cn/) / 中国观鸟记录中心 小程序 API 的 CLI。HTTP 默认访问 API 主机 `https://weixin.birdrecord.cn`（可用 `--base-url` 覆盖）；[官网](https://www.birdreport.cn/) 与 API 主机不同。

**鸟种**：清单、中文名/拉丁名及 `taxonid` 等均与小程序一致，以 **郑四**（《中国鸟类分类与分布名录》第四版）为准。

> [!TIP]
> ### OpenClaw — TL;DR（智能体技能）
>
> **把下面整段复制到 OpenClaw**，由它在本机执行安装：
>
> ```
> 帮我安装 https://github.com/yoshino-s/birdrecord-cli 仓库里 skills/ 目录下的 Agent Skills，并挂到 OpenClaw。请在合适的工作目录执行：npx skills add https://github.com/yoshino-s/birdrecord-cli -a openclaw -y，然后用 npx skills list 确认已装上。若全局安装更合适请改用 -g 并说明原因。
> ```

## 从 PyPI 安装

需要 **Python 3.12+**。

```bash
pip install birdrecord-cli
# 或: uv tool install birdrecord-cli
birdrecord-cli --help
```

包页面：[pypi.org/project/birdrecord-cli](https://pypi.org/project/birdrecord-cli/)。

## 用 uvx 运行（无需事先安装）

[uv](https://docs.astral.sh/uv/) 会临时拉取包。建议 **固定版本** 以便结果可复现：

```bash
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli --help
uvx --from 'birdrecord-cli==0.1.0' birdrecord-cli provinces --pretty
```

示例中的版本号请以 PyPI 当前最新版为准。

## 单文件 + uv（不安装包）

[PEP 723](https://peps.python.org/pep-0723/) 脚本，用 [uv](https://docs.astral.sh/uv/) 自动装依赖。

```bash
curl -fsSL -o main.py 'https://raw.githubusercontent.com/yoshino-s/birdrecord-cli/main/main.py'
uv run main.py --help
```

fork 请改 URL 中的 `yoshino-s` / `main`。

## 用法

常用选项：`--token`、`--base-url`、`--no-verify`、`--timeout`、`--pretty`、`--envelope`。子命令含 `provinces`、`cities`、`taxon`、`report`、`search`；多数支持 `--schema`。`search` 可选 `--taxon` / `--report` 做活动下钻，输出形态见 [docs/CLI.zh-CN.md](docs/CLI.zh-CN.md)。

```bash
birdrecord-cli provinces --pretty
birdrecord-cli report --id 1948816 --pretty
birdrecord-cli search --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' --pretty
```

（若用 `uv run main.py`，在命令后接相同子命令即可。）

环境变量：

- `BIRDRECORD_CACHE_DIR`：物种表缓存根目录（可选，文件在 `…/taxon`）；未设置时优先 `$XDG_CACHE_HOME/birdrecord/taxon`，否则 `~/.cache/birdrecord/taxon`。
- `BIRDRECORD_CLI_CN`：设为非 `0` / `false` / `no` / `off` 的任意真值时，`--schema` 等 JSON Schema 描述为中文。

## 智能体技能（`npx skills`）

本仓库在 [`skills/`](./skills/) 下提供 [Agent Skills](https://agentskills.io)（`birdrecord-search`、`birdrecord-report-detail`、`birdrecord-taxon-search`），便于 **Cursor** 等编码智能体按规范调用 `birdrecord-cli`。**OpenClaw：** 见安装部分最上方带 **TIP** 标记的提示框（在 **从 PyPI 安装** 之前）。手动安装见 [skills CLI](https://github.com/vercel-labs/skills)（[Cursor：Skills](https://cursor.com/docs/context/skills)）：

```bash
# 安装全部技能（CLI 会探测已装智能体；有交互提示）
npx skills add yoshino-s/birdrecord-cli

# 只列出可安装项，不安装
npx skills add yoshino-s/birdrecord-cli --list

# 仅 Cursor、跳过确认（适合脚本）
npx skills add yoshino-s/birdrecord-cli -a cursor -y

# 只装某一个技能
npx skills add yoshino-s/birdrecord-cli --skill birdrecord-search -a cursor -y
```

若使用 fork，把 `yoshino-s/birdrecord-cli` 换成你的 `owner/repo`，或使用指向单技能目录的 tree 地址，例如 `https://github.com/yoshino-s/birdrecord-cli/tree/main/skills/birdrecord-search`。

## 演示

![birdrecord-cli 演示](https://raw.githubusercontent.com/yoshino-s/birdrecord-cli/main/docs/birdrecord-demo.gif)

## 开发

克隆后 `uv sync --group dev && uv run pytest tests/ -v`（部分请求线上 API；部分 `verify=False`）。测试经 [`birdrecord_client.py`](./birdrecord_client.py) 导入。

## 许可

MIT，见 [LICENSE](LICENSE)。

---

**English**: [README.md](./README.md)
