"""VMC meeting-participation reminders: unlike parse_workbook.py (which only
extracts what carries an S-89-S slip), this module extracts EVERY named
role in the meeting — Treasures talk, Digging for Spiritual Gems, Bible
reading, Apply Yourself to the Field Ministry items with a helper,
Living as Christians talks, Conductor/Reader of the Congregation Bible
Study, opening and closing prayer — except the Chairman. It also
generates the cropped image of each week (to send the same program photo
to everyone taking part that week).

parse_workbook.py itself is never touched: its low-level utilities (reading
the PDF by coordinates) are reused here by import. Walking each week is
done separately because some roles have their own text label instead of
a main-room/overflow-room column (verified against a real VMC):

    'Oración inicio Jaime Leyes'                (the "de" is sometimes
                                                  missing in the printed
                                                  label — both are matched)
    'Presidente Ángel Pardo'                    (excluded)
    'Conductor Gustavo Murria Lector Iván Muñoz'
    'Oración final Pedro Frutos'

For the regular items (Treasures, Apply Yourself to the Field Ministry,
Living as Christians talks) the column scheme from parse_workbook.py is still
respected: if the congregation has an overflow room active, the same item
can have two different people at once (one per room, each with their own
helper), and both must get the reminder.

Note on language: same as parse_workbook.py — the VMC PDF content itself is
normally in Spanish, only the code is in English; since 24/08 an
English-language VMC is also recognized (see `_REMINDER_LANG_PACKS`
below), best-effort and built from jw.org's published item names rather
than a real filled-in English VMC (none was available to verify
against). The Spanish literals below are matched against real PDF text
and are deliberately not translated.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import fitz

from .i18n import t
from .parse_workbook import (
    RE_TITLE,
    _LANG_PACKS,
    _detect_language,
    _pdf_to_lines,
    _section_bands,
    _split_name_helper,
    _week_blocks,
    _column_text,
)

# Unnumbered items within the meeting body (e.g. "Necesidades de la
# congregación", sometimes called "Anuncios" or "Logros de la
# organización" depending on the week — some weeks it's numbered like any
# other item, some weeks it isn't, verified against a real VMC) also carry
# a speaker's name and DO need a reminder, unlike "Palabras de
# introducción/conclusión" (the Chairman, always unnumbered) and "Canción
# ..." lines with a time in front, which also lack a number but aren't a
# participant. This band-title structure ("HH:MM Title (min.)") itself is
# language-agnostic, so RE_TITLE_NO_NUMBER is shared by both languages.
RE_TITLE_NO_NUMBER = re.compile(r"^\d{1,2}:\d{2}\s*(.+?)\s*(?:\(\d+\s*min\.?\))?\s*$")

# Per-language patterns/labels for the reminder extraction. The Spanish
# ones are verified against real VMC PDFs; the English ones are
# best-effort (see module docstring) — in particular the exact wording of
# the standalone "Opening Prayer [Name]"/"Closing Prayer [Name]" lines
# and the printed-footer date format are guesses at the likely convention,
# not confirmed against a real English VMC.
_REMINDER_LANG_PACKS = {
    "es": {
        "opening_prayer_re": re.compile(r"^Oración (?:de )?inicio\s+(.+)$"),
        "closing_prayer_re": re.compile(r"^Oración final\s+(.+)$"),
        "conductor_reader_re": re.compile(r"^Conductor\s+(.+?)\s+Lector\s+(.+)$"),
        "no_reminder_prefixes": ("Canción", "Palabras de"),
        # The song between sections sometimes prints loose, with no time in
        # front (e.g. next to the "NUESTRA VIDA CRISTIANA" title, on the
        # right) — if not discarded, it doesn't anchor its own band and its
        # text spills into the neighboring numbered item, mixing in with
        # the name.
        "loose_song_re": re.compile(r"^Canción\s+\d+\b"),
        # Footer with the PDF's print date (e.g. "Impreso 03/08/2026"),
        # which spills into the last week's line block on each page — has
        # to be discarded when working out where that week's real content
        # actually ends, otherwise the cropped image ends with that line
        # stuck to the bottom.
        "printed_footer_re": re.compile(r"^Impreso\s+\d{2}/\d{2}/\d{4}$"),
        "opening_prayer_role": "Oración de inicio",
        "closing_prayer_role": "Oración final",
        "conductor_role": "Conductor del Estudio Bíblico de Congregación",
        "reader_role": "Lector del Estudio Bíblico de Congregación",
        "expected_roles": (
            "Lectura de la Biblia",
            "Conductor del Estudio Bíblico de Congregación",
            "Oración de inicio",
            "Oración final",
        ),
    },
    "en": {
        "opening_prayer_re": re.compile(r"^Opening Prayer:?\s+(.+)$"),
        "closing_prayer_re": re.compile(r"^(?:Closing|Concluding) Prayer:?\s+(.+)$"),
        "conductor_reader_re": re.compile(r"^Conductor\s+(.+?)\s+Reader\s+(.+)$"),
        "no_reminder_prefixes": ("Song", "Opening Comments", "Concluding Comments"),
        "loose_song_re": re.compile(r"^Song\s+\d+\b"),
        "printed_footer_re": re.compile(r"^Printed\s+\d{1,2}/\d{1,2}/\d{4}$"),
        "opening_prayer_role": "Opening Prayer",
        "closing_prayer_role": "Closing Prayer",
        "conductor_role": "Conductor of the Congregation Bible Study",
        "reader_role": "Reader of the Congregation Bible Study",
        "expected_roles": (
            "Bible Reading",
            "Conductor of the Congregation Bible Study",
            "Opening Prayer",
            "Closing Prayer",
        ),
    },
}

CROP_MARGIN_TOP_PT = 10.0     # air before the date header (same as bottom)
CROP_MARGIN_BOTTOM_PT = 10.0  # air after the last line of real content
APPROX_LINE_HEIGHT_PT = 14.0  # to fully include that last line (not cut it off at its y0)


@dataclass
class Participant:
    name: str
    date: date
    roles: list[str] = field(default_factory=list)
    phone: str | None = None


def _normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return " ".join(name.lower().split())


def _add(participants: dict[str, Participant], name: str, fecha: date, role: str) -> None:
    name = name.strip()
    if not name:
        return
    key = _normalize(name)
    if key in participants:
        participants[key].roles.append(role)
    else:
        participants[key] = Participant(name=name, date=fecha, roles=[role])


def _extract_week(fecha: date, lines: list[dict]) -> list[Participant]:
    lang = _detect_language(lines)
    pack = _REMINDER_LANG_PACKS[lang]
    ignored_lines = _LANG_PACKS[lang]["ignored_lines"]

    lines = [l for l in lines if not pack["loose_song_re"].match(l["texto"].strip())]
    participants: dict[str, Participant] = {}

    for l in lines:
        text = l["texto"].strip()
        m = pack["opening_prayer_re"].match(text)
        if m:
            _add(participants, m.group(1), fecha, pack["opening_prayer_role"])
            continue
        m = pack["closing_prayer_re"].match(text)
        if m:
            _add(participants, m.group(1), fecha, pack["closing_prayer_role"])
            continue

    # Any meeting item, numbered or not (not just Treasures/Apply
    # Yourself, unlike parse_workbook.py). The Chairman's bands ("Palabras de
    # introducción/conclusión") and the "Canción ..." ones also lack a
    # number, so they're explicitly discarded by their text — they never
    # enter the recipient list.
    for _index, y_start, y_end in _section_bands(lines, 0, len(lines)):
        title_text = _column_text(lines, y_start, y_end, "izquierda", ignored_lines)
        m = RE_TITLE.match(title_text)
        if m:
            part = m.group(2).strip()
        else:
            m_no_num = RE_TITLE_NO_NUMBER.match(title_text)
            if not m_no_num:
                continue
            part = m_no_num.group(1).strip()
            if part.startswith(pack["no_reminder_prefixes"]):
                continue

        # The two columns are looked at separately, not concatenated: when
        # the congregation has an overflow room active, an Apply Yourself
        # band can have TWO different people at once (one per room, each
        # with their own helper) — same as parse_workbook.py already handles
        # for the S-89 slips. The special case is "Conductor ... Lector
        # ...", whose real column sometimes falls below the x0=380 limit
        # that separates aux/main (verified against a real VMC: it was
        # lost in 6 of 7 weeks if only "principal" was checked) — it's
        # searched for in both columns before treating them as two
        # different-room students.
        main_text = _column_text(lines, y_start, y_end, "principal", ignored_lines)
        aux_text = _column_text(lines, y_start, y_end, "aux", ignored_lines)
        if not main_text and not aux_text:
            continue

        is_conductor_reader = False
        for text in (main_text, aux_text):
            m_cl = pack["conductor_reader_re"].match(text) if text else None
            if m_cl:
                _add(participants, m_cl.group(1), fecha, pack["conductor_role"])
                _add(participants, m_cl.group(2), fecha, pack["reader_role"])
                is_conductor_reader = True
                break
        if is_conductor_reader:
            continue

        # Unlike parse_workbook.py (which prints the helper's name on the
        # same S-89 slip as the main student), reminders only go to the
        # person actually in charge of the assignment — the helper for an
        # Apply Yourself item doesn't get their own reminder.
        for text in (main_text, aux_text):
            if not text:
                continue
            name, _helper = _split_name_helper(text)
            if name:
                _add(participants, name, fecha, part)

    return list(participants.values())


def parse_reminder_workbook(pdf_path: Path) -> dict[date, list[Participant]]:
    result: dict[date, list[Participant]] = {}
    for page_lines in _pdf_to_lines(pdf_path):
        for fecha, week_lines in _week_blocks(page_lines):
            participants = _extract_week(fecha, week_lines)
            if participants:
                result[fecha] = participants
    return result


def week_warnings(semanas: dict[date, list[Participant]], fecha: date) -> list[str]:
    """Checks whether a given week's extraction looks incomplete, by
    comparing it against the other weeks of the same VMC (not against a
    fixed number, so it doesn't depend on any one congregation's specific
    template) and against the roles any normal week should carry. Not a
    guaranteed failure — it's meant to warn, so the user can decide
    whether to check the VMC or continue anyway."""
    participants = semanas.get(fecha, [])
    warnings: list[str] = []
    if not participants:
        warnings.append(t("errores.semana_sin_participantes"))
        return warnings

    others = [len(v) for f, v in semanas.items() if f != fecha]
    if others:
        average = sum(others) / len(others)
        if len(participants) < average * 0.6:
            warnings.append(t("errores.semana_pocos_participantes", n=len(participants), media=f"{average:.0f}"))

    week_roles = [r for p in participants for r in p.roles]
    # Roles collected already carry the label of whichever language that
    # week was written in (see _extract_week) — "Congregation Bible
    # Study" only ever appears in the English pack's role labels, so its
    # presence is a reliable signal without needing to store the detected
    # language separately.
    lang = "en" if any("Congregation Bible Study" in r for r in week_roles) else "es"
    for expected in _REMINDER_LANG_PACKS[lang]["expected_roles"]:
        if not any(expected in r for r in week_roles):
            warnings.append(t("errores.rol_no_detectado", rol=expected))

    return warnings


def _page_crops(pdf_path: Path, doc: fitz.Document) -> dict[date, tuple[int, float, float]]:
    """Works out each week's rectangle from its own content (not from
    where the next week starts, nor the page height): the top limit is the
    date header, and the bottom is the lowest line of real content for
    that week (usually the closing prayer), discarding the "Impreso
    DD/MM/AAAA" footer if it spills into the block. This way the crop
    doesn't depend on how much blank space there is between weeks, and it
    doesn't drag the page footer into the last week on each sheet."""
    result: dict[date, tuple[int, float, float]] = {}
    for pnum, page_lines in enumerate(_pdf_to_lines(pdf_path)):
        page_height = doc[pnum].rect.height
        for fecha, block in _week_blocks(page_lines):
            y_start = max(0.0, block[0]["y0"] - CROP_MARGIN_TOP_PT)

            footer_re = _REMINDER_LANG_PACKS[_detect_language(block)]["printed_footer_re"]
            content_ys = [
                l["y0"] for l in block if not footer_re.match(l["texto"].strip())
            ]
            content_y_end = max(content_ys) if content_ys else block[0]["y0"]
            y_end = min(page_height, content_y_end + APPROX_LINE_HEIGHT_PT + CROP_MARGIN_BOTTOM_PT)

            result[fecha] = (pnum, y_start, y_end)
    return result


