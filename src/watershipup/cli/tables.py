"""Functions for tabulating a plan or a publish report."""

from ..plan import Plan
from ..publish_report import PublishReport
from ..upload_round import UploadRound
from ..upload_rounds import round_of

ROUND_TITLES = {
    UploadRound.ASSETS: "Assets",
    UploadRound.PAGES: "Pages",
    UploadRound.FEEDS: "Feeds",
}
"""The title of each round's table."""


def _rows(
    source: Plan | PublishReport,
) -> dict[UploadRound, list[tuple[str, str]]]:
    """List each round's changes.

    Args:
        source: The plan or the publish report.

    Returns:
        The storage zone paths of the uploads and deletions in each round with
        changes, with "Upload" or "Delete" for a plan, or "Uploaded" or "Deleted" for
        a publish report, sorted by path.
    """
    if isinstance(source, Plan):
        changes = [
            *((local_file.remote_path, "Upload") for local_file in source.uploads),
            *((remote_path, "Delete") for remote_path in source.deletions),
        ]
    else:
        changes = [
            *((remote_path, "Uploaded") for remote_path in source.uploaded),
            *((remote_path, "Deleted") for remote_path in source.deleted),
        ]

    rows: dict[UploadRound, list[tuple[str, str]]] = {
        upload_round: [] for upload_round in UploadRound
    }

    for remote_path, change in changes:
        rows[round_of(remote_path)].append(
            (
                remote_path,
                change,
            ),
        )

    for round_rows in rows.values():
        round_rows.sort()

    return {
        upload_round: round_rows
        for upload_round, round_rows in rows.items()
        if round_rows
    }


def tabulate_markdown(
    source: Plan | PublishReport,
) -> str:
    """Tabulate a plan's or a publish report's changes as Markdown.

    Args:
        source: The plan or the publish report.

    Returns:
        A table for each round with changes, or "No changes." when there are none.
    """
    rounds = _rows(source)

    if not rounds:
        return "No changes."

    tables: list[str] = []

    for upload_round, rows in rounds.items():
        lines = [
            f"### {ROUND_TITLES[upload_round]}",
            "",
            "| Path | Change |",
            "| - | - |",
            *(f"| `{path}` | {change} |" for path, change in rows),
        ]

        tables.append("\n".join(lines))

    return "\n\n".join(tables)


def tabulate_text(
    source: Plan | PublishReport,
) -> str:
    """Tabulate a plan's or a publish report's changes as plain text.

    Args:
        source: The plan or the publish report.

    Returns:
        A table for each round with changes, or "No changes." when there are none.
    """
    rounds = _rows(source)

    if not rounds:
        return "No changes."

    width = max(
        len("Path"),
        *(len(path) for rows in rounds.values() for path, _ in rows),
    )

    tables: list[str] = []

    for upload_round, rows in rounds.items():
        lines = [
            ROUND_TITLES[upload_round],
            "",
            f"{'Path':<{width}}  Change",
            *(f"{path:<{width}}  {change}" for path, change in rows),
        ]

        tables.append("\n".join(lines))

    return "\n\n".join(tables)
