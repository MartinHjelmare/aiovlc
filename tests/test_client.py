"""Test the client."""
from __future__ import annotations

from unittest.mock import AsyncMock, call

from aiovlc.client import Client


async def test_client_connect_disconnect(transport: AsyncMock, client: Client) -> None:
    """Test the client transport connect and disconnect."""
    await client.connect()

    assert transport.call_count == 1
    assert transport.call_args == call(host="localhost", port=4212)

    await client.disconnect()

    mock_writer: AsyncMock = transport.return_value[1]
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1

    transport.reset_mock()
    mock_writer.reset_mock()

    async with client:
        assert transport.call_count == 1
        assert transport.call_args == call(host="localhost", port=4212)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
