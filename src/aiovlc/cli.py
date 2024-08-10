"""CLI for the VLC client."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Annotated

from rich import print
import typer

from .client import Client
from .exceptions import AIOVLCError
from .model.command import Info, Status

app = typer.Typer()

ClientFactory = Callable[[], Awaitable[Client]]


@app.command()
def client(
    password: Annotated[
        str,
        typer.Option(help="Password of the connection.", prompt=True, hide_input=True),
    ],
    host: Annotated[str, typer.Option(help="Host of the connection.")] = "localhost",
    port: Annotated[int, typer.Option(help="Port of the connection.")] = 4212,
) -> None:
    """Start a client."""

    async def client_factory() -> Client:
        """Return a client."""
        return Client(password, host=host, port=port)

    run_client(client_factory)


def run_client(client_factory: ClientFactory) -> None:
    """Run a client."""
    print("Starting client")
    try:
        asyncio.run(start_client(client_factory))
    except KeyboardInterrupt:
        pass
    finally:
        print("Exiting CLI")


async def start_client(client_factory: ClientFactory) -> None:
    """Start the client."""
    vlc_client = await client_factory()

    try:
        async with vlc_client:
            await vlc_client.login()
            await handle_client(vlc_client)
    except AIOVLCError as err:
        print("Error:", err)


async def handle_client(vlc_client: Client) -> None:
    """Handle the client calls."""
    while True:
        command = Status()
        output = await command.send(vlc_client)
        print("Received:", output)
        info_command = Info()
        info_output = await info_command.send(vlc_client)
        print("Received:", info_output)
        await asyncio.sleep(10)
