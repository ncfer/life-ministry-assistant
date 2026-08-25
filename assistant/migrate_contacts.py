"""One-off migration: dumps the HERMANOS sheet from the xlsm into
contacts.csv.

Usage:
    python -m assistant.migrate_contacts "PLANTILLA ASIGNACIONES.xlsm" [destination.csv]

From then on, contacts.csv is the source of truth — it can be edited
directly (LibreOffice Calc, Excel, or a text editor) without touching the
xlsm again.
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

from . import i18n
from .config import load_config
from .contacts import save_contacts
from .i18n import t


def migrate(xlsm_path: Path, destination: Path) -> int:
    wb = openpyxl.load_workbook(str(xlsm_path), data_only=True, read_only=True)
    ws = wb["HERMANOS"]
    contacts = {}
    for name, phone in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        if name and phone:
            contacts[str(name).strip()] = str(int(phone))
    wb.close()

    save_contacts(destination, contacts)
    return len(contacts)


def main() -> None:
    i18n.set_language(load_config().language)
    if len(sys.argv) < 2:
        print(t("migrar.uso"))
        sys.exit(1)
    xlsm_path = Path(sys.argv[1])
    destination = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contacts.csv")

    total = migrate(xlsm_path, destination)
    print(t("migrar.completado", total=total, ruta=destination.resolve()))


if __name__ == "__main__":
    main()
