"""Tests for storage zone listings."""

import json

from pytest import mark, raises

from tests.checksum_helpers import checksum_of
from watershipup.zone_file import ZoneFile
from watershipup.zone_listing import ZoneListing
from watershipup.zone_listings import is_valid_directory, is_valid_name, parse_listing


def _entry(
    name: str,
    *,
    checksum: str | None = None,
    content_type: str = "",
    is_directory: bool = False,
    path: str = "/example-zone/",
) -> dict[str, object]:
    """Make a listing entry, with every field that bunny.net sends.

    Args:
        name: The entry's `ObjectName`.
        checksum: The entry's `Checksum`.
        content_type: The entry's `ContentType`.
        is_directory: The entry's `IsDirectory`.
        path: The entry's `Path`.

    Returns:
        The entry.
    """
    return {
        "ArrayNumber": 0,
        "Checksum": checksum,
        "ContentType": content_type,
        "DateCreated": "2026-01-01T12:00:00",
        "Guid": "00000000-0000-0000-0000-000000000000",
        "IsDirectory": is_directory,
        "LastChanged": "2026-01-01T12:00:00.25",
        "Length": 0,
        "ObjectName": name,
        "Path": path,
        "ReplicatedZones": None if is_directory else "",
        "ServerId": 0,
        "StorageZoneId": 0,
        "StorageZoneName": "example-zone",
        "UserId": "00000000-0000-0000-0000-000000000000",
    }


@mark.parametrize(
    "directory",
    [
        "",
        "css/",
        "css/fonts/",
        "about us/",
        "café/",
    ],
)
def test_is_valid_directory(directory: str) -> None:
    """`is_valid_directory` must be true for the root, or names that each end in "/"."""
    valid = is_valid_directory(directory)
    assert valid


@mark.parametrize(
    "directory",
    [
        "css",
        "css/fonts",
        "/",
        "/css/",
        "css//",
        "./",
        "../",
        "css/../",
        "\ud800/",
    ],
)
def test_is_valid_directory_when_invalid(directory: str) -> None:
    """`is_valid_directory` must be false for each kind of invalid directory path."""
    valid = is_valid_directory(directory)
    assert not valid


@mark.parametrize(
    "name",
    [
        "index.html",
        "fonts",
        "about us.html",
        "café",
        "...",
        "\U0001f600.png",
        # Refused by `has_invalid_name`, but not here.
        " index.html",
        "index.html ",
        "zero​width.html",
        "bell\x07.html",
    ],
)
def test_is_valid_name(name: str) -> None:
    """`is_valid_name` must be true for a name that can be part of a path."""
    valid = is_valid_name(name)
    assert valid


@mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "/",
        "css/site.css",
        "\ud800",
        "lone\udfffsurrogate.html",
    ],
)
def test_is_valid_name_when_invalid(name: str) -> None:
    """`is_valid_name` must be false for each kind of invalid name."""
    valid = is_valid_name(name)
    assert not valid


def test_parse_listing() -> None:
    """`parse_listing` must record each file's path, checksum and type."""
    index_checksum = checksum_of(b"made-up index")
    manifest_checksum = checksum_of(b"made-up manifest")

    content = json.dumps(
        [
            _entry(
                "index.html",
                checksum=index_checksum,
            ),
            _entry(
                "site.webmanifest",
                checksum=manifest_checksum,
                content_type="application/manifest+json",
            ),
        ]
    ).encode()

    listing = parse_listing(
        "",
        content,
    )

    expect = ZoneListing(
        files=(
            ZoneFile("index.html", index_checksum, ""),
            ZoneFile(
                "site.webmanifest",
                manifest_checksum,
                "application/manifest+json",
            ),
        ),
        directories=(),
    )

    assert listing == expect


def test_parse_listing_directories() -> None:
    """`parse_listing` must record each subdirectory's path, ending in "/"."""
    content = json.dumps(
        [
            _entry(
                "fonts",
                is_directory=True,
            ),
        ]
    ).encode()

    listing = parse_listing(
        "css/",
        content,
    )

    expect = ZoneListing(files=(), directories=("css/fonts/",))

    assert listing == expect


