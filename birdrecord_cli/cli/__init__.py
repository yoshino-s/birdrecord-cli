"""Click CLI entrypoint for birdrecord-cli; subpackages register commands."""

from __future__ import annotations

import click

from birdrecord_cli.cli.adcode import register_adcode_commands
from birdrecord_cli.cli.core import BirdrecordGroup
from birdrecord_cli.cli.report import register_report_commands
from birdrecord_cli.cli.search import register_search_commands
from birdrecord_cli.cli.taxon import register_taxon_commands
from birdrecord_cli.i18n import _cli_txt


@click.group(
    cls=BirdrecordGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=_cli_txt(
        "Birdrecord mini-program API CLI.",
        "Birdrecord 小程序 API 命令行工具。",
    ),
)
def cli() -> None:
    pass


register_adcode_commands(cli)
register_taxon_commands(cli)
register_report_commands(cli)
register_search_commands(cli)


def main() -> None:
    """Entry point for the ``birdrecord-cli`` console script."""
    cli.main(prog_name="birdrecord-cli", standalone_mode=True)


if __name__ == "__main__":
    main()
