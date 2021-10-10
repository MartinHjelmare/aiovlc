"""Provide commands for aiovlc."""
from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import CommandParseError


class Command:
    """Represent a VLC command."""

    prefix: str

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

    def parse_output(self, output: list[str]) -> StatusOutput:
        """Parse command output."""
        input_loc: str | None = None
        if len(output) == 3:
            input_loc_item = output.pop(0)
            input_loc = "%20".join(input_loc_item.split(" ")[3:-1])
        if len(output) == 2:
            volume = int(output[0].split(" ")[3])
            state = output[1].split(" ")[2]
        else:
            raise CommandParseError("Could not get status.")
        return StatusOutput(state=state, volume=volume, input_loc=input_loc)


@dataclass
class StatusOutput(CommandOutput):
    """Represent the status command output."""

    state: str
    volume: int
    input_loc: str | None = None
