"""Tests for summarising a publish."""

from pytest import mark

from watershipup import PublishReport
from watershipup.cli.summaries import summarise


def _paths(count: int) -> tuple[str, ...]:
    """Make made-up storage zone paths.

    Args:
        count: How many paths to make.

    Returns:
        The paths.
    """
    return tuple(f"{index}.html" for index in range(count))


@mark.parametrize(
    ["report", "expect"],
    [
        (
            PublishReport(
                deleted=_paths(2),
                kept=_paths(3),
                unchanged=_paths(340),
                uploaded=_paths(12),
            ),
            "Uploaded 12 files, left 340 unchanged, deleted 2, and kept 3 that are no "
            "longer in the directory.",
        ),
        (
            PublishReport(
                deleted=(),
                kept=_paths(1),
                unchanged=(),
                uploaded=_paths(1),
            ),
            "Uploaded 1 file, left 0 unchanged, deleted 0, and kept 1 that is no "
            "longer in the directory.",
        ),
        (
            PublishReport(
                deleted=(),
                kept=(),
                unchanged=(),
                uploaded=(),
            ),
            "Uploaded 0 files, left 0 unchanged, deleted 0, and kept 0 that are no "
            "longer in the directory.",
        ),
    ],
)
def test_summarise(
    report: PublishReport,
    expect: str,
) -> None:
    """`summarise` must count what a publish did, in one sentence."""
    summary = summarise(report)
    assert summary == expect
