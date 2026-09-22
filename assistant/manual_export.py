"""Dumps generated slips into a folder so they can be sent by hand.

The escape hatch for when WhatsApp Web refuses to cooperate (a changed
selector, an expired session, no browser): everything the app would
have sent is already on disk, so this just gathers it per person —
image, calendar file and the exact message text, phone number
included — into one folder the user picks. Nothing is regenerated and
nothing is deleted; it's a copy.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .models import Assignment
from .reminder_workbook import Participant
from .send_reminders import format_reminder_message
from .whatsapp_send import ReminderMode, format_message, load_message_template

# Characters Windows forbids in a file name. The assignment names
# themselves are people's names (accents are fine, those aren't touched)
# but a stray "/" in a surname would otherwise create a subfolder.
_INVALID = '<>:"/\\|?*'


def safe_name(name: str) -> str:
    cleaned = "".join("-" if c in _INVALID else c for c in name).strip(" .")
    return cleaned or "sin-nombre"


def export_for_manual_send(
    items: list[tuple[Assignment, Path, Path]],
    destination: Path,
    template_path: Path,
    mode: ReminderMode = "ambos",
) -> list[Path]:
    """Copies each item into `destination/<person>/` and writes the
    message next to it. Returns the folders actually created.

    items are the same (assignment, jpg, ics) triples send_assignments
    takes, so a failed send can be re-exported without rebuilding
    anything.
    """
    template = load_message_template(template_path)
    destination.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for assignment, jpg, ics in items:
        folder = destination / safe_name(assignment.name)
        folder.mkdir(parents=True, exist_ok=True)

        for source in (jpg, ics):
            # The .ics is skipped when the user picked the link-only
            # reminder mode, and a missing file shouldn't abort the
            # whole export for everyone else.
            if source and Path(source).exists():
                if source == ics and mode == "gcal":
                    continue
                shutil.copy2(source, folder / Path(source).name)

        phone = assignment.phone or ""
        text = format_message(assignment, template, mode)
        (folder / "mensaje.txt").write_text(
            f"{phone}\n\n{text}\n", encoding="utf-8"
        )
        created.append(folder)
    return created


def export_reminders_for_manual_send(
    items: list[tuple[Participant, Path]],
    destination: Path,
    template_path: Path,
) -> list[Path]:
    """Same as export_for_manual_send, for the reminders flow.

    Reminders have no .ics and every participant shares the same week
    image, so the image is copied once per person's folder — a folder
    someone can open and forward as-is is worth more than saving a few
    hundred kilobytes.
    """
    template = load_message_template(template_path)
    destination.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for participant, jpg in items:
        folder = destination / safe_name(participant.name)
        folder.mkdir(parents=True, exist_ok=True)
        if jpg and Path(jpg).exists():
            shutil.copy2(jpg, folder / Path(jpg).name)
        (folder / "mensaje.txt").write_text(
            f"{participant.phone or ''}\n\n{format_reminder_message(participant, template)}\n",
            encoding="utf-8",
        )
        created.append(folder)
    return created
