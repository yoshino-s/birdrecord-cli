## [0.1.2] — 2026-04-14

- Replaced `httpx` with `requests` as the HTTP client (`requests.Session`); public API unchanged.
- Added `pre-commit` configuration with `pre-push` hooks: `ruff` lint, `ruff-format --check`, `uv lock --check`, requirements export check, and `pytest`.
- Added `requirements.txt` auto-generated from `uv export --frozen --no-dev`.

**Full Changelog**: https://github.com/yoshino-s/birdrecord-cli/compare/v0.1.1...v0.1.2

---

## [0.1.1] — 2026-03-25

---

## [0.1.1] — 2026-03-25

- Split `birdrecord_cli.cli` into subpackages per command; `models` into `models.client` (HTTP API) and `models.cli` (CLI-only shapes).
- Renamed chart/activity/search models for consistent `*Request` / `UnifiedSearch*` naming.
- Fixed setuptools `packages.find` so wheels include all subpackages; console entrypoint is `birdrecord_cli.cli:main`.
- Removed root `main.py` and `birdrecord_client.py` shims; tests import from `birdrecord_cli` directly.

**Full Changelog**: https://github.com/yoshino-s/birdrecord-cli/commits/v0.1.1

## [0.1.0] — 2026-03-24

**Full Changelog**: https://github.com/yoshino-s/birdrecord-cli/commits/v0.1.0

---

# Changelog

Entries below are added automatically when `pyproject.toml` `[project].version` is bumped on `main`. Full history and assets: [GitHub Releases](https://github.com/yoshino-s/birdrecord-cli/releases).

---
