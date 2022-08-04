"""Test the commands."""
from __future__ import annotations

from typing import Type
from unittest.mock import AsyncMock, call

import pytest

from aiovlc.client import Client
from aiovlc.exceptions import AuthError, CommandError, CommandParseError

# pylint: disable=unused-argument


@pytest.mark.parametrize(
    "read, length",
    [(b"372\r\n> ", 372), (b"\r\n> ", 0)],
)
async def test_get_length(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
    read: list[bytes],
    length: int,
) -> None:
    """Test the get length command."""
    mock_reader, mock_writer = transport
    mock_reader.readuntil.return_value = read

    output = await client_connected.get_length()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"get_length\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.length == length


@pytest.mark.parametrize(
    "read, error, error_message",
    [
        (b"> ", CommandParseError, "Could not get length."),
        (
            b"unexpected\r\n> ",
            CommandParseError,
            "Could not get length.",
        ),
    ],
)
async def test_get_length_error(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
    read: list[bytes],
    error: Type[Exception],
    error_message: str,
) -> None:
    """Test the get length command errors."""
    mock_reader, mock_writer = transport
    mock_reader.readuntil.return_value = read

    with pytest.raises(error) as err:
        await client_connected.get_length()

    assert str(err.value) == error_message
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"get_length\n")
    assert mock_reader.readuntil.call_count == 1


async def test_info_command(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
) -> None:
    """Test the info command."""
    mock_reader, mock_writer = transport
    mock_reader.readuntil.return_value = (
        b"+----[ Meta data ]\r\n"
        b"|\r\n"
        b"| filename: test_song.mp3\r\n"
        b"|\r\n"
        b"+----[ Stream 0 ]\r\n"
        b"|\r\n"
        b"| Channels: Stereo\r\n"
        b"| Codec: MPEG Audio layer 1/2 (mpga)\r\n"
        b"| Bits per sample: 32\r\n"
        b"| Type: Audio\r\n"
        b"| Sample rate: 44100 Hz\r\n"
        b"|\r\n"
        b"+----[ end of stream info ]\r\n"
        b"> "
    )

    output = await client_connected.info()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"info\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.data == {
        0: {
            "Bits per sample": 32,
            "Channels": "Stereo",
            "Codec": "MPEG Audio layer 1/2 (mpga)",
            "Sample rate": "44100 Hz",
            "Type": "Audio",
        },
        "data": {"filename": "test_song.mp3"},
    }


async def test_info_command_error(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
) -> None:
    """Test the info command error."""
    mock_reader, mock_writer = transport
    mock_reader.readuntil.return_value = b"unexpected\r\n" b"> "

    with pytest.raises(CommandError) as err:
        await client_connected.info()

    assert str(err.value) == "Unexpected line in info output: unexpected"

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"info\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "read, read_call_count",
    [([b"Welcome, Master\r\n", b"> "], 4), ([b"Welcome, Master> \r\n"], 3)],
)
async def test_password_command(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
    read: list[bytes],
    read_call_count: int,
) -> None:
    """Test the password command."""
    password = "test-password"
    mock_reader, mock_writer = transport
    mock_reader.readuntil.side_effect = [
        b"VLC media player 3.0.9.2 Vetinari\nPassword: ",
        b"\xff\xfb\x01\xff\xfc\x01\r\n",
        *read,
    ]

    output = await client_connected.login()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(f"{password}\n".encode())
    assert mock_reader.readuntil.call_count == read_call_count
    assert output
    assert output.response == "Welcome, Master"


@pytest.mark.parametrize(
    "read, error, error_message",
    [
        ([b"Wrong password\r\n"], AuthError, "Failed to login to VLC."),
        (
            [b"unexpected reply\r\n"],
            CommandError,
            "Unexpected password response: unexpected reply",
        ),
        ([b"\r\n"], CommandError, "Empty password response"),
    ],
)
async def test_password_command_error(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
    read: list[bytes],
    error: Type[Exception],
    error_message: str,
) -> None:
    """Test the password command errors."""
    password = "test-password"
    mock_reader, mock_writer = transport
    mock_reader.readuntil.side_effect = [
        b"VLC media player 3.0.9.2 Vetinari\nPassword: ",
        b"\xff\xfb\x01\xff\xfc\x01\r\n",
        *read,
    ]

    with pytest.raises(error) as err:
        await client_connected.login()

    assert str(err.value) == error_message
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(f"{password}\n".encode())


async def test_status_command(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
) -> None:
    """Test the status command."""
    mock_reader, mock_writer = transport
    mock_reader.readuntil.return_value = (
        b"( audio volume: 0 )\r\n( state stopped )\r\n> "
    )

    output = await client_connected.status()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"status\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.audio_volume == 0
    assert output.state == "stopped"
    assert output.input_loc is None
