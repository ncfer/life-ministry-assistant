"""Weekday/month names and date formatting, without relying on the
system locale (unreliable across Linux/Windows/Mac).

Spanish and English names are both built in; `long_date()` and
`date_with_weekday()` pick between them based on the current UI language
(`i18n.current_language()`) — a congregation running the app in English
gets English dates in the messages it sends and on the S-89 slip, not
just in the app's own menus. (`WEEKDAYS`/`MONTHS` stay exported as the
Spanish lists for anything that was already importing them directly;
new code should go through `weekday_name()`/`month_name()` instead so it
follows the UI language.)"""
from __future__ import annotations

from datetime import date, timedelta

from . import i18n

WEEKDAYS = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
WEEKDAYS_EN = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]
MONTHS_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def weekday_name(weekday_index: int) -> str:
    names = WEEKDAYS_EN if i18n.current_language() == "en" else WEEKDAYS
    return names[weekday_index]


def month_name(month: int) -> str:
    """`month` is 1-12, matching `date.month`."""
    names = MONTHS_EN if i18n.current_language() == "en" else MONTHS
    return names[month - 1]


def long_date(d: date) -> str:
    """"12 de agosto de 2026" (Spanish UI) / "August 12, 2026" (English UI)."""
    if i18n.current_language() == "en":
        return f"{month_name(d.month)} {d.day}, {d.year}"
    return f"{d.day} de {month_name(d.month)} de {d.year}"


def date_with_weekday(d: date) -> str:
    """"miércoles 12 de agosto" (Spanish UI) / "Wednesday, August 12" (English UI)."""
    if i18n.current_language() == "en":
        return f"{weekday_name(d.weekday())}, {month_name(d.month)} {d.day}"
    return f"{weekday_name(d.weekday())} {d.day} de {month_name(d.month)}"


def week_start(d: date) -> date:
    """Monday of the calendar week (Monday-Sunday) `d` falls in — used to
    compare two dates "by week" regardless of which weekday each one is."""
    return d - timedelta(days=d.weekday())


def next_month(d: date) -> tuple[int, int]:
    """(year, month) of the calendar month right after `d`'s, wrapping
    December -> January of the next year."""
    if d.month == 12:
        return d.year + 1, 1
    return d.year, d.month + 1
