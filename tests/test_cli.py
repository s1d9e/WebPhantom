"""Tests for WebPhantom CLI."""

from click.testing import CliRunner
from webphantom.cli.main import main


def test_cli_version():
    """Test CLI version command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "WebPhantom" in result.output


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Browser Forensics Decoder" in result.output


def test_cli_detect():
    """Test CLI detect command."""
    runner = CliRunner()
    result = runner.invoke(main, ["detect"])
    assert result.exit_code == 0
    assert "Detected Browser Profiles" in result.output


def test_cli_scan_nonexistent():
    """Test CLI scan with nonexistent path."""
    runner = CliRunner()
    result = runner.invoke(main, ["scan", "/nonexistent/path"])
    assert result.exit_code != 0


def test_cli_walinfo_nonexistent():
    """Test CLI walinfo with nonexistent file."""
    runner = CliRunner()
    result = runner.invoke(main, ["walinfo", "/nonexistent/file.db"])
    assert result.exit_code != 0
