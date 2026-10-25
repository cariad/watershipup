"""Tests for URLs."""

from pytest import mark, raises

from watershipup.urls import make_zone_url


@mark.parametrize(
    ["remote_path", "expect"],
    [
        (
            "index.html",
            "https://storage.bunnycdn.com/foo/index.html",
        ),
        (
            "test_upload/file +#%41.txt",
            "https://storage.bunnycdn.com/foo/test_upload/file%20%2B%23%2541.txt",
        ),
    ],
)
def test_make_zone_url(
    remote_path: str,
    expect: str,
) -> None:
    """`make_zone_url` must create a properly encoded URL."""
    url = make_zone_url("foo", remote_path)

    assert url == expect


@mark.parametrize(
    "remote_path",
    [
        ".",
        "css/..",
        "../index.html",
    ],
)
def test_make_zone_url_refuses_dot_segment(remote_path: str) -> None:
    """`make_zone_url` must refuse a path with a "." or ".." segment."""
    with raises(ValueError, match="dot segment"):
        make_zone_url("foo", remote_path)
