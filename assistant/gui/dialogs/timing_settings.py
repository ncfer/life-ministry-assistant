from __future__ import annotations

from dataclasses import replace

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout,
)

from ...config import Config
from ...i18n import t
from ..style import ICON_BADGE_BG, PRIMARY
from ..widgets import Card, IconBadge, NavButton

# Evaluated at import time (same pattern as widgets.STEPS).
# Note: the first element of each tuple is a real TimingConfig field name
# — kept in sync with config.py's field names (English since 24/08; the
# JSON key on disk is migrated transparently by load_config()). The icon
# is chosen to match what that wait is actually FOR in the real WhatsApp
# automation sequence (open the chat, attach the file, wait for the
# upload, send, pause before the next contact) rather than reusing one
# generic "clock" icon five times, which wouldn't tell the rows apart.
FIELDS = [
    ("open_chat_wait_s", "message", t("tiempos.espera_abrir_chat")),
    ("after_attach_wait_s", "paperclip", t("tiempos.espera_tras_adjuntar")),
    ("after_upload_wait_s", "file-up", t("tiempos.espera_tras_cargar")),
    ("after_send_wait_s", "check-check", t("tiempos.espera_tras_enviar")),
    ("between_contacts_pause_s", "users", t("tiempos.pausa_entre_contactos")),
]


class TimingSettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("tiempos.titulo_ventana"))
        self.resize(460, 380)
        self.config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)
        help_label = QLabel(t("tiempos.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(6, 6, 6, 6)
        card_layout.setSpacing(2)

        self.fields = {}
        for attr_name, icon_name, label in FIELDS:
            row = QHBoxLayout()
            row.setContentsMargins(10, 8, 10, 8)
            row.setSpacing(12)

            badge = IconBadge(icon_name, PRIMARY)
            badge.setFixedSize(32, 32)
            badge.setStyleSheet(f"background-color: {ICON_BADGE_BG}; border-radius: 9px;")
            row.addWidget(badge)

            row.addWidget(QLabel(label), 1)

            spin = QSpinBox()
            spin.setRange(0, 300)
            spin.setSuffix(" s")
            spin.setValue(getattr(config.timing, attr_name))
            spin.setFixedWidth(90)
            row.addWidget(spin)
            self.fields[attr_name] = spin

            card_layout.addLayout(row)
        layout.addWidget(card)

        layout.addStretch()

        buttons = QHBoxLayout()
        reset_button = NavButton(t("tiempos.restaurar_defecto"), icon_name="rotate-ccw")
        reset_button.clicked.connect(self._reset)
        buttons.addWidget(reset_button)
        buttons.addStretch()
        cancel_button = NavButton(t("comun.cancelar"), icon_name="x")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        save_button = NavButton(t("comun.guardar"), primary=True, icon_name="check")
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

    def _reset(self) -> None:
        from ...config import TimingConfig
        default = TimingConfig()
        for attr_name, spin in self.fields.items():
            spin.setValue(getattr(default, attr_name))

    def _save(self) -> None:
        new_values = {attr_name: spin.value() for attr_name, spin in self.fields.items()}
        self.config = replace(self.config, timing=replace(self.config.timing, **new_values))
        self.accept()
