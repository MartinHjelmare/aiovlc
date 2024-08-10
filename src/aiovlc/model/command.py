"""Provide commands for aiovlc."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from ..const import LOGGER
from ..exceptions import (
    AuthError,
    CommandError,
    CommandParameterError,
    CommandParseError,
)

if TYPE_CHECKING:
    from ..client import Client

T = TypeVar("T")
DEFAULT_COMMAND_READ_TERMINATOR = "> "


@dataclass
class Command(Generic[T]):
    """Represent a VLC command."""

    log_command: bool = field(init=False, default=True)
    prefix: str = field(init=False)
    read_terminator: str = field(init=False, default=DEFAULT_COMMAND_READ_TERMINATOR)

    async def send(self, client: Client) -> T:
        """Send the command."""
        return await self._send_command(client)

    async def _send_command(self, client: Client) -> T:
        """Send the command."""
        command_string = self.build_command()

        async with client.command_lock:
            if self.log_command:
                LOGGER.debug("Sending command: %s", command_string.strip())
            await client.write(command_string)
            raw_output = await client.read(self.read_terminator)

        command_output = raw_output.split("\r\n")[:-1]
        LOGGER.debug("Command output: %s", command_output)

        if command_output:
            if re.match(
                r"Unknown command `.*'\. Type `help' for help\.",
                command_output[0],
            ):
                raise CommandError("Unknown Command")
            if command_error := re.match(r"Error in.*", command_output[0]):
                raise CommandError(command_error.group())

        return self.parse_output(command_output)

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix}\n"

    def parse_output(self, output: list[str]) -> T:  # noqa: ARG002
        """Parse command output."""
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
class Clear(Command[None]):
    """Represent the clear command."""

    prefix = "clear"


@dataclass
class Enqueue(Command[None]):
    """Represent the enqueue command."""

    prefix = "enqueue"
    playlist_item: str

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix} {self.playlist_item}\n"


@dataclass
class GetLengthOutput(CommandOutput):
    """Represent the get length command output."""

    length: int


@dataclass
class GetLength(Command[GetLengthOutput]):
    """Represent the get length command."""

    prefix = "get_length"

    def parse_output(self, output: list[str]) -> GetLengthOutput:
        """Parse command output."""
        try:
            if not (length_string := output[0]):
                return GetLengthOutput(length=0)
            length = int(length_string)
        except (IndexError, ValueError) as err:
            raise CommandParseError("Could not get length.") from err
        return GetLengthOutput(length=length)


@dataclass
class GetTimeOutput(CommandOutput):
    """Represent the get time command output."""

    time: int


@dataclass
class GetTime(Command[GetTimeOutput]):
    """Represent the get time command."""

    prefix = "get_time"

    def parse_output(self, output: list[str]) -> GetTimeOutput:
        """Parse command output."""
        try:
            if not (time_string := output[0]):
                return GetTimeOutput(time=0)
            time = int(time_string)
        except (IndexError, ValueError) as err:
            raise CommandParseError("Could not get time.") from err
        return GetTimeOutput(time=time)


@dataclass
class InfoOutput(CommandOutput):
    """Represent the info command output."""

    data: dict[str | int, dict[str, str | int | float]] = field(default_factory=dict)


@dataclass
class Info(Command[InfoOutput]):
    """Represent the info command."""

    prefix = "info"

    def parse_output(self, output: list[str]) -> InfoOutput:
        """Parse command output."""
        data: dict[str | int, dict[str, str | int | float]] = {}
        section: int | str = "unknown"
        for line in output:
            if line[0] == "+":
                # Example: "+----[ Stream 5 ]" or "+----[ Meta data ]"  # noqa: ERA001
                if "end of stream info" in line:
                    continue
                section = line.split("[")[1].replace("]", "").strip().split(" ")[1]
                with contextlib.suppress(ValueError):
                    section = int(section)
                data[section] = {}
            elif line[0] == "|":
                # Example: "| Description: Closed captions 4"  # noqa: ERA001
                if len(line[2:]) == 0:
                    continue
                value: int | float | str = "unknown"
                key, value = line[2:].split(":", 1)
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        value = value.strip()  # type: ignore[union-attr]
                data[section][key.strip()] = value
            else:
                raise CommandParseError(f"Unexpected line in info output: {line}")
        return InfoOutput(data=data)


@dataclass
class PasswordOutput(CommandOutput):
    """Represent the password command output."""

    response: str


@dataclass
class Password(Command[PasswordOutput]):
    """Represent the password command."""

    log_command = False
    prefix = ""
    password: str
    read_terminator = "\n"

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix}{self.password}\n"

    def parse_output(self, output: list[str]) -> PasswordOutput:
        """Parse command output."""
        response: str = ""
        for line in output:
            if not line:
                continue
            response = line
            parsed_output = response.lower()
            if "wrong password" in parsed_output:
                raise AuthError("Failed to login to VLC.")
            if "welcome" not in parsed_output:
                raise CommandError(f"Unexpected password response: {response}")

        if not response:
            raise CommandError("Empty password response")
        return PasswordOutput(response)

    async def send(self, client: Client) -> PasswordOutput:
        """Send the command."""
        await client.read("Password: ")
        password_output = await super().send(client)
        if DEFAULT_COMMAND_READ_TERMINATOR in password_output.response:
            password_output.response = password_output.response.strip(
                DEFAULT_COMMAND_READ_TERMINATOR,
            )
            return password_output
        # Read until prompt
        await client.read(DEFAULT_COMMAND_READ_TERMINATOR)
        return password_output


@dataclass
class Next(Command[None]):
    """Represent the next command."""

    prefix = "next"


@dataclass
class Pause(Command[None]):
    """Represent the pause command."""

    prefix = "pause"


@dataclass
class Play(Command[None]):
    """Represent the play command."""

    prefix = "play"


@dataclass
class Prev(Command[None]):
    """Represent the prev command."""

    prefix = "prev"


@dataclass
class Random(Command[None]):
    """Represent the random command."""

    prefix = "random"
    mode: Literal["on", "off"] | None = None
    VALID_MODES = (None, "on", "off")

    def build_command(self) -> str:
        """Return the full command string."""
        if self.mode not in self.VALID_MODES:
            raise CommandParameterError(f"Parameter mode not in {self.VALID_MODES}")
        mode = "" if self.mode is None else f" {self.mode}"
        return f"{self.prefix}{mode}\n"


@dataclass
class Seek(Command[None]):
    """Represent the seek command."""

    prefix = "seek"
    seconds: int

    def build_command(self) -> str:
        """Return the full command string."""
        return f"{self.prefix} {self.seconds}\n"


@dataclass
class StatusOutput(CommandOutput):
    """Represent the status command output."""

    audio_volume: int
    state: str
    input_loc: str | None = None


@dataclass
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
            audio_volume = int(float(output[0].split(" ")[3].replace(",", ".")))
            state = output[1].split(" ")[2]
        else:
            raise CommandParseError("Could not get status.")
        return StatusOutput(audio_volume=audio_volume, state=state, input_loc=input_loc)


@dataclass
class Stop(Command[None]):
    """Represent the stop command."""

    prefix = "stop"


@dataclass
class VolumeOutput(CommandOutput):
    """Represent the volume command output."""

    audio_volume: int


@dataclass
class Volume(Command[VolumeOutput]):
    """Represent the volume command."""

    prefix = "volume"

    def parse_output(self, output: list[str]) -> VolumeOutput:
        """Parse command output."""
        try:
            audio_volume = int(float(output[0].replace(",", ".")))
        except (IndexError, ValueError) as err:
            raise CommandParseError("Could not get volume.") from err
        return VolumeOutput(audio_volume=audio_volume)


@dataclass
class SetVolume(Command[None]):
    """Represent the set volume command."""

    prefix = "volume"
    volume: int
    VALID_VOLUME = range(500)

    def build_command(self) -> str:
        """Return the full command string."""
        try:
            volume = int(self.volume)
        except ValueError as err:
            raise CommandParameterError(
                f"Invalid volume parameter: {self.volume}",
            ) from err
        if volume not in self.VALID_VOLUME:
            raise CommandParameterError(f"Parameter volume not in {self.VALID_VOLUME}")
        return f"{self.prefix} {volume}\n"
