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
