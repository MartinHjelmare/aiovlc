"""Provide a client for aiovlc."""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Literal, Self

from .const import LOGGER
from .exceptions import ConnectError, ConnectReadError
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
    Password,
    PasswordOutput,
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
        self,
        password: str,
        host: str = "localhost",
        port: int = 4212,
    ) -> None:
        """Set up the client client."""
        self.host = host
        self.password = password
        self.port = port
        self.command_lock = asyncio.Lock()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> Self:
        """Connect the client with context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Disconnect the client with context manager."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect the client."""
        try:
            self._reader, self._writer = await asyncio.open_connection(
                host=self.host,
                port=self.port,
            )
        except OSError as err:
            raise ConnectError(f"Failed to connect: {err}") from err

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if self._writer is None:
            raise RuntimeError("Client is not connected")
        try:
            self._writer.close()
            await self._writer.wait_closed()
        except OSError:
            pass

    async def read(self, read_until: str = TERMINATOR) -> str:
        """Return a decoded message."""
        if self._reader is None:
            raise RuntimeError("Client is not connected")

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
        if self._writer is None:
            raise RuntimeError("Client is not connected")

        try:
            self._writer.write(command.encode("utf-8"))
            await self._writer.drain()
        except OSError as err:
            raise ConnectError(f"Failed to write: {err}") from err

    async def login(self) -> PasswordOutput:
        """Login."""
        return await Password(self.password).send(self)

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
