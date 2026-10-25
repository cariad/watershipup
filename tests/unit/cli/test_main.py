"""Tests for the command's entry point."""

import os
import subprocess
import sys
import sysconfig
from importlib.metadata import entry_points, version
from pathlib import Path

import pytest

from tests.file_helpers import touch_files
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


def test_empty_directory(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A directory with no files must exit 1, with an error, before any request."""
    monkeypatch.setenv("WATERSHIPUP_PASSWORD", "made-up")

    code = main(
        [
            "--zone",
            "example-zone",
            str(tmp_path),
        ],
    )

    err = capsys.readouterr().err
    expect = f"watershipup: error: No files to publish in {str(tmp_path)!r}\n"

    assert (code, err) == (1, expect)


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


def test_hidden_file(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A hidden file must exit 1, with an error, before any request."""
    monkeypatch.setenv("WATERSHIPUP_PASSWORD", "made-up")
    (tmp_path / ".env").touch()

    code = main(
        [
            "--zone",
            "example-zone",
            str(tmp_path),
        ],
    )

    err = capsys.readouterr().err

    expect = (
        "watershipup: error: Won't publish a hidden file or directory: "
        f"{str(tmp_path / '.env')!r}\n"
    )

    assert (code, err) == (1, expect)


@pytest.mark.parametrize(
    "password",
    [
        None,
        "",
    ],
)
def test_missing_password(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    password: str | None,
    tmp_path: Path,
) -> None:
    """A missing or empty password must exit 2, with an error."""
    if password is None:
        monkeypatch.delenv("WATERSHIPUP_PASSWORD", raising=False)
    else:
        monkeypatch.setenv("WATERSHIPUP_PASSWORD", password)

    code = main(
        [
            "--zone",
            "example-zone",
            str(tmp_path),
        ],
    )

    err = capsys.readouterr().err
    expect = "watershipup: error: WATERSHIPUP_PASSWORD must be set\n"

    assert (code, err) == (2, expect)


@pytest.mark.skipif(
    sys.platform == "darwin",
    reason="macOS can't create a name that isn't valid UTF-8",
)
def test_name_not_utf8(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A name that isn't valid UTF-8 must exit 1, with an error, before any request."""
    monkeypatch.setenv("WATERSHIPUP_PASSWORD", "made-up")

    touch_files(
        tmp_path,
        os.fsdecode(b"caf\xe9.html"),
    )

    code = main(
        [
            "--zone",
            "example-zone",
            str(tmp_path),
        ],
    )

    err = capsys.readouterr().err

    expect = (
        "watershipup: error: 'utf-8' codec can't encode character '\\udce9' in "
        "position 3: surrogates not allowed\n"
    )

    assert (code, err) == (1, expect)


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
    """Without arguments, the command must exit 2, with a usage error."""
    with pytest.raises(SystemExit) as caught:
        main([])

    assert caught.value.code == 2
    assert "watershipup: error: " in capsys.readouterr().err


def test_zone_with_line_break(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A line break in `--zone` must exit 1, with an error, before any request."""
    monkeypatch.setenv("WATERSHIPUP_PASSWORD", "made-up")

    touch_files(
        tmp_path,
        "index.html",
    )

    code = main(
        [
            "--zone",
            "example\nzone",
            str(tmp_path),
        ],
    )

    err = capsys.readouterr().err

    expect = (
        "watershipup: error: Invalid non-printable ASCII character in URL, '\\n' at "
        "position 36.\n"
    )

    assert (code, err) == (1, expect)
