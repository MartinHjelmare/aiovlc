"""Provide a client for aiovlc."""
from __future__ import annotations

import asyncio
import re
from types import TracebackType
from typing import Literal

from .const import LOGGER
from .exceptions import AuthError, CommandError, ConnectError, ConnectReadError
from .model.command import (
    Add,
    Clear,
    Enqueue,
    GetLength,
    GetLengthOutput,
    GetTime,
    GetTimeOutput,
    Info,
    InfoOutput,
    Next,
    Pause,
    Play,
    Prev,
    Random,
    Seek,
    SetVolume,
    Status,
    StatusOutput,
    Stop,
    Volume,
    VolumeOutput,
)

IAC = bytes([255])  # "Interpret As Command"
TERMINATOR = "\n"


class Client:
    """Represent a client for aiovlc."""

    # pylint: disable=too-many-public-methods

    def __init__(
        self, password: str, host: str = "localhost", port: int = 4212
    ) -> None:
        """Set up the client client."""
        self.host = host
        self.password = password
        self.port = port
        self._command_lock = asyncio.Lock()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

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
            self._reader, self._writer = await asyncio.open_connection(
                host=self.host, port=self.port
            )
        except OSError as err:
            raise ConnectError(f"Failed to connect: {err}") from err

    async def disconnect(self) -> None:
        """Disconnect the client."""
        assert self._writer is not None
        try:
            self._writer.close()
            await self._writer.wait_closed()
        except OSError:
            pass

    async def read(self, read_until: str = TERMINATOR) -> str:
        """Return a decoded message."""
        assert self._reader is not None

        try:
            read = await self._reader.readuntil(read_until.encode("utf-8"))
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
        assert self._writer is not None

        try:
            self._writer.write(command.encode("utf-8"))
            await self._writer.drain()
        except OSError as err:
            raise ConnectError(f"Failed to write: {err}") from err

    async def login(self) -> None:
        """Login."""
        await self.read("Password: ")
        command_string = f"{self.password}\n"
        await self.write(command_string)
        for _ in range(2):
            command_output = (await self.read("\n")).strip("\r\n")
            if command_output:  # discard empty line once.
                break
        parsed_output = command_output.lower()
        if "wrong password" in parsed_output:
            raise AuthError("Failed to login to VLC.")
        if "welcome" not in parsed_output:
            raise CommandError(f"Unexpected password response: {command_output}")
        if "> " in command_output:
            return
        # Read until prompt
        await self.read("> ")

    async def send_command(self, command_string: str) -> list[str]:
        """Send a command and return the output."""
        async with self._command_lock:
            LOGGER.debug("Sending command: %s", command_string.strip())
            await self.write(command_string)
            command_output = (await self.read("> ")).split("\r\n")[:-1]
            LOGGER.debug("Command output: %s", command_output)
        if command_output:
            if re.match(
                r"Unknown command `.*'\. Type `help' for help\.", command_output[0]
            ):
                raise CommandError("Unknown Command")
            if command_error := re.match(r"Error in.*", command_output[0]):
                raise CommandError(command_error.group())

        return command_output

    async def add(self, playlist_item: str) -> None:
        """Send the add command."""
        await Add(playlist_item).send(self)

    async def clear(self) -> None:
        """Send the clear command."""
        await Clear().send(self)

    async def enqueue(self, playlist_item: str) -> None:
        """Send the enqueue command."""
        await Enqueue(playlist_item).send(self)

    async def get_length(self) -> GetLengthOutput:
        """Send the get_length command."""
        return await GetLength().send(self)

    async def get_time(self) -> GetTimeOutput:
        """Send the get_time command."""
        return await GetTime().send(self)

    async def info(self) -> InfoOutput:
        """Send the info command."""
        return await Info().send(self)

    async def next(self) -> None:
        """Send the next command."""
        await Next().send(self)

    async def pause(self) -> None:
        """Send the pause command."""
        await Pause().send(self)

    async def play(self) -> None:
        """Send the play command."""
        await Play().send(self)

    async def prev(self) -> None:
        """Send the prev command."""
        await Prev().send(self)

    async def random(self, mode: Literal["on", "off"] | None = None) -> None:
        """Send the random command."""
        await Random(mode).send(self)

    async def seek(self, seconds: int) -> None:
        """Send the seek command."""
        await Seek(seconds).send(self)

    async def set_volume(self, volume: int) -> None:
        """Send the volume command with a parameter to set volume."""
        await SetVolume(volume).send(self)

    async def status(self) -> StatusOutput:
        """Send the status command."""
        return await Status().send(self)

    async def stop(self) -> None:
        """Send the stop command."""
        await Stop().send(self)

    async def volume(self) -> VolumeOutput:
        """Send the volume command."""
        return await Volume().send(self)
