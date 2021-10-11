"""Provide commands for aiovlc."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

from ..exceptions import CommandParseError

if TYPE_CHECKING:
    from ..client import Client

T = TypeVar("T")


@dataclass
class Command(Generic[T]):
    """Represent a VLC command."""

    prefix: str = field(init=False)

    async def send(self, client: Client) -> T:
        """Send the command."""
        return await self._send(client)

    async def _send(self, client: Client) -> T:
        """Send the command."""
        output = await client.send_command(self.build_command())
        return self.parse_output(output)

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix}\n"

    def parse_output(self, output: list[str]) -> T:
        """Parse command output."""
        # pylint: disable=no-self-use, unused-argument
        # Disable mypy to have cleaner code in child classes.
        return None  # type: ignore[return-value]


@dataclass
class CommandOutput:
    """Represent a command output."""


@dataclass
class Add(Command[None]):
    """Represent the add command."""

    prefix = "add"
    playlist_item: str

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix} {self.playlist_item}\n"


@dataclass
class Enqueue(Command[None]):
    """Represent the enqueue command."""

    prefix = "enqueue"
    playlist_item: str

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix} {self.playlist_item}\n"


@dataclass
class Next(Command[None]):
    """Represent the next command."""

    prefix = "next"


@dataclass
class Play(Command[None]):
    """Represent the play command."""

    prefix = "play"


@dataclass
class Prev(Command[None]):
    """Represent the prev command."""

    prefix = "prev"


@dataclass
class StatusOutput(CommandOutput):
    """Represent the status command output."""

    audio_volume: int
    state: str
    input_loc: str | None = None


class Status(Command[StatusOutput]):
    """Represent the status command."""

    prefix = "status"

    def parse_output(self, output: list[str]) -> StatusOutput:
        """Parse command output."""
        input_loc: str | None = None
        if len(output) == 3:
            input_loc_item = output.pop(0)
            input_loc = "%20".join(input_loc_item.split(" ")[3:-1])
        if len(output) == 2:
            audio_volume = int(output[0].split(" ")[3])
            state = output[1].split(" ")[2]
        else:
            raise CommandParseError("Could not get status.")
        return StatusOutput(audio_volume=audio_volume, state=state, input_loc=input_loc)


@dataclass
class Stop(Command[None]):
    """Represent the stop command."""

    prefix = "stop"