def test_parse_listing_empty() -> None:
    """`parse_listing` must find nothing in an empty listing."""
    listing = parse_listing("", b"[]")
    expect = ZoneListing(files=(), directories=())

    assert listing == expect


def test_parse_listing_ignores_directory_fields() -> None:
    """`parse_listing` must not read a directory's `Checksum` or `ContentType`."""
    content = json.dumps(
        [
            {
                **_entry("fonts", is_directory=True),
                "Checksum": 0,
                "ContentType": 0,
            },
        ]
    ).encode()

    listing = parse_listing(
        "css/",
        content,
    )

    expect = ZoneListing(files=(), directories=("css/fonts/",))

    assert listing == expect


def test_parse_listing_ignores_path() -> None:
    """`parse_listing` must build each path from the directory, not `Path`."""
    content = json.dumps(
        [
            _entry(
                "site.css",
                path="/example-zone/elsewhere/",
            ),
        ]
    ).encode()

    listing = parse_listing(
        "css/",
        content,
    )

    expect = ZoneListing(files=(ZoneFile("css/site.css", None, ""),), directories=())

    assert listing == expect


@mark.parametrize(
    "content",
    [
        b'{"HttpCode":401,"Message":"Unauthorized"}',
        b"null",
    ],
)
def test_parse_listing_refuses_body(content: bytes) -> None:
    """`parse_listing` must refuse a body that isn't a JSON array."""
    with raises(ValueError, match="isn't a JSON array"):
        parse_listing("", content)


@mark.parametrize(
    "entries",
    [
        [_entry("index.html"), _entry("index.html")],
        [_entry("fonts"), _entry("fonts", is_directory=True)],
    ],
)
def test_parse_listing_refuses_duplicate_name(
    entries: list[dict[str, object]],
) -> None:
    """`parse_listing` must refuse a listing that has a name more than once."""
    content = json.dumps(entries).encode()

    with raises(ValueError, match="more than once"):
        parse_listing("", content)


@mark.parametrize(
    ["entry", "match"],
    [
        ("index.html", "without a string ObjectName"),
        ({**_entry("index.html"), "ObjectName": None}, "without a string ObjectName"),
        (_entry(""), "invalid ObjectName"),
        (_entry("."), "invalid ObjectName"),
        (_entry(".."), "invalid ObjectName"),
        (_entry("css/site.css"), "invalid ObjectName"),
        (_entry("\ud800"), "invalid ObjectName"),
        ({**_entry("index.html"), "IsDirectory": "false"}, "invalid IsDirectory"),
        ({**_entry("index.html"), "IsDirectory": None}, "invalid IsDirectory"),
        ({**_entry("index.html"), "Checksum": 0}, "invalid Checksum"),
        ({**_entry("index.html"), "ContentType": 0}, "invalid ContentType"),
    ],
)
def test_parse_listing_refuses_entry(
    entry: object,
    match: str,
) -> None:
    """`parse_listing` must refuse an entry whose name or fields it can't use."""
    content = json.dumps([entry]).encode()

    with raises(ValueError, match=match):
        parse_listing("", content)


def test_parse_listing_uppercases_checksum() -> None:
    """`parse_listing` must record each checksum in uppercase."""
    checksum = checksum_of(b"made-up index")

    content = json.dumps(
        [
            _entry(
                "index.html",
                checksum=checksum.lower(),
            ),
        ]
    ).encode()

    listing = parse_listing(
        "",
        content,
    )

    expect = ZoneListing(files=(ZoneFile("index.html", checksum, ""),), directories=())

    assert listing == expect


@mark.parametrize(
    "entry",
    [
        _entry("index.html"),
        _entry("index.html", checksum=""),
        {**_entry("index.html"), "ContentType": None},
        {
            key: value
            for key, value in _entry("index.html").items()
            if key not in ("Checksum", "ContentType")
        },
    ],
)
def test_parse_listing_without_checksum_or_type(entry: dict[str, object]) -> None:
    """`parse_listing` must record no checksum as `None`, and no type as ""."""
    content = json.dumps([entry]).encode()

    listing = parse_listing(
        "",
        content,
    )

    expect = ZoneListing(files=(ZoneFile("index.html", None, ""),), directories=())

    assert listing == expect
