"""Test the client."""
from __future__ import annotations

from unittest.mock import AsyncMock, call

import pytest

from aiovlc.client import Client
from aiovlc.exceptions import ConnectError


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


async def test_client_connect_failure(transport: AsyncMock, client: Client) -> None:
    """Test the client transport connect failure."""
    transport.side_effect = OSError("Boom")

    with pytest.raises(ConnectError) as err:
        await client.connect()

    assert str(err.value) == "Failed to connect: Boom"


async def test_client_disconnect_failure(transport: AsyncMock, client: Client) -> None:
    """Test the client transport disconnect failure."""
    mock_writer: AsyncMock = transport.return_value[1]
    mock_writer.wait_closed.side_effect = OSError("Boom")

    await client.connect()
    # Disconnect error should be caught.
    await client.disconnect()

    assert transport.call_count == 1
    assert transport.call_args == call(host="localhost", port=4212)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_client_read_write(transport: AsyncMock, client: Client) -> None:
    """Test the client transport read and write."""
    mock_reader: AsyncMock = transport.return_value[0]
    mock_writer: AsyncMock = transport.return_value[1]
    bytes_messages = [b"\xff\xfb\x01\xff\xfc\x01\r\n", b"> "]
    mock_reader.readuntil.side_effect = bytes_messages

    await client.connect()

    assert transport.call_count == 1
    assert transport.call_args == call(host="localhost", port=4212)

    read = await client.read()
    assert read == "> "

    message = "stop\n"

    await client.write("stop\n")
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(message.encode())

    await client.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
