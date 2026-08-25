"""Regression check for the VMC reminder parser
(assistant/reminder_workbook.py).

Not a pytest suite: the real VMC contains personal congregation data and
can't be committed to the repo for an automatic test anyone can
reproduce. It's a script run by hand against the actual VMC, applying the
same sanity checks the GUI already uses (week_warnings) plus a
check for already-known regressions: that no role contains section-header,
song, or Chairman text (the first real bug found and fixed while building
this parser, on 2026-08-15).

Usage:
    python -m assistant.verify_reminder_parser --vmc "ruta/al/VMC.pdf"

Run it again whenever reminder_workbook.py is touched, to confirm it still
extracts the same (or better) results as before the change.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .reminder_workbook import week_warnings, parse_reminder_workbook

# Text that should never appear inside a role — if it does, it's the same
# class of bug as "Canción 128 - Aguantemos hasta el fin Filip Martínez"
# (a header/song/chairman line that leaked into a real item's name or
# title).
SUSPICIOUS_TEXT = ("Canción", "Presidente", "Palabras de", "TESOROS", "SEAMOS", "NUESTRA VIDA")


def verify(pdf_path: Path) -> bool:
    print(f"Parseando {pdf_path.name}...")
    weeks = parse_reminder_workbook(pdf_path)
    if not weeks:
        print("FALLO: no se ha extraído ninguna semana del VMC.")
        return False

    all_ok = True
    for fecha in sorted(weeks):
        participants = weeks[fecha]
        print(f"\n{fecha}: {len(participants)} participantes")

        for p in participants:
            if not p.name.strip():
                print("  FALLO: participante con nombre vacío")
                all_ok = False
            for role in p.roles:
                if any(t in role for t in SUSPICIOUS_TEXT) or any(t in p.name for t in SUSPICIOUS_TEXT):
                    print(f"  FALLO: dato sospechoso (regresión conocida) -> {p.name!r} / {role!r}")
                    all_ok = False

        for warning in week_warnings(weeks, fecha):
            print(f"  AVISO: {warning}")

    print()
    if all_ok:
        print(f"OK: {len(weeks)} semanas verificadas sin fallos.")
    else:
        print("Hay fallos — revisa el parser antes de dar esto por bueno.")
    return all_ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vmc", required=True, type=Path, help="Ruta al PDF del VMC a verificar")
    args = ap.parse_args()

    if not args.vmc.exists():
        print(f"No existe el archivo: {args.vmc}")
        sys.exit(2)

    ok = verify(args.vmc)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
