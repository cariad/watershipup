"""Functions for tabulating a plan."""

from ..plan import Plan
from ..upload_round import UploadRound
from ..upload_rounds import round_of

ROUND_TITLES = {
    UploadRound.ASSETS: "Assets",
    UploadRound.PAGES: "Pages",
    UploadRound.FEEDS: "Feeds",
}
"""The title of each round's table."""


def _rows(plan: Plan) -> dict[UploadRound, list[tuple[str, str]]]:
    """List each round's changes.

    Args:
        plan: The plan.

    Returns:
        Each round's storage zone paths to upload or delete, with "Upload" or
        "Delete", sorted by path.
    """
    rows: dict[UploadRound, list[tuple[str, str]]] = {
        upload_round: [] for upload_round in UploadRound
    }

    for local_file in plan.uploads:
        rows[round_of(local_file.remote_path)].append(
            (
                local_file.remote_path,
                "Upload",
            ),
        )

    for remote_path in plan.deletions:
        rows[round_of(remote_path)].append(
            (
                remote_path,
                "Delete",
            ),
        )

    for round_rows in rows.values():
        round_rows.sort()

    return rows


def tabulate_text(plan: Plan) -> str:
    """Tabulate a plan's changes as plain text.

    Args:
        plan: The plan.

    Returns:
        A table for each round with changes, or "No changes." when there are none.
    """
    rounds = {upload_round: rows for upload_round, rows in _rows(plan).items() if rows}

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
