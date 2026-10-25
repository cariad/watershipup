"""Functions for storage zone paths."""


def extension_of(remote_path: str) -> str:
    """Find a file's extension.

    A file's extension is the part of its name after the last dot, unless that dot
    starts the name.

    Args:
        remote_path: The file's storage zone path, like "css/site.css".

    Returns:
        The file's extension in lowercase, like "css", or "" if it has none.
    """
    leaf = remote_path.rsplit("/", 1)[-1]
    dot = leaf.rfind(".")

    return leaf[dot + 1 :].lower() if dot > 0 else ""
