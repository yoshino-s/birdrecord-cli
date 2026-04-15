> [!CAUTION]
> ### ⚠️ 声明（非官方）！！！
>
> **本项目并非** [中国观鸟记录中心](https://www.birdreport.cn/) **的官方项目**，与其无隶属或授权关系。**仅供个人研究使用，禁止滥用。** 数据解释权归中国观鸟记录中心所有。
>
> *This repository is **not** an official project of [中国观鸟记录中心](https://www.birdreport.cn/). **Personal research only; misuse is prohibited.** Interpretation of data belongs to 中国观鸟记录中心.*

---

# Birdrecord CLI

面向 [观鸟记录 / 中国观鸟记录中心](https://www.birdreport.cn/) 的 **命令行工具**（`birdrecord-cli`），并附带 **Agent Skills**，供智能体使用同一套能力：**在中心名录里查鸟种**、**按条件搜索与统计观鸟记录**、**按记录 id 查看单条详情**。

**鸟种**：清单、中文名/拉丁名及 `taxonid` 等均与小程序一致，以 **郑四**（《中国鸟类分类与分布名录》第四版）为准。

> [!NOTE]
> **国内网络备选（GitCode）**  
> 若访问 **GitHub**（`github.com`、`raw.githubusercontent.com` 等）**较慢、不稳定或超时**，可将**本仓库**相关地址换用镜像：**[https://gitcode.com/yoshino-s/birdrecord-cli](https://gitcode.com/yoshino-s/birdrecord-cli)**。下文凡同时给出 **方案一（GitHub）** 与 **方案二（GitCode）** 时，在国内网络不佳时请优先采用方案二。

> [!TIP]
> ### OpenClaw — TL;DR（智能体技能）
>
> **复制下方整段给 OpenClaw 即可。**
>
> **方案一（GitHub）**
>
> ```
> 帮我安装 https://github.com/yoshino-s/birdrecord-cli 的 skills
> ```
>
> **方案二（国内网络不佳：GitCode 镜像）**
>
> ```
> 帮我安装 https://gitcode.com/yoshino-s/birdrecord-cli 的 skills
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
uvx --from 'birdrecord-cli==0.1.3' birdrecord-cli --help
uvx --from 'birdrecord-cli==0.1.3' birdrecord-cli provinces --pretty
```

示例中的版本号请以 PyPI 当前最新版为准。

## 用法

常用选项：`--token`、`--base-url`、`--no-verify`、`--timeout`、`--pretty`、`--envelope`。子命令含 `provinces`、`cities`、`taxon`、`report`、`search`；多数支持 `--schema`。`search` 可选 `--taxon` / `--report` 做活动下钻，输出形态见 [docs/CLI.zh-CN.md](docs/CLI.zh-CN.md)。

```bash
birdrecord-cli provinces --pretty
birdrecord-cli report --id 1948816 --pretty
birdrecord-cli search --body-json '{"startTime":"2026-02-24","endTime":"2026-03-24","province":"河北省","taxonid":4148,"version":"CH4"}' --pretty
```

环境变量：

- `BIRDRECORD_CACHE_DIR`：物种表缓存根目录（可选，文件在 `…/taxon`）；未设置时优先 `$XDG_CACHE_HOME/birdrecord/taxon`，否则 `~/.cache/birdrecord/taxon`。
- `BIRDRECORD_CLI_CN`：设为非 `0` / `false` / `no` / `off` 的任意真值时，`--schema` 等 JSON Schema 描述为中文。

## 智能体技能（`npx skills`）

本仓库在 [`skills/`](./skills/) 下提供 [Agent Skills](https://agentskills.io)（`birdrecord-search`、`birdrecord-report-detail`、`birdrecord-taxon-search`），便于 **Cursor** 等编码智能体按规范调用 `birdrecord-cli`。**OpenClaw：** 见安装部分最上方 **TIP** 提示框（在 **从 PyPI 安装** 之前；内含 **方案一 GitHub / 方案二 GitCode** 两段可复制话术）。手动安装见 [skills CLI](https://github.com/vercel-labs/skills)（官方仓库在 GitHub，国内访问慢时可稍后再试或使用代理）与 [Cursor：Skills](https://cursor.com/docs/context/skills)：

**方案一（GitHub）** — `owner/repo` 简写默认指向 GitHub：

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

**方案二（国内网络不佳：GitCode 镜像）** — 使用仓库 **HTTPS 根地址**（将 `github.com/...` 换为 GitCode）：

```bash
npx skills add https://gitcode.com/yoshino-s/birdrecord-cli --list
npx skills add https://gitcode.com/yoshino-s/birdrecord-cli -a cursor -y
npx skills add https://gitcode.com/yoshino-s/birdrecord-cli --skill birdrecord-search -a cursor -y
```

若使用 fork：方案一把 `yoshino-s/birdrecord-cli` 换成你的 `owner/repo`；方案二把 `https://gitcode.com/yoshino-s/birdrecord-cli` 换成你的 GitCode 仓库 URL。单技能目录 tree 示例 — 方案一：`https://github.com/yoshino-s/birdrecord-cli/tree/main/skills/birdrecord-search`；方案二：`https://gitcode.com/yoshino-s/birdrecord-cli/tree/main/skills/birdrecord-search`。

## 演示

![birdrecord-cli 演示](https://raw.githubusercontent.com/yoshino-s/birdrecord-cli/main/docs/birdrecord-demo.gif)

## 开发

克隆后 `uv sync --group dev && uv run pytest tests/ -v`（部分请求线上 API；部分 `verify=False`）。代码在 [`birdrecord_cli/`](./birdrecord_cli/)，开发树中可用 `uv run birdrecord-cli …` 运行 CLI。测试从 `birdrecord_cli` 包导入。

## 许可

MIT，见 [LICENSE](LICENSE)。

---

**English**: [README.md](./README.md)
