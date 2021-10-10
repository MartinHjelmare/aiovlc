"""Provide a client for aiovlc."""
from __future__ import annotations

import asyncio
from types import TracebackType
from typing import AsyncGenerator

from .const import LOGGER
from .exceptions import AuthError, CommandError, ConnectError, ConnectReadError

IAC = bytes([255])  # "Interpret As Command"
TERMINATOR = "\n"


class Client:
    """Represent a client for aiovlc."""

    def __init__(
        self, password: str, host: str = "localhost", port: int = 4212
    ) -> None:
        """Set up the client client."""
        self.host = host
        self.password = password
        self.port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> Client:
        """Connect the client with context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect the client with context manager."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect the client."""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                host=self.host, port=self.port
            )
        except OSError as err:
            raise ConnectError(f"Failed to connect: {err}") from err

    async def disconnect(self) -> None:
        """Disconnect the client."""
        assert self.writer is not None
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except OSError:
            pass

    async def read(self, read_until: str = TERMINATOR) -> str:
        """Return a decoded message."""
        assert self.reader is not None

        try:
            read = await self.reader.readuntil(read_until.encode("utf-8"))
        except asyncio.LimitOverrunError as err:
            raise ConnectReadError(err) from err
        except asyncio.IncompleteReadError as err:
            raise ConnectReadError(err, err.partial) from err
        except OSError as err:
            raise ConnectError(f"Failed to read: {err}") from err

        LOGGER.debug("Bytes read: %s", read)

        # Drop IAC command and read again.
        if IAC in read:
            return await self.read(read_until)
        return read.decode("utf-8")

    async def write(self, command: str) -> None:
        """Write a command to the connection."""
        assert self.writer is not None

        try:
            self.writer.write(command.encode("utf-8"))
            await self.writer.drain()
        except OSError as err:
            raise ConnectError(f"Failed to write: {err}") from err

    async def listen(self) -> AsyncGenerator[str, None]:
        """Listen and yield a message."""
        while True:
            message_string = await self.read()

            yield message_string

    async def login(self):
        """Login."""
        await self.read("Password: ")
        full_command = f"{self.password}\n"
        await self.write(full_command)
        for _ in range(2):
            command_output = (await self.read("\n")).strip("\r\n")
            if command_output:  # discard empty line once.
                break
        parsed_output = command_output.lower()
        if "wrong password" in parsed_output:
            raise AuthError("Failed to login to VLC.")
        if "welcome" not in parsed_output:
            raise CommandError(
                "Unexpected password response: {}".format(command_output)
            )
        if "> " in command_output:
            return
        # Read until prompt
        await self.read("> ")
