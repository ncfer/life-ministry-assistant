"""Extracts from the VMC (the Life and Ministry Meeting Workbook PDF) the
assignments that carry an S-89-S slip: item 3 "Lectura de la Biblia" and
every item in the "SEAMOS MEJORES MAESTROS" section of each week
(normally 3, but some weeks have a 4th item — e.g. "Haga discípulos" —
before reaching "NUESTRA VIDA CRISTIANA").

When the congregation uses an overflow room, the VMC adds a second column
of names ("Sala auxiliar" next to "Auditorio principal") for those same
items, and each item's title wraps onto two lines to make room for it.
That's why PyMuPDF is used (not `pdftotext -layout`) to read each word's
real position: a text fragment's column is decided by where its OWN line
starts, not by a fixed character position — this avoids mixing one room's
name with the other's, or with the title.

Note on language: the VMC PDF itself is normally in Spanish (that's the
language most JW congregations using this app receive it in), but since
24/08 an English-language VMC is also recognized (see `_LANG_PACKS`
below) — a congregation that gets its workbook in English can use the
app the same way. The Spanish string literals matched against real PDF
text are deliberately not translated; the English ones were built from
the section/item titles published on jw.org (a real English VMC PDF
already filled in with assignment names was not available to verify
against, so this path is best-effort and may need small adjustments once
tested against one).
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import fitz

from .i18n import t
from .models import Assignment

# Horizontal margins (in PDF points) separating the row's three columns.
# Decided by where the WHOLE line starts (not each loose word), so a long
# title that spills to the right on its own line never gets confused with
# a name in the neighboring column.
LEFT_MARGIN_X = 60   # time ("20:16") and wrapped title continuations
AUX_LIMIT_X = 380     # below: "Sala auxiliar"/"Overflow Room"; above: "Auditorio principal"/"Main Hall"

RE_DATE = re.compile(r"^(\d{2}/\d{2}/\d{4})")
RE_TIME = re.compile(r"^\d{1,2}:\d{2}$")
RE_TITLE = re.compile(r"^\d{1,2}:\d{2}\s*(\d{1,2})\.\s*(.+?)\s*(?:\(\d+\s*min\.?\))?\s*$")
# When an item is only done in one of the two rooms, the VMC states it in
# the title itself, e.g. "¿Qué diría? (Sala Principal)" / "What Would You
# Say? (Overflow Room)" — that nuance is already captured in
# Assignment.room, so it's trimmed out here to avoid duplicating it
# inside `part`.
RE_ROOM_IN_TITLE = re.compile(r"\s*\((?:Sala[^)]*|Overflow[^)]*|Main Hall)\)\s*$", re.IGNORECASE)

# Per-language section keywords/labels, matched against real PDF text.
# `treasures`/`apply`/`living` are the (partial, order-independent) words
# `_title_index` looks for in each of the three section headers;
# `bible_reading` is the item-3 label under `treasures`.
_LANG_PACKS = {
    "es": {
        "treasures": ("TESOROS", "DE LA BIBLIA"),
        "apply": ("SEAMOS", "MEJORES MAESTROS"),
        "living": ("NUESTRA", "VIDA CRISTIANA"),
        "bible_reading": "Lectura de la Biblia",
        "ignored_lines": {
            "TESOROS DE LA BIBLIA", "SEAMOS MEJORES MAESTROS", "NUESTRA VIDA CRISTIANA",
            "Sala auxiliar", "Auditorio principal",
        },
    },
    "en": {
        "treasures": ("TREASURES", "GOD'S WORD"),
        "apply": ("APPLY YOURSELF", "FIELD MINISTRY"),
        "living": ("LIVING AS", "CHRISTIANS"),
        "bible_reading": "Bible Reading",
        "ignored_lines": {
            "TREASURES FROM GOD'S WORD", "APPLY YOURSELF TO THE FIELD MINISTRY", "LIVING AS CHRISTIANS",
            "Overflow Room", "Main Hall",
        },
    },
}


def _detect_language(lines: list[dict]) -> str:
    """Looks at a week's own lines (not the whole PDF) so a document could
    in theory mix languages across pages without breaking — in practice a
    congregation's VMC is always one language throughout, but detecting
    per-week costs nothing and removes that assumption."""
    blob = " ".join(l["texto"] for l in lines)
    for lang, pack in _LANG_PACKS.items():
        if lang == "es":
            continue
        if all(k in blob for k in pack["treasures"]):
            return lang
    return "es"


def _strip_parens(name: str) -> str:
    """"Lara (de Clares)" -> "Lara de Clares" (only the parentheses are
    removed, not their content, which is usually a married surname)."""
    return re.sub(r"[()]", "", name).strip()


def _split_name_helper(text: str) -> tuple[str, str]:
    text = text.strip()
    if " & " in text:
        name, helper = text.split(" & ", 1)
        return _strip_parens(name), _strip_parens(helper)
    return _strip_parens(text), ""


def _pdf_to_lines(pdf_path: Path) -> list[list[dict]]:
    """One list per page; each line groups the words PyMuPDF already
    detects on the same visual row, with their x0/y0 and original index."""
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        raise RuntimeError(t("errores.pdf_no_abre", ruta=pdf_path)) from e

    pages = []
    for page in doc:
        groups: dict[tuple[int, int], list[tuple[float, float, str]]] = defaultdict(list)
        for x0, y0, _x1, _y1, text, block, line, _num in page.get_text("words"):
            groups[(block, line)].append((x0, y0, text))

        lines = []
        for words in groups.values():
            words.sort(key=lambda w: w[0])
            lines.append({
                "x0": words[0][0],
                "y0": min(w[1] for w in words),
                "texto": " ".join(w[2] for w in words),
            })
        lines.sort(key=lambda l: (l["y0"], l["x0"]))
        pages.append(lines)
    doc.close()
    return pages


def _column_type(x0: float) -> str:
    if x0 < LEFT_MARGIN_X:
        return "izquierda"
    if x0 < AUX_LIMIT_X:
        return "aux"
    return "principal"


def _title_index(lines: list[dict], *keywords: str) -> int | None:
    # Case-insensitive: the section headers ("TESOROS DE LA BIBLIA",
    # "NUESTRA VIDA CRISTIANA"...) are usually printed in small caps in
    # the VMC, but PyMuPDF extracts the underlying text run verbatim —
    # and a real VMC was found where some of those headers come through
    # as "Tesoros de la Biblia"/"Nuestra Vida Cristiana" (Title Case)
    # while others ("SEAMOS MEJORES MAESTROS") stay upper case in the
    # very same PDF. A case-sensitive match silently missed the
    # lower-cased ones, which broke the section boundary used to bound
    # "SEAMOS MEJORES MAESTROS" — with `i_nuestra` never found, that
    # loop ran all the way to the end of the week's lines instead of
    # stopping at "NUESTRA VIDA CRISTIANA", scooping up the Congregation
    # Bible Study line ("Conductor X Lector Y") as if it were one more
    # Apply Yourself assignment. The missing `i_tesoros` also meant
    # "Lectura de la Biblia" was never even looked for, silently
    # dropping the Bible Reading assignment every single week.
    for i, l in enumerate(lines):
        text_upper = l["texto"].upper()
        if all(k.upper() in text_upper for k in keywords):
            return i
    return None


def _column_text(lines: list[dict], y_start: float, y_end: float, column: str, ignored_lines: set[str] | None = None) -> str:
    ignored_lines = ignored_lines if ignored_lines is not None else _LANG_PACKS["es"]["ignored_lines"]
    ignored_upper = {s.upper() for s in ignored_lines}
    parts = [
        l for l in lines
        if y_start <= l["y0"] < y_end
        and l["texto"].strip().upper() not in ignored_upper
        and _column_type(l["x0"]) == column
    ]
    parts.sort(key=lambda l: (l["y0"], l["x0"]))
    return " ".join(p["texto"] for p in parts).strip()


def _section_bands(lines: list[dict], start: int, end: int) -> list[tuple[int, float, float]]:
    """For each numbered item (anchored by "HH:MM ...") within
    lines[start:end], works out the Y range it owns (up to the midpoint
    with its neighbors), so a name wrapped onto two lines or written just
    before its time doesn't spill into the previous or next item."""
    section = lines[start:end]
    anchors = [i for i, l in enumerate(section) if RE_TIME.match(l["texto"].split(" ", 1)[0])]
    if not anchors:
        return []

    y_section_start = lines[start]["y0"]
    y_section_end = lines[end]["y0"] if end < len(lines) else float("inf")
    ys = [section[i]["y0"] for i in anchors]

    bands = []
    for k, i in enumerate(anchors):
        y_start = y_section_start if k == 0 else (ys[k - 1] + ys[k]) / 2
        y_end = y_section_end if k == len(anchors) - 1 else (ys[k] + ys[k + 1]) / 2
        bands.append((start + i, y_start, y_end))
    return bands


