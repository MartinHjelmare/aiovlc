"""Provide a client."""
import asyncio
from collections.abc import Awaitable, Callable
import logging

import click

from ..client import Client
from ..exceptions import AIOVLCError
from ..model.command import Info, Status

LOGGER = logging.getLogger("aiovlc")

ClientFactory = Callable[[], Awaitable[Client]]


@click.command(options_metavar="<options>")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    required=True,
    help="Password of the connection.",
)
@click.option(
    "-H",
    "--host",
    default="localhost",
    show_default=True,
    help="Host of the connection.",
)
@click.option(
    "-p",
    "--port",
    default=4212,
    show_default=True,
    type=int,
    help="Port of the connection.",
)
def client(password: str, host: str, port: int) -> None:
    """Start a client."""

    async def client_factory() -> Client:
        """Return a client."""
        vlc_client = Client(password, host=host, port=port)
        return vlc_client

    run_client(client_factory)


def run_client(client_factory: ClientFactory) -> None:
    """Run a client."""
    LOGGER.info("Starting client")
    try:
        asyncio.run(start_client(client_factory))
    except KeyboardInterrupt:
        pass
    finally:
        LOGGER.info("Exiting CLI")


async def start_client(client_factory: ClientFactory) -> None:
    """Start the client."""
    vlc_client = await client_factory()

    try:
        async with vlc_client:
            await vlc_client.login()
            await handle_client(vlc_client)
    except AIOVLCError as err:
        LOGGER.error("Error '%s'", err)


async def handle_client(vlc_client: Client) -> None:
    """Handle the client calls."""
    while True:
        command = Status()
        output = await command.send(vlc_client)
        LOGGER.debug("Received: %s", output)
        info_command = Info()
        info_output = await info_command.send(vlc_client)
        LOGGER.debug("Received: %s", info_output)
        await asyncio.sleep(10)