def crop_week_jpg(
    pdf_path: Path,
    fecha: date,
    destino: Path,
    dpi: int = 200,
    ajuste_arriba_pt: float = 0.0,
    ajuste_abajo_pt: float = 0.0,
) -> None:
    """Generates a cropped image with only the given week, to send the
    same program photo to everyone taking part that week (no manual
    cropping needed).

    ajuste_arriba_pt/ajuste_abajo_pt (in PDF points, +/-): let an
    automatic crop that overshoots or falls short be corrected by hand —
    positive expands the crop on that edge, negative shrinks it. Defaults
    to 0, same result as the automatic calculation alone."""
    doc = fitz.open(str(pdf_path))
    try:
        crops = _page_crops(pdf_path, doc)
        if fecha not in crops:
            raise ValueError(t("errores.semana_no_encontrada", fecha=fecha.isoformat()))
        page_num, y_start, y_end = crops[fecha]
        page = doc[page_num]
        y_start = max(0.0, y_start - ajuste_arriba_pt)
        y_end = min(page.rect.height, y_end + ajuste_abajo_pt)
        rect = fitz.Rect(0, y_start, page.rect.width, y_end)
        zoom = dpi / 72
        pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(zoom, zoom))
        destino.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(destino))
    finally:
        doc.close()