def _assignments_in_band(
    section_lines: list[dict], y_start: float, y_end: float, fecha: date, ignored_lines: set[str] | None = None
) -> list[Assignment]:
    title_text = _column_text(section_lines, y_start, y_end, "izquierda", ignored_lines)
    m = RE_TITLE.match(title_text)
    if not m:
        return []
    number, part = m.group(1), m.group(2).strip()
    part = RE_ROOM_IN_TITLE.sub("", part).strip()

    assignments = []
    for column, room in (("principal", "principal"), ("aux", "aux1")):
        text = _column_text(section_lines, y_start, y_end, column, ignored_lines)
        if not text:
            continue
        name, helper = _split_name_helper(text)
        if not name:
            continue
        assignments.append(
            Assignment(name=name, helper=helper, date=fecha, number=number, part=part, room=room)
        )
    return assignments


def _extract_week(fecha: date, lines: list[dict]) -> list[Assignment]:
    assignments: list[Assignment] = []

    lang = _detect_language(lines)
    pack = _LANG_PACKS[lang]
    i_tesoros = _title_index(lines, *pack["treasures"])
    i_seamos = _title_index(lines, *pack["apply"])
    i_nuestra = _title_index(lines, *pack["living"])

    # 1) Bible reading (item 3 of "TESOROS DE LA BIBLIA" / "TREASURES FROM GOD'S WORD")
    if i_tesoros is not None and i_seamos is not None:
        for index, y_start, y_end in _section_bands(lines, i_tesoros, i_seamos):
            if pack["bible_reading"] not in lines[index]["texto"]:
                continue
            assignments.extend(_assignments_in_band(lines, y_start, y_end, fecha, pack["ignored_lines"]))
            break

    # 2) Every item in "SEAMOS MEJORES MAESTROS" / "APPLY YOURSELF TO THE FIELD MINISTRY"
    if i_seamos is not None:
        end = i_nuestra if i_nuestra is not None else len(lines)
        for _index, y_start, y_end in _section_bands(lines, i_seamos, end):
            assignments.extend(_assignments_in_band(lines, y_start, y_end, fecha, pack["ignored_lines"]))

    return assignments


def _week_blocks(lines: list[dict]) -> list[tuple[date, list[dict]]]:
    indices = [i for i, l in enumerate(lines) if RE_DATE.match(l["texto"])]
    blocks = []
    for n, i in enumerate(indices):
        m = RE_DATE.match(lines[i]["texto"])
        fecha = datetime.strptime(m.group(1), "%d/%m/%Y").date()
        end = indices[n + 1] if n + 1 < len(indices) else len(lines)
        blocks.append((fecha, lines[i:end]))
    return blocks


def parse_workbook(pdf_path: Path) -> dict[date, list[Assignment]]:
    result: dict[date, list[Assignment]] = {}
    for page_lines in _pdf_to_lines(pdf_path):
        for fecha, week_lines in _week_blocks(page_lines):
            assignments = _extract_week(fecha, week_lines)
            if assignments:
                result[fecha] = assignments
    return result
