"""Generates .ics files for an assignment, replicating the template from
the PLANTILLA ASIGNACIONES.xlsm's Módulo2 (ExportarICSdesdeTabla1) VBA
macro.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from .i18n import t
from .models import Assignment

LOCATION = "https://maps.app.goo.gl/QPitn2RsavrCPPaT9"
START_TIME = "194500"
END_TIME = "213000"


def _ics_date(event_date: date, time_str: str) -> str:
    return f"{event_date.strftime('%Y%m%d')}T{time_str}"


def generate_ics(assignment: Assignment) -> str:
    dtstart = _ics_date(assignment.date, START_TIME)
    dtend = _ics_date(assignment.date, END_TIME)
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = t("calendario.titulo_evento_ics", numero=assignment.number, tipo=assignment.part, nombre=assignment.name)
    # Per-event unique UID (the original macro used a fixed "12345", which
    # made some calendar clients collapse several events into one).
    # Deterministic so the same .ics can be regenerated.
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{assignment.name}-{dtstart}")

    # RFC 5545 doesn't allow stray blank lines inside VCALENDAR (only
    # "name:value" or component BEGIN/END). Google's parser just ignores
    # them, but Apple Calendar/Mail's is much stricter and with blank
    # lines in between it can show the file without ever offering "Add to
    # calendar". METHOD:PUBLISH and CALSCALE:GREGORIAN aren't strictly
    # required either, but it's the recommended combination for Apple to
    # recognize a standalone .ics (no organizer/attendees) as an
    # importable event instead of treating it as a generic attachment.
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//AnandChowdhary//calendar-link//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"DTSTAMP:{dtstamp}\r\n"
        f"SUMMARY:{summary}\r\n"
        "DESCRIPTION:\r\n"
        f"LOCATION:{LOCATION}\r\n"
        f"UID:{uid}\r\n"
        "BEGIN:VALARM\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:{t('calendario.aviso_1_semana')}\r\n"
        "TRIGGER:-P1W\r\n"
        "END:VALARM\r\n"
        "BEGIN:VALARM\r\n"
        "ACTION:DISPLAY\r\n"
        f"DESCRIPTION:{t('calendario.aviso_1_dia')}\r\n"
        "TRIGGER:-P1D\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def write_ics(assignment: Assignment, path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(generate_ics(assignment))
