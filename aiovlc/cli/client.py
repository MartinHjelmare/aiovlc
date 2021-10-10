"""Provide a TCP client."""
import asyncio
import logging
from typing import Awaitable, Callable

import click

from aiovlc.client import Client
from aiovlc.exceptions import AIOVLCError

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
        client = Client(password, host=host, port=port)
        return client

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
    client = await client_factory()

    async with client:
        while True:
            try:
                await handle_client(client)
            except AIOVLCError as err:
                LOGGER.error("Error '%s'", err)
                break


async def handle_client(client: Client) -> None:
    """Handle the client calls."""
    await client.login()

    async for msg in client.listen():  # pragma: no cover
        LOGGER.debug("Received: %s", msg)
