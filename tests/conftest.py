"""Provide common fixtures."""
from __future__ import annotations

import asyncio
from typing import Generator
from unittest.mock import AsyncMock, patch

import pytest

from aiovlc.client import Client

# pylint: disable=unused-argument


@pytest.fixture(name="transport")
def transport_fixture() -> Generator[tuple[AsyncMock, AsyncMock], None, None]:
    """Mock the transport."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("asyncio.open_connection", autospec=True) as open_connection:
        open_connection.return_value = (mock_reader, mock_writer)
        yield open_connection.return_value


@pytest.fixture(name="client")
async def client_fixture(transport: tuple[AsyncMock, AsyncMock]) -> Client:
    """Mock a client."""
    return Client("test-password")


@pytest.fixture(name="client_connected")
async def client_connected_fixture(client: Client) -> Client:
    """Mock a connected client."""
    await client.connect()
    return client
