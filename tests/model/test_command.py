"""Test the commands."""
from __future__ import annotations

from typing import Type
from unittest.mock import AsyncMock, call

import pytest

from aiovlc.client import Client
from aiovlc.exceptions import AuthError, CommandError
from aiovlc.model.command import Password, Status

# pylint: disable=unused-argument


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

    command = Password(password)
    output = await command.send(client_connected)

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
    """Test the password command."""
    password = "test-password"
    mock_reader, mock_writer = transport
    mock_reader.readuntil.side_effect = [
        b"VLC media player 3.0.9.2 Vetinari\nPassword: ",
        b"\xff\xfb\x01\xff\xfc\x01\r\n",
        *read,
    ]

    command = Password(password)
    with pytest.raises(error) as err:
        await command.send(client_connected)

    assert str(err.value) == error_message
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(f"{password}\n".encode())


async def test_status_command(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
    status_command_response: None,
) -> None:
    """Test the status command."""
    mock_reader, mock_writer = transport

    command = Status()
    output = await command.send(client_connected)

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"status\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.audio_volume == 0
    assert output.state == "stopped"
    assert output.input_loc is None
