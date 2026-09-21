"""Fetch files from a public Google Drive folder, as a convenience alongside upload.

PRD §4: an optional cloud-mode convenience, not the primary path — the
student pastes a link to a folder shared as "Anyone with the link can view."
Public-folder fetching is not a stable, documented API, so any failure here
must surface as a friendly message pointing back to upload rather than crash
the app.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class DriveFetchError(Exception):
    """Raised with a message that is safe to show directly in the UI."""


def fetch_drive_folder(url: str) -> list[tuple[str, bytes]]:
    """Download every file in a public Drive folder, as (filename, bytes) pairs
    matching the shape of an uploaded file list.

    Downloads to a temporary directory that is deleted as soon as the files
    are read into memory — nothing from this persists on disk.
    """
    import gdown

    url = url.strip()
    if not url:
        raise DriveFetchError("Paste a Google Drive folder link first.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            paths = gdown.download_folder(url=url, output=tmp_dir, quiet=True, use_cookies=False)
        except Exception as exc:  # noqa: BLE001 - gdown raises several exception types for bad/private links
            raise DriveFetchError(
                'Could not fetch that Drive folder. Make sure it\'s shared as "Anyone with the '
                "link can view\", that the link points at a folder (not a single file), and try "
                "again. You can always upload files instead."
            ) from exc

        if not paths:
            raise DriveFetchError(
                "That link didn't return any files. Check the folder is shared as \"Anyone with "
                'the link can view" and isn\'t empty.'
            )

        return [(Path(p).name, Path(p).read_bytes()) for p in paths if Path(p).is_file()]
