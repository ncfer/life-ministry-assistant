"""Removes generated slips/images from output/ once they're old enough
to be useless regardless of whether they were ever sent — called once at
app startup (see gui/app.py). A file whose own meeting already happened
weeks ago has no purpose anymore, sent or not: there's no "maybe I'll
retry this later" case once the date itself is in the past, unlike
sending_progress.py's per-send cleanup (which only removes a file right
after a confirmed successful send, see gui/pages/sending_progress.py and
gui/pages/reminder_sending.py).
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

MAX_AGE_DAYS = 14

# Every file generated under output/ starts with its own meeting's date
# (see workers.py: "{fecha.isoformat()} - ..."), regardless of whether
# it's a slip (assignment) or a reminder crop.
_RE_LEADING_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def cleanup_old_output(output_folder: str | Path, max_age_days: int = MAX_AGE_DAYS, today: date | None = None) -> int:
    """Deletes every file under `output_folder` whose own meeting date is
    more than `max_age_days` in the past. Files that don't match the
    "YYYY-MM-DD - ..." naming are left alone — never guess, only act on
    what's unambiguous. Also removes any month folder left empty by this.
    Returns how many files were deleted. Never raises: this runs
    unconditionally on every app startup, so a folder it can't read
    (permissions, a network drive hiccup) should never block opening the
    app — it just skips cleanup for this run."""
    output_folder = Path(output_folder)
    if not output_folder.exists():
        return 0
    today = today or date.today()
    cutoff = today - timedelta(days=max_age_days)

    deleted = 0
    try:
        paths = list(output_folder.rglob("*"))
    except OSError:
        return 0

    for path in paths:
        if not path.is_file():
            continue
        m = _RE_LEADING_DATE.match(path.name)
        if not m:
            continue
        try:
            file_date = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if file_date < cutoff:
            try:
                path.unlink()
                deleted += 1
            except OSError:
                pass

    try:
        for folder in output_folder.iterdir():
            if folder.is_dir():
                try:
                    folder.rmdir()  # only succeeds if now empty
                except OSError:
                    pass
    except OSError:
        pass

    return deleted
