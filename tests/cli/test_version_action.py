"""Tests for the command's `--version` option."""

from importlib.metadata import version

import pytest

from watershipup.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """`--version` must print the installed version, and exit 0."""
    with pytest.raises(SystemExit) as caught:
        main(["--version"])

    assert caught.value.code == 0
    assert capsys.readouterr().out == f"watershipup {version('watershipup')}\n"
