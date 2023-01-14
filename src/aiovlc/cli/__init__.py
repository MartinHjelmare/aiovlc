"""Provide a CLI for aiovlc."""
import logging

import click

from aiovlc import __version__

from .client_command import client

SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    options_metavar="", subcommand_metavar="<command>", context_settings=SETTINGS
)
@click.option("--debug", is_flag=True, help="Start aiovlc in debug mode.")
@click.version_option(__version__)
def cli(debug: bool) -> None:
    """Run aiovlc as an app for testing purposes."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


cli.add_command(client)
