"""Provide common fixtures."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from aiovlc.client import Client

# pylint: disable=unused-argument


@pytest.fixture(name="transport")
def transport_fixture():
    """Mock the transport."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("asyncio.open_connection", autospec=True) as open_connection:
        open_connection.return_value = (mock_reader, mock_writer)
        yield open_connection.return_value


@pytest.fixture(name="client")
async def client_fixture(transport):
    """Mock a client."""
    return Client("test-password")


@pytest.fixture(name="client_connected")
async def client_connected_fixture(client):
    """Mock a connected client."""
    await client.connect()
    return client


@pytest.fixture(name="status_command_response")
def status_command_response_fixture(transport):
    """Mock a status command response."""
    mock_reader, _ = transport
    mock_reader.readuntil.return_value = (
        b"( audio volume: 0 )\r\n( state stopped )\r\n> "
    )
