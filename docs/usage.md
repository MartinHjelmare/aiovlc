# Usage

Here's an example of how to use the library to connect to a VLC instance:

```python
from aiovlc.client import Client
from aiovlc.exceptions import AIOVLCError
from aiovlc.model.command import Info, Status

LOGGER = logging.getLogger("aiovlc")


def run_client() -> None:
    """Run a VLC client."""
    LOGGER.info("Starting client")
    host = "localhost"
    password = "a1ve3ry4ha6rd7pas9wo1rd"
    port = 4212
    try:
        asyncio.run(start_client(host, password, port))
    except KeyboardInterrupt:
        pass
    finally:
        LOGGER.info("Stopped client")


async def start_client(host: str, password: str, port: int) -> None:
    """Start the client."""
    try:
        async with Client(password, host=host, port=port) as vlc_client:
            await vlc_client.login()
            await handle_client(vlc_client)
    except AIOVLCError as err:
        LOGGER.error("Error '%s'", err)


async def handle_client(vlc_client: Client) -> None:
    """Handle the client calls."""
    while True:
        command = Status()
        output = await command.send(vlc_client)
        LOGGER.debug("Received: %s", output)
        info_command = Info()
        info_output = await info_command.send(vlc_client)
        LOGGER.debug("Received: %s", info_output)
        await asyncio.sleep(10)


if __name__ == "__main__":
    run_client()
```

There's also a CLI to test the library.

```sh
aiovlc --debug client
```
