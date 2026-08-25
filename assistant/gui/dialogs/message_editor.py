from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit,
    QVBoxLayout,
)

from ... import i18n
from ...i18n import t
from ..widgets import MessageBubble, NavButton

# Evaluated at import time (same pattern as widgets.STEPS) — fine because
# the language is already set before this module is first imported.
HELP_TEXT = t("mensaje.ayuda")
REMINDER_HELP_TEXT = t("mensaje.ayuda_recordatorio")

# Every {placeholder} format_message()/format_reminder_message() accept
# (see whatsapp_send.py / send_reminders.py) — shown as clickable chips,
# and substituted with a made-up example so the preview bubble always
# has something concrete to show regardless of which ones the template
# actually uses.
ASSIGNMENT_PLACEHOLDERS = ["nombre", "nombre_pila", "ayudante", "fecha", "numero", "tipo", "link"]
REMINDER_PLACEHOLDERS = ["nombre", "nombre_pila", "rol", "fecha", "fecha_relativa"]

# format_message()/format_reminder_message() accept either name for each
# placeholder (see whatsapp_send.py) — the chips show whichever one
# matches the current UI language, instead of always the Spanish key
# regardless of what the help text above them is telling the user to type.
_EN_ALIAS = {
    "nombre": "name", "nombre_pila": "first_name", "ayudante": "helper",
    "fecha": "date", "numero": "number", "tipo": "type", "link": "link",
    "rol": "role", "fecha_relativa": "relative_date",
}


def _display_key(key: str) -> str:
    return _EN_ALIAS.get(key, key) if i18n.current_language() == "en" else key


_EXAMPLE_VALUES_ES = {
    "nombre": "Andrés Ferrer",
    "nombre_pila": "Andrés",
    "ayudante": "Diego Iranzo",
    "fecha": "6 de septiembre de 2026",
    "numero": "3",
    "tipo": "Lectura de la Biblia",
    "link": "https://calendar.google.com/calendar/event?...",
    "rol": "Lectura de la Biblia",
    "fecha_relativa": "mañana",
}
_EXAMPLE_VALUES_EN = {
    "nombre": "Andrew Ferrer",
    "nombre_pila": "Andrew",
    "ayudante": "Diego Iranzo",
    "fecha": "September 6, 2026",
    "numero": "3",
    "tipo": "Bible Reading",
    "link": "https://calendar.google.com/calendar/event?...",
    "rol": "Bible Reading",
    "fecha_relativa": "tomorrow",
}


def _example_values() -> dict[str, str]:
    """Demo content for the live preview, in whichever language the UI
    is currently in — not tied to `dates.py`'s long_date() (deliberately
    always Spanish for the real send, see its docstring), this is only
    the made-up preview text so an English-UI screenshot doesn't show a
    Spanish month name next to English sentences."""
    base = _EXAMPLE_VALUES_EN if i18n.current_language() == "en" else _EXAMPLE_VALUES_ES
    # Reachable under both the Spanish and English key, whichever one a
    # chip just inserted (see _display_key).
    return base | {en: base[es] for es, en in _EN_ALIAS.items()}


def _preview_text(template: str) -> str:
    """A plain string-replace substitution, deliberately NOT the same
    `template.format(**fields)` format_message()/format_reminder_message()
    use for the real send — that raises on a stray "{" or an unknown
    placeholder, which happens constantly while someone is still mid-edit
    typing a template. This just leaves anything it doesn't recognize
    untouched instead of crashing the live preview."""
    text = template
    for key, value in _example_values().items():
        text = text.replace("{" + key + "}", value)
    return text


class MessageEditorDialog(QDialog):
    def __init__(
        self, message_txt: str, parent=None, title: str | None = None,
        help_text: str = HELP_TEXT, default_template_key: str = "mensaje.plantilla_defecto",
        placeholders: list[str] | None = None,
    ):
        title = title or t("mensaje.titulo_ventana")
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(660, 420)
        self.path = Path(message_txt)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)
        help_label = QLabel(help_text)
        help_label.setProperty("help", True)
        layout.addWidget(help_label)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        for key in (placeholders or ASSIGNMENT_PLACEHOLDERS):
            label_key = _display_key(key)
            chip = QPushButton("{" + label_key + "}")
            chip.setProperty("chip", True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _, k=label_key: self._insert_placeholder(k))
            chips_row.addWidget(chip)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        content = QHBoxLayout()
        content.setSpacing(14)

        self.text_edit = QTextEdit()
        if self.path.exists():
            self.text_edit.setPlainText(self.path.read_text(encoding="utf-8"))
        else:
            # Brand-new install, nothing written yet: pre-fill a starter
            # template in the current UI language instead of leaving this
            # blank — makes the {placeholder} syntax obvious without
            # having to open the README. Never overwrites anything: this
            # only runs when self.path doesn't exist, and typing here
            # doesn't touch disk until "Save" is pressed.
            self.text_edit.setPlainText(t(default_template_key))
        self.text_edit.textChanged.connect(self._update_preview)
        content.addWidget(self.text_edit, 1)

        preview_col = QVBoxLayout()
        preview_col.setSpacing(6)
        preview_label = QLabel(t("mensaje.vista_previa"))
        preview_label.setProperty("subtitle", True)
        preview_col.addWidget(preview_label)
        self.preview = MessageBubble()
        preview_col.addWidget(self.preview)
        preview_col.addStretch()
        content.addLayout(preview_col)

        layout.addLayout(content)

        buttons = QHBoxLayout()
        cancel_button = NavButton(t("comun.cancelar"), icon_name="x")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        buttons.addStretch()
        save_button = NavButton(t("comun.guardar"), primary=True, icon_name="check")
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

        self._update_preview()

    def _insert_placeholder(self, key: str) -> None:
        self.text_edit.insertPlainText("{" + key + "}")
        self.text_edit.setFocus()

    def _update_preview(self) -> None:
        text = _preview_text(self.text_edit.toPlainText())
        self.preview.set_content("papeleta.jpg", text)

    def _save(self) -> None:
        content = self.text_edit.toPlainText()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write (temp file + replace), same reason as
        # save_contacts/persist_config: never leave the file half-written.
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(self.path)
        QMessageBox.information(self, t("comun.guardado_titulo"), t("mensaje.guardado_msg"))
        self.accept()
