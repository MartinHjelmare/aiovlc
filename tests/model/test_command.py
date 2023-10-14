"""Test the commands."""
from __future__ import annotations

from typing import Any, Literal
from unittest.mock import AsyncMock, call

import pytest

from aiovlc.client import Client
from aiovlc.exceptions import (
    AuthError,
    CommandError,
    CommandParameterError,
    CommandParseError,
)


async def test_clear_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the clear command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.clear()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"clear\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "read, length",
    [(b"372\r\n> ", 372), (b"\r\n> ", 0)],
)
async def test_get_length_command(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    length: int,
) -> None:
    """Test the get length command."""
    mock_reader, mock_writer = transport.return_value
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
async def test_get_length_command_error(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    error: type[Exception],
    error_message: str,
) -> None:
    """Test the get length command errors."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = read

    with pytest.raises(error) as err:
        await client_connected.get_length()

    assert str(err.value) == error_message
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"get_length\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "read, time_result",
    [(b"8\r\n> ", 8), (b"\r\n> ", 0)],
)
async def test_get_time_command(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    time_result: int,
) -> None:
    """Test the get time command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = read

    output = await client_connected.get_time()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"get_time\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.time == time_result


@pytest.mark.parametrize(
    "read, error, error_message",
    [
        (b"> ", CommandParseError, "Could not get time."),
        (
            b"unexpected\r\n> ",
            CommandParseError,
            "Could not get time.",
        ),
    ],
)
async def test_get_time_command_error(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    error: type[Exception],
    error_message: str,
) -> None:
    """Test the get time command errors."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = read

    with pytest.raises(error) as err:
        await client_connected.get_time()

    assert str(err.value) == error_message
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"get_time\n")
    assert mock_reader.readuntil.call_count == 1


async def test_info_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the info command."""
    mock_reader, mock_writer = transport.return_value
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
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the info command error."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"unexpected\r\n" b"> "

    with pytest.raises(CommandError) as err:
        await client_connected.info()

    assert str(err.value) == "Unexpected line in info output: unexpected"

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"info\n")
    assert mock_reader.readuntil.call_count == 1


async def test_next_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the next command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.next()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"next\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "read, read_call_count",
    [([b"Welcome, Master\r\n", b"> "], 4), ([b"Welcome, Master> \r\n"], 3)],
)
async def test_password_command(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    read_call_count: int,
) -> None:
    """Test the password command."""
    password = "test-password"
    mock_reader, mock_writer = transport.return_value
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
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    error: type[Exception],
    error_message: str,
) -> None:
    """Test the password command errors."""
    password = "test-password"
    mock_reader, mock_writer = transport.return_value
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


async def test_pause_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the pause command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.pause()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"pause\n")
    assert mock_reader.readuntil.call_count == 1


async def test_play_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the play command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.play()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"play\n")
    assert mock_reader.readuntil.call_count == 1


async def test_prev_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the prev command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.prev()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"prev\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "mode, call_argument",
    [
        ("on", " on"),
        ("off", " off"),
        (None, ""),
    ],
)
async def test_random_command(
    transport: AsyncMock,
    client_connected: Client,
    mode: Literal["on", "off"] | None,
    call_argument: str,
) -> None:
    """Test the random command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.random(mode)

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(f"random{call_argument}\n".encode())
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "mode, error, error_message",
    [
        (
            "bad_mode",
            CommandParameterError,
            f"Parameter mode not in {(None, 'on', 'off')}",
        ),
        (
            42,
            CommandParameterError,
            f"Parameter mode not in {(None, 'on', 'off')}",
        ),
    ],
)
async def test_random_command_error(
    transport: AsyncMock,
    client_connected: Client,
    mode: Any,
    error: type[Exception],
    error_message: str,
) -> None:
    """Test the random command errors."""
    mock_reader, mock_writer = transport.return_value

    with pytest.raises(error) as err:
        await client_connected.random(mode)

    assert str(err.value) == error_message
    assert mock_reader.readuntil.call_count == 0
    assert mock_writer.write.call_count == 0


async def test_set_volume_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the set volume command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.set_volume(300)

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"volume 300\n")
    assert mock_reader.readuntil.call_count == 1


@pytest.mark.parametrize(
    "volume, error, error_message",
    [
        ("bad_volume", CommandParameterError, "Invalid volume parameter: bad_volume"),
        (
            9000,
            CommandParameterError,
            f"Parameter volume not in {range(500)}",
        ),
    ],
)
async def test_set_volume_command_error(
    transport: AsyncMock,
    client_connected: Client,
    volume: Any,
    error: type[Exception],
    error_message: str,
) -> None:
    """Test the set volume command errors."""
    mock_reader, mock_writer = transport.return_value

    with pytest.raises(error) as err:
        await client_connected.set_volume(volume)

    assert str(err.value) == error_message
    assert mock_reader.readuntil.call_count == 0
    assert mock_writer.write.call_count == 0


@pytest.mark.parametrize(
    "read, audio_volume, state, input_loc",
    [
        (b"( audio volume: 0 )\r\n( state stopped )\r\n> ",
         0, "stopped", None),
        (b"( audio volume: 0.0 )\r\n( state stopped )\r\n> ",
         0, "stopped", None),
        (b"( audio volume: 0,0 )\r\n( state stopped )\r\n> ",
         0, "stopped", None),
        (b"( new input: file:///path/to/music.mp3 )\r\n( audio volume: 128.0 )\r\n( state paused )\r\n> ",
         128, "paused", "file:///path/to/music.mp3"),
        (b"( new input: file:///home/felix/Musik/Madonna - Jump.ogg )\r\n( audio volume: 256.0 )\r\n( state playing )\r\n> ",
         256, "playing", "file:///home/felix/Musik/Madonna%20-%20Jump.ogg")
    ]
)
async def test_status_command(
    transport: AsyncMock,
    client_connected: Client,
    read: list[bytes],
    audio_volume: int,
    state: str,
    input_loc: str | None
) -> None:
    """Test the status command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = read

    output = await client_connected.status()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"status\n")
    assert mock_reader.readuntil.call_count == 1
    assert output
    assert output.audio_volume == audio_volume
    assert output.state == state
    if input_loc is None:
        assert output.input_loc is None
    else:
        assert output.input_loc == input_loc


async def test_stop_command(
    transport: AsyncMock,
    client_connected: Client,
) -> None:
    """Test the stop command."""
    mock_reader, mock_writer = transport.return_value
    mock_reader.readuntil.return_value = b"> "

    await client_connected.stop()

    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(b"stop\n")
    assert mock_reader.readuntil.call_count == 1
