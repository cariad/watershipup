"""Tests for publishing."""

from pathlib import Path

from pytest import mark, raises

from watershipup.publishing import publish


@mark.parametrize(
    "concurrency",
    [0, 17, True],
)
def test_publish_rejects_concurrency(
    concurrency: int,
    tmp_path: Path,
) -> None:
    """`publish` must refuse a concurrency that isn't an `int` from 1 to 16."""
    with raises(ValueError, match="Concurrency must be 1 to 16: "):
        publish(
            tmp_path,
            concurrency=concurrency,
            password="made-up",
            zone="made-up",
        )
