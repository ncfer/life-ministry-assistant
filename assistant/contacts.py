"""Contact list in a plain CSV (name,phone) — editable with any text
editor or with LibreOffice Calc/Excel — and fuzzy-match phone lookup for
each assignment by name, to tolerate variations like "Ester (de Piqueras)"
vs "Ester Piqueras".

Note on language: the column headers are English ("name"/"phone") going
forward — but `load_contacts()` also accepts a file still using the old
Spanish headers ("nombre"/"telefono", what every contacts.csv written
before 2026-08-24 has), the same legacy-key pattern as config.py. A file
read this way gets rewritten with the new English header the next time
it's saved from the app; nothing is migrated silently on disk on its
own.
"""
from __future__ import annotations

import csv
import os
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

MATCH_THRESHOLD = 0.85       # from here up, the phone is auto-filled
SUGGESTION_THRESHOLD = 0.65  # between this and MATCH_THRESHOLD, it's suggested but not auto-filled
HEADER = ["name", "phone"]
_LEGACY_HEADER = {"name": "nombre", "phone": "telefono"}


@dataclass
class Match:
    searched_name: str
    found_name: str | None   # only if confidence >= MATCH_THRESHOLD (auto-accepted)
    phone: str | None        # ditto
    confidence: float
    suggested_name: str | None = None    # closest candidate, even below MATCH_THRESHOLD
    suggested_phone: str | None = None


def _clean(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-zA-Z\s]", " ", name)
    return " ".join(name.lower().split())


def _variants(name: str) -> list[str]:
    """A name like "Carolina (de Medina)" may appear in HERMANOS with or
    without the married surname in parentheses, so both forms are tried:
    flattened ("Carolina de Medina") and without the parentheses
    ("Carolina")."""
    flattened = _clean(re.sub(r"[()]", "", name))
    no_parens = _clean(re.sub(r"\(.*?\)", "", name))
    return list({flattened, no_parens})


def load_contacts(csv_path: Path) -> dict[str, str]:
    """Returns {name: phone}. If the file doesn't exist, starts empty."""
    if not Path(csv_path).exists():
        return {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        name_key = "name" if "name" in fieldnames else _LEGACY_HEADER["name"]
        phone_key = "phone" if "phone" in fieldnames else _LEGACY_HEADER["phone"]
        return {
            row[name_key].strip(): row[phone_key].strip()
            for row in reader
            if row.get(name_key) and row.get(phone_key)
        }


def save_contacts(csv_path: Path, contacts: dict[str, str]) -> None:
    """Atomic write: writes to a temp file in the same folder first, and
    only at the end replaces the real one (`os.replace`, atomic on
    Windows/Mac/Linux). Without this, a close mid-write (crash, power
    loss, or simply the user force-closing a hung app) would leave
    `contacts.csv` truncated or empty — the most expensive data to lose,
    since it's the whole congregation's phone list, not something that
    can be regenerated automatically."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for name, phone in sorted(contacts.items()):
            writer.writerow([name, phone])
    os.replace(tmp_path, csv_path)


def find_phone(name: str, contacts: dict[str, str]) -> Match:
    targets = _variants(name)

    # 1) exact normalized match (any of the variants)
    for real_name, phone in contacts.items():
        if _clean(real_name) in targets:
            return Match(name, real_name, phone, 1.0)

    # 2) best fuzzy match, trying all variants
    best_name, best_phone, best_ratio = None, None, 0.0
    for real_name, phone in contacts.items():
        candidate = _clean(real_name)
        ratio = max(SequenceMatcher(None, t, candidate).ratio() for t in targets)
        if ratio > best_ratio:
            best_name, best_phone, best_ratio = real_name, phone, ratio

    if best_ratio >= MATCH_THRESHOLD:
        return Match(name, best_name, best_phone, best_ratio,
                     suggested_name=best_name, suggested_phone=best_phone)

    if best_ratio >= SUGGESTION_THRESHOLD:
        return Match(name, None, None, best_ratio,
                     suggested_name=best_name, suggested_phone=best_phone)

    return Match(name, None, None, best_ratio)
