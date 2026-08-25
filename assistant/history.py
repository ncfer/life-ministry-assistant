"""Sending log: who has received their assignment, when, and whether it
failed, so it can be checked or only the ones that didn't arrive can be
retried."""
from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

# Column headers are English going forward; `load_history()` below
# normalizes an old file (Spanish headers, what every history.csv/
# reminder_history.csv written before 2026-08-24 has) to these same keys
# on read, so every caller only ever deals with one set of names — same
# legacy pattern as config.py/contacts.py. Only the HEADER row changes;
# the "status" column's own values ("enviado"/"fallido") are untouched,
# same as message content elsewhere.
HEADER = ["timestamp", "assignment_date", "name", "phone", "status", "reason"]
_LEGACY_HEADER = {
    "assignment_date": "fecha_asignacion",
    "name": "nombre",
    "phone": "telefono",
    "status": "estado",
    "reason": "motivo",
}


def log_entry(
    history_path: Path,
    assignment_date: date,
    name: str,
    phone: str,
    success: bool,
    reason: str = "",
) -> None:
    history_path = Path(history_path)
    exists = history_path.exists()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(HEADER)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            assignment_date.isoformat(),
            name,
            phone,
            "enviado" if success else "fallido",
            reason,
        ])


def load_history(history_path: Path) -> list[dict]:
    """Returns dicts keyed by the new English names (`HEADER` above)
    regardless of whether the file on disk still has the old Spanish
    header — every caller only has to handle one set of keys."""
    history_path = Path(history_path)
    if not history_path.exists():
        return []
    with open(history_path, newline="", encoding="utf-8") as f:
        rows = [
            {
                key: raw.get(key) or raw.get(_LEGACY_HEADER.get(key, key), "")
                for key in HEADER
            }
            for raw in csv.DictReader(f)
        ]
    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows
