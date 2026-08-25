"""Configuration persisted in config.json: file paths and WhatsApp wait
times. All editable from the GUI (dialogs/general_settings.py and
dialogs/timing_settings.py) without touching code.

Note on migration: config.json files from before this field-name
translation (24/08) still have their nested dicts keyed with the OLD
Spanish field names (`plantilla_pdf`, `espera_abrir_chat_s`, `tema`,
`idioma`, etc.). `load_config()` reads either the new English key or,
if absent, falls back to the matching old Spanish key — so an existing
production config.json keeps loading correctly with zero data loss.
`persist_config()` always writes the new English keys, so a config.json
migrates to the new format the first time it's saved from the app.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Everything lives next to the app itself (relative paths) — config,
# contacts, messages, history, generated output. No separate "Documents"
# folder: since every one of these files is already editable from the
# GUI (general settings, contacts editor, message editor), there's no
# real need for them to live somewhere else meant for hand-editing.
CONFIG_PATH = Path("config.json")


@dataclass
class TimingConfig:
    open_chat_wait_s: int = 3
    after_attach_wait_s: int = 2
    after_upload_wait_s: int = 4
    after_send_wait_s: int = 2
    between_contacts_pause_s: int = 10


# Old Spanish key -> new English field, for reading a pre-migration config.json.
_TIMING_LEGACY_KEYS = {
    "espera_abrir_chat_s": "open_chat_wait_s",
    "espera_tras_adjuntar_s": "after_attach_wait_s",
    "espera_tras_cargar_archivo_s": "after_upload_wait_s",
    "espera_tras_enviar_s": "after_send_wait_s",
    "pausa_entre_contactos_s": "between_contacts_pause_s",
}


@dataclass
class PadletConfig:
    url: str = ""
    password: str = ""
    workbook_title: str = "VIDA Y MINISTERIO"


# Both old keys map to the same new one: "titulo_vmc" is the original
# (pre-24/08) key still in most real config.json files; "vmc_title" was
# this same field's name for a few hours this same day, before "VMC" was
# also translated to "workbook" in the code.
_PADLET_LEGACY_KEYS = {"titulo_vmc": "workbook_title", "vmc_title": "workbook_title"}


@dataclass
class PathsConfig:
    # The defaults are only used for a NEW install (no config.json
    # anywhere yet) — an existing install that already had these fields
    # saved in its config.json keeps using those values as-is when
    # loading, this doesn't affect them.
    pdf_template: str = ""
    output_folder: str = "output"
    contacts_csv: str = "contacts.csv"
    message_txt: str = "message.txt"
    history_csv: str = "history.csv"
    reminder_message_txt: str = "reminder_message.txt"
    reminder_history_csv: str = "reminder_history.csv"


_PATHS_LEGACY_KEYS = {
    "plantilla_pdf": "pdf_template",
    "carpeta_salida": "output_folder",
    "contactos_csv": "contacts_csv",
    "mensaje_txt": "message_txt",
    "historial_csv": "history_csv",
    "mensaje_recordatorio_txt": "reminder_message_txt",
    "historial_recordatorios_csv": "reminder_history_csv",
}


def _migrate(data: dict, legacy_keys: dict[str, str]) -> dict:
    """Returns a copy of `data` with any old (Spanish) key translated to
    its new (English) key, without overwriting a new key that's already
    present (in case an already-migrated and a not-yet-migrated
    config.json ever got mixed together, the new one always wins)."""
    migrated = dict(data)
    for old_key, new_key in legacy_keys.items():
        if old_key in migrated and new_key not in migrated:
            migrated[new_key] = migrated.pop(old_key)
        else:
            migrated.pop(old_key, None)
    return migrated


@dataclass
class Config:
    paths: PathsConfig = field(default_factory=PathsConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    padlet: PadletConfig = field(default_factory=PadletConfig)
    drive_link: str = ""  # Google Drive share link for the VMC PDF — see assistant/drive.py
    theme: str = "sistema"  # "claro" | "oscuro" | "sistema"
    language: str = "es"  # "es" | "en" — see assistant/i18n.py
    test_number: str = ""  # number for the "Try it with me" button


_CONFIG_LEGACY_KEYS = {
    "rutas": "paths",
    "tiempos": "timing",
    "tema": "theme",
    "idioma": "language",
    "numero_prueba": "test_number",
}


def load_config(path: Path = CONFIG_PATH) -> Config:
    if not path.exists():
        return Config()
    data = json.loads(path.read_text(encoding="utf-8"))
    data = _migrate(data, _CONFIG_LEGACY_KEYS)
    return Config(
        paths=PathsConfig(**_migrate(data.get("paths", {}), _PATHS_LEGACY_KEYS)),
        timing=TimingConfig(**_migrate(data.get("timing", {}), _TIMING_LEGACY_KEYS)),
        padlet=PadletConfig(**_migrate(data.get("padlet", {}), _PADLET_LEGACY_KEYS)),
        drive_link=data.get("drive_link", ""),
        theme=data.get("theme", "sistema"),
        language=data.get("language", "es"),
        test_number=data.get("test_number", ""),
    )


def persist_config(config: Config, path: Path = CONFIG_PATH) -> None:
    """Atomic write (temp file + `os.replace`) for the same reason as
    `save_contacts` in contacts.py: a close mid-write must never leave
    `config.json` corrupted — that would break the whole app the next
    time it opens, not just one stray setting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "paths": asdict(config.paths),
        "timing": asdict(config.timing),
        "padlet": asdict(config.padlet),
        "drive_link": config.drive_link,
        "theme": config.theme,
        "language": config.language,
        "test_number": config.test_number,
    }
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)
