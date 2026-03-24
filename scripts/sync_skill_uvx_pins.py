#!/usr/bin/env python3
"""Rewrite ``birdrecord-cli==X.Y.Z`` pins wherever we document ``uvx --from``.

Updates:
  - ``skills/**/*.md`` (agent SKILL examples)
  - ``README.md``, ``README.zh-CN.md`` (user-facing uvx examples)

Usage:
  python3 scripts/sync_skill_uvx_pins.py           # version from pyproject.toml
  python3 scripts/sync_skill_uvx_pins.py 0.2.0     # explicit version
"""

from __future__ import annotations

import pathlib
import re
import sys


def _version_from_pyproject() -> str:
    import tomllib

    data = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _paths_to_scan(repo: pathlib.Path) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    skills = repo / "skills"
    if skills.is_dir():
        out.extend(sorted(skills.rglob("*.md")))
    for name in ("README.md", "README.zh-CN.md"):
        p = repo / name
        if p.is_file():
            out.append(p)
    return out


def main() -> None:
    ver = sys.argv[1] if len(sys.argv) > 1 else _version_from_pyproject()
    repo = pathlib.Path(__file__).resolve().parent.parent
    paths = _paths_to_scan(repo)
    if not paths:
        print("No skills/ or README*.md found", file=sys.stderr)
        sys.exit(1)
    # Match full pin after == up to whitespace, quotes, or closing paren.
    pat = re.compile(r"birdrecord-cli==[^\s'\"`\)]+")
    rep = f"birdrecord-cli=={ver}"
    changed: list[pathlib.Path] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        new = pat.sub(rep, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    for p in changed:
        print(p)


if __name__ == "__main__":
    main()
