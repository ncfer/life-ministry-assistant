from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ...i18n import t
from ..widgets import Card, IconRow


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel(t("app.titulo"))
        title.setProperty("title", True)
        layout.addWidget(title)

        layout.addWidget(self._section(
            t("home.subtitulo_asignaciones"),
            [
                ("calendar_check", t("home.boton_nueva_asignacion"), self.main_window.new_assignment, True),
                ("history", t("home.boton_historial"), self.main_window.open_history, False),
                ("message", t("home.boton_mensaje"), self.main_window.open_message_editor, False),
            ],
        ))
        layout.addWidget(self._section(
            t("home.subtitulo_recordatorios"),
            [
                ("bell", t("home.boton_nuevo_recordatorio"), self.main_window.new_reminder, True),
                ("history", t("home.boton_historial_recordatorios"), self.main_window.open_reminder_history, False),
                ("message", t("home.boton_mensaje_recordatorio"), self.main_window.open_reminder_message_editor, False),
            ],
        ))
        layout.addWidget(self._section(
            t("home.subtitulo_comun"),
            [
                ("users", t("home.boton_contactos"), self.main_window.open_contacts_editor, False),
                ("sliders", t("home.boton_config_general"), self.main_window.open_general_settings, False),
                ("settings", t("home.boton_config_avanzada"), self.main_window.open_timing_settings, False),
            ],
        ))
        layout.addStretch()

    def _section(self, subtitle: str, rows: list[tuple[str, str, callable, bool]]) -> Card:
        card = Card()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 14, 16, 10)
        v.setSpacing(2)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setProperty("subtitle", True)
        subtitle_label.setContentsMargins(4, 0, 0, 6)
        v.addWidget(subtitle_label)

        for icon_name, text, callback, primary in rows:
            row = IconRow(icon_name, text, primary=primary)
            row.clicked.connect(callback)
            v.addWidget(row)

        return card

    def enter(self) -> None:
        pass
