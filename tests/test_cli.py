"""Test the CLI."""

from typer.testing import CliRunner

from aiovlc.cli import app

runner = CliRunner()


def test_help() -> None:
    """The help message includes the CLI name."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Start a client." in result.stdout
