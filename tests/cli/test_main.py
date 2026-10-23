"""Tests for the command's entry point."""

import subprocess
import sysconfig
from importlib.metadata import entry_points, version
from pathlib import Path

import pytest

from watershipup.cli import main


def test_console_script() -> None:
    """The `watershipup` console script must run `main`."""
    (script,) = entry_points(
        group="console_scripts",
        name="watershipup",
    )

    assert script.load() is main


def test_console_script_runs() -> None:
    """The installed `watershipup` command must run."""
    command = Path(sysconfig.get_path("scripts")) / "watershipup"

    result = subprocess.run(
        [command, "--version"],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )

    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout == f"watershipup {version('watershipup')}\n"


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    """`--help` must describe the command, and exit 0."""
    with pytest.raises(SystemExit) as caught:
        main(["--help"])

    assert caught.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: watershipup ")

    # argparse wraps the description to the terminal's width.
    description = "Upload a static website to a Bunny Storage zone."
    assert description in " ".join(out.split())


def test_no_colour(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Help and usage errors must be plain text, even when colour is forced."""
    # Either would turn colour off, and let the test pass without the fix.
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("PYTHON_COLORS", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")

    with pytest.raises(SystemExit):
        main(["--help"])

    with pytest.raises(SystemExit):
        main(["--unknown"])

    output = capsys.readouterr()

    assert "\x1b" not in output.out
    assert "\x1b" not in output.err
    assert "watershipup: error: " in output.err


def test_unknown_argument(capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown argument must exit 2, with a usage error."""
    with pytest.raises(SystemExit) as caught:
        main(["--unknown"])

    assert caught.value.code == 2
    assert "watershipup: error: " in capsys.readouterr().err


def test_without_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    """Without arguments, the command must do nothing yet, and exit 0."""
    assert main([]) == 0
    assert capsys.readouterr() == ("", "")
