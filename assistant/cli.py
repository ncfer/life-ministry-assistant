"""Orquestador: VMC -> asignaciones -> PDF/JPG/ICS -> (opcional) WhatsApp.

Uso:
    python -m assistant.cli --vmc "VMC 09-10 2026.pdf" \
        --plantilla "PLANTILLA ASIGNACIONES.pdf" \
        --contactos contacts.csv \
        --mes 2026-09

    # Añadir --enviar para, tras confirmar, mandarlo por WhatsApp Web
    # --recordatorio {ics,gcal,ambos} elige qué se manda como recordatorio
    #   de calendario; si se omite, se pregunta por terminal.
    #
    # Every flag has an English alias (--workbook, --template,
    # --contacts, --message, --month, --weeks, --send, --reminder) for
    # an English-speaking congregation — same behavior either way, pick
    # whichever language you prefer to type. The prompts/summary printed
    # while it runs follow config.json's language setting (see i18n.py).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from . import i18n
from .config import load_config
from .contacts import find_phone, load_contacts
from .dates import weekday_name
from .fill_pdf import fill_pdf
from .gen_ics import write_ics
from .i18n import t
from .models import Assignment
from .parse_workbook import parse_workbook
from .to_jpg import pdf_to_jpg


def _slug(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", text).strip()


def _filter_weeks(
    weeks: dict[date, list[Assignment]],
    dates: list[date] | None,
    month: str | None,
) -> dict[date, list[Assignment]]:
    if dates:
        return {f: a for f, a in weeks.items() if f in dates}
    if month:
        year, m = (int(x) for x in month.split("-"))
        return {f: a for f, a in weeks.items() if f.year == year and f.month == m}
    return weeks


def _resolve_phones(
    weeks: dict[date, list[Assignment]], contacts: dict[str, str]
) -> dict[date, list[Assignment]]:
    result = {}
    for fecha, assignments in weeks.items():
        updated = []
        for a in assignments:
            match = find_phone(a.name, contacts)
            updated.append(replace(a, phone=match.phone))
        result[fecha] = updated
    return result


def _generate_documents(
    weeks: dict[date, list[Assignment]], template: Path, output_dir: Path
) -> dict[date, list[tuple[Assignment, Path, Path, Path]]]:
    """Devuelve {fecha: [(asignacion, pdf, jpg, ics), ...]}."""
    result = {}
    for fecha, assignments in weeks.items():
        folder = output_dir / fecha.strftime("%Y-%m")
        items = []
        for a in assignments:
            base = folder / f"{fecha.isoformat()} - {a.number} - {_slug(a.name)}"
            pdf_path = base.with_suffix(".pdf")
            jpg_path = base.with_suffix(".jpg")
            ics_path = base.with_suffix(".ics")

            fill_pdf(template, a, pdf_path)
            pdf_to_jpg(pdf_path, jpg_path)
            write_ics(a, ics_path)

            items.append((a, pdf_path, jpg_path, ics_path))
        result[fecha] = items
    return result


def _print_summary(generated: dict[date, list[tuple[Assignment, Path, Path, Path]]]) -> int:
    total = 0
    no_phone = 0
    for fecha in sorted(generated):
        print(f"\n{weekday_name(fecha.weekday())} {fecha.day:02d}/{fecha.month:02d}/{fecha.year}")
        for a, _pdf, _jpg, _ics in generated[fecha]:
            total += 1
            if a.phone:
                status = a.phone
            else:
                status = t("cli.sin_telefono")
                no_phone += 1
            helper_text = f" + {a.helper}" if a.helper else ""
            print(f"  [{a.number}] {a.part:<25} {a.name}{helper_text:<25} -> {status}")
    print("\n" + t("cli.total_generado", total=total, sin_telefono=no_phone))
    return no_phone


def main() -> None:
    i18n.set_language(load_config().language)

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vmc", "--workbook", dest="vmc", required=True, type=Path)
    ap.add_argument("--plantilla", "--template", dest="plantilla", required=True, type=Path,
                     help=t("cli.ayuda_plantilla"))
    ap.add_argument("--contactos", "--contacts", dest="contactos", type=Path, default=Path("contacts.csv"),
                     help=t("cli.ayuda_contactos"))
    ap.add_argument("--mensaje", "--message", dest="mensaje", type=Path, default=Path("message.txt"),
                     help=t("cli.ayuda_mensaje"))
    ap.add_argument("--output", type=Path, default=Path("output"))
    ap.add_argument("--mes", "--month", dest="mes", help=t("cli.ayuda_mes"))
    ap.add_argument("--semanas", "--weeks", dest="semanas", help=t("cli.ayuda_semanas"))
    ap.add_argument("--enviar", "--send", dest="enviar", action="store_true",
                     help=t("cli.ayuda_enviar"))
    ap.add_argument("--recordatorio", "--reminder", dest="recordatorio",
                     choices=["ics", "gcal", "ambos", "both"],
                     help=t("cli.ayuda_recordatorio"))
    args = ap.parse_args()
    if args.recordatorio == "both":
        args.recordatorio = "ambos"

    dates = None
    if args.semanas:
        dates = [date.fromisoformat(s.strip()) for s in args.semanas.split(",")]

    print(t("cli.parseando", nombre=args.vmc.name))
    weeks = parse_workbook(args.vmc)
    weeks = _filter_weeks(weeks, dates, args.mes)
    if not weeks:
        print(t("cli.sin_semanas"))
        sys.exit(1)

    print(t("cli.cargando_contactos"))
    contacts = load_contacts(args.contactos)
    weeks = _resolve_phones(weeks, contacts)

    print(t("cli.generando"))
    generated = _generate_documents(weeks, args.plantilla, args.output)

    no_phone = _print_summary(generated)

    if not args.enviar:
        print("\n" + t("cli.documentos_en", ruta=args.output.resolve()))
        return

    if no_phone:
        print("\n" + t("cli.excluidos_sin_telefono", n=no_phone))

    reminder_mode = args.recordatorio or _ask_reminder_mode()

    answer = input("\n" + t("cli.confirmar_envio")).strip().lower()
    if answer != t("cli.confirmar_respuesta"):
        print(t("cli.cancelado"))
        return

    from .whatsapp_send import send_assignments

    sendable = [
        (a, jpg, ics)
        for items in generated.values()
        for a, _pdf, jpg, ics in items
        if a.phone
    ]
    send_assignments(sendable, modo_recordatorio=reminder_mode, plantilla_mensaje=args.mensaje)


def _ask_reminder_mode() -> str:
    print("\n" + t("cli.pregunta_recordatorio"))
    print("  " + t("cli.opcion_ics"))
    print("  " + t("cli.opcion_gcal"))
    print("  " + t("cli.opcion_ambos"))
    options = {"1": "ics", "2": "gcal", "3": "ambos"}
    while True:
        choice = input(t("cli.elige_opcion")).strip() or "3"
        if choice in options:
            return options[choice]
        print(t("cli.opcion_invalida"))


if __name__ == "__main__":
    main()
