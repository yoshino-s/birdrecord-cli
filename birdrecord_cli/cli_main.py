"""Backward-compatible re-export; implementation lives in ``birdrecord_cli.cli``."""

from birdrecord_cli.cli import cli, main

__all__ = ["cli", "main"]
