"""Functions for summarising a publish."""

from ..publish_report import PublishReport


def summarise(report: PublishReport) -> str:
    """Describe what a publish did, in one sentence.

    Args:
        report: What the publish did.

    Returns:
        The summary, like "Uploaded 12 files, left 340 unchanged, deleted 2, and kept 3
        that are no longer in the directory."
    """
    uploaded = len(report.uploaded)
    kept = len(report.kept)

    files = "file" if uploaded == 1 else "files"
    are = "is" if kept == 1 else "are"

    return (
        f"Uploaded {uploaded} {files}, left {len(report.unchanged)} unchanged, "
        f"deleted {len(report.deleted)}, and kept {kept} that {are} no longer in the "
        "directory."
    )
