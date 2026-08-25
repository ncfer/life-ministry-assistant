"""Data model shared across the project's modules."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from .i18n import t

Room = Literal["principal", "aux1", "aux2"]

# Evaluated at import time (same pattern as widgets.STEPS) — fine because
# the language is already set before this module is first imported from
# the GUI. CLI usage (which never calls i18n.set_language) gets the
# default language, same as it always has.
ROOM_LABEL: dict[Room, str] = {
    "principal": t("room.principal"),
    "aux1": t("room.aux1"),
    "aux2": t("room.aux2"),
}


@dataclass
class Assignment:
    name: str
    helper: str
    date: date
    number: str
    part: str
    room: Room = "principal"
    phone: str | None = None
