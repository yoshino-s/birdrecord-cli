"""CLI language toggle (BIRDRECORD_CLI_CN)."""

import os


def _cli_use_zh_cn() -> bool:
    """True when BIRDRECORD_CLI_CN is set to a truthy value (0/false/no/off disable)."""
    raw = os.environ.get("BIRDRECORD_CLI_CN")
    if raw is None:
        return False
    s = raw.strip().lower()
    if s in ("0", "false", "no", "off"):
        return False
    return bool(s)


def _cli_txt(en: str, cn: str) -> str:
    return cn if _cli_use_zh_cn() else en


# Bilingual schema text only for models exposed via ``birdrecord_cli.models`` or emitted
# via CLI ``--schema`` (see ``json_schema_text`` / ``json_schema_text_object``).
_schema_txt = _cli_txt
