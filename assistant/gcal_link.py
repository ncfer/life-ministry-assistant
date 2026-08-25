"""Generates the "Add to Google Calendar" link, in the same format the
original xlsm's 0_CALENDAR sheet already used (cell B4: the base URL).
"""
from __future__ import annotations

import urllib.parse

from .i18n import t
from .models import Assignment

BASE_URL = "https://calendar.google.com/calendar/event?action=TEMPLATE"
START_TIME = "194500"
END_TIME = "213000"


def generate_gcal_link(assignment: Assignment) -> str:
    event_date = assignment.date.strftime("%Y%m%d")
    dates = f"{event_date}T{START_TIME}/{event_date}T{END_TIME}"
    title = t(
        "calendario.titulo_evento",
        numero=assignment.number, tipo=assignment.part, nombre=assignment.name.upper(),
    )
    query = urllib.parse.urlencode({"dates": dates, "text": title})
    return f"{BASE_URL}&{query}"
