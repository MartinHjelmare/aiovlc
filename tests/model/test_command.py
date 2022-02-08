"""Test the commands."""
from __future__ import annotations

from unittest.mock import AsyncMock, call

from aiovlc.client import Client
from aiovlc.model.command import Status

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
