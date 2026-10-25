"""Integration tests for the command."""

from pathlib import Path
from uuid import uuid4

import pytest

from tests.file_helpers import write_files
from watershipup.cli import main

from .storage_zone import environment_variable


def _publish(directory: Path) -> int:
    """Run the command to publish a directory to the test zone.

    Args:
        directory: The directory to publish.

    Returns:
        The command's exit code.
    """
    return main(
        [
            "--zone",
            environment_variable("WATERSHIPUP_TEST_ZONE"),
            str(directory),
        ]
    )


def test_main(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """`main` must publish the directory, say what it did, and exit 0."""
    # The command reads only this variable, so it's set here from the test's own.
    monkeypatch.setenv(
        "WATERSHIPUP_PASSWORD",
        environment_variable("WATERSHIPUP_TEST_PASSWORD"),
    )

    write_files(
        tmp_path,
        {
            "test_main/index.html": uuid4().bytes,
            "test_main/old.css": uuid4().bytes,
            "test_main/old.html": uuid4().bytes,
        },
    )

    first = _publish(tmp_path)
    first_err = capsys.readouterr().err

    assert (first, first_err) == (0, "")

    # Different on every run, so the page is always uploaded.
    (tmp_path / "test_main/index.html").write_bytes(uuid4().bytes)
    (tmp_path / "test_main/old.css").unlink()
    (tmp_path / "test_main/old.html").unlink()

    code = _publish(tmp_path)
    output = capsys.readouterr()
    lines = output.out.splitlines()

    # The zone can hold other files that are no longer in the directory, so only this
    # test's lines are looked for, in the order printed, and only the start of the
    # summary.
    expect = [
        "Uploaded 'test_main/index.html'",
        "Deleted 'test_main/old.html'",
        "Kept 'test_main/old.css', which is no longer in the directory",
    ]

    found = [line for line in lines if line in expect]

    assert (code, output.err) == (0, "")
    assert found == expect
    assert lines[-1].startswith("Uploaded 1 file, left 0 unchanged, deleted ")
