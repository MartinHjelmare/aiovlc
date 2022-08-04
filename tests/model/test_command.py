"""Test the commands."""
from __future__ import annotations

from unittest.mock import AsyncMock, call

from aiovlc.client import Client
from aiovlc.model.command import Password, Status

# pylint: disable=unused-argument


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


async def test_password_command(
    transport: tuple[AsyncMock, AsyncMock],
    client_connected: Client,
) -> None:
    """Test the password command."""
    password = "test-password"
    mock_reader, mock_writer = transport
    mock_reader.readuntil.side_effect = [
        b"VLC media player 3.0.9.2 Vetinari\nPassword: ",
        b"\xff\xfb\x01\xff\xfc\x01\r\n",
        b"Welcome, Master\r\n",
        b"> ",
    ]

    command = Password(password)
    output = await command.send(client_connected)

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(f"{password}\n".encode())
    assert mock_reader.readuntil.call_count == 4
    assert output
    assert output.response == "Welcome, Master"
