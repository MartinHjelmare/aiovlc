"""Provide exceptions for aiovlc."""

from __future__ import annotations


class AIOVLCError(Exception):
    """Represent a common error for aiovlc."""


class ConnectError(AIOVLCError):
    """Represent a connection error for aiovlc."""


class ConnectReadError(ConnectError):
    """The client failed to read."""

    def __init__(self, error: Exception, partial_bytes: bytes | None = None) -> None:
        """Set up error."""
        message = f"Failed to read: {error}."

        if partial_bytes is not None:
            message = f"{message} Partial bytes read: {partial_bytes!r}"

        super().__init__(message)
        self.partial_bytes = partial_bytes


class AuthError(AIOVLCError):
    """Represent an authentication error."""


class CommandError(AIOVLCError):
    """Represent a command error."""


class CommandParameterError(CommandError):
    """Represent an error with a parameter when calling the command."""


class CommandParseError(CommandError):
    """Represent an error when parsing the command output."""
