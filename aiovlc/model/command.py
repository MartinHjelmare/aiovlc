"""Provide commands for aiovlc."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from ..exceptions import CommandParseError

if TYPE_CHECKING:
    from ..client import Client


class Command:
    """Represent a VLC command."""

    prefix: str

    async def send(self, client: Client) -> CommandOutput | None:
        """Send the command."""
        return await self._send(client)

    async def _send(self, client: Client) -> CommandOutput | None:
        """Send the command."""
        output = await client.send_command(self.build_command())
        return self.parse_output(output)

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix}\n"

    def parse_output(self, output: list[str]) -> CommandOutput | None:
        """Parse command output."""
        # pylint: disable=no-self-use, unused-argument
        return None


@dataclass
class CommandOutput:
    """Represent a command output."""


class StatusCommand(Command):
    """Represent the status command."""

    prefix = "status"

    async def send(self, client: Client) -> StatusOutput:
        """Send the command."""
        return cast(StatusOutput, await self._send(client))

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
class StatusOutput(CommandOutput):
    """Represent the status command output."""

    audio_volume: int
    state: str
    input_loc: str | None = None
