"""Simple terminal menu to edit contacts.csv without touching code or
needing to open a spreadsheet.

Usage:
    python -m assistant.edit_contacts [contacts.csv]
"""
from __future__ import annotations

import sys
from pathlib import Path

from . import i18n
from .config import load_config
from .contacts import load_contacts, save_contacts
from .i18n import t


def _list(contacts: dict[str, str]) -> None:
    if not contacts:
        print(t("editar_contactos.sin_contactos"))
        return
    for name, phone in sorted(contacts.items()):
        print(f"  {name:<35} {phone}")


def _search(contacts: dict[str, str]) -> None:
    text = input(t("editar_contactos.buscar_prompt")).strip().lower()
    found = {name: phone for name, phone in contacts.items() if text in name.lower()}
    _list(found)


def _add(contacts: dict[str, str]) -> None:
    name = input(t("editar_contactos.nombre_prompt")).strip()
    if not name:
        print(t("editar_contactos.nombre_vacio"))
        return
    phone = input(t("editar_contactos.telefono_prompt")).strip()
    if not phone.isdigit():
        print(t("editar_contactos.telefono_invalido"))
        return
    if name in contacts:
        print(t("editar_contactos.actualizado", nombre=name, anterior=contacts[name], nuevo=phone))
    else:
        print(t("editar_contactos.anadido", nombre=name, telefono=phone))
    contacts[name] = phone


def _delete(contacts: dict[str, str]) -> None:
    name = input(t("editar_contactos.borrar_prompt")).strip()
    if name in contacts:
        del contacts[name]
        print(t("editar_contactos.borrado", nombre=name))
    else:
        print(t("editar_contactos.no_encontrado"))


def main() -> None:
    i18n.set_language(load_config().language)
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("contacts.csv")
    contacts = load_contacts(csv_path)
    print(t("editar_contactos.cargados", n=len(contacts), ruta=csv_path.resolve()))

    while True:
        print(t("editar_contactos.menu"))
        option = input(t("editar_contactos.elige_opcion")).strip()
        if option == "1":
            _list(contacts)
        elif option == "2":
            _search(contacts)
        elif option == "3":
            _add(contacts)
        elif option == "4":
            _delete(contacts)
        elif option == "5":
            save_contacts(csv_path, contacts)
            print(t("editar_contactos.guardado", ruta=csv_path.resolve()))
            break
        elif option == "0":
            print(t("editar_contactos.salido_sin_guardar"))
            break
        else:
            print(t("editar_contactos.opcion_invalida"))


if __name__ == "__main__":
    main()
