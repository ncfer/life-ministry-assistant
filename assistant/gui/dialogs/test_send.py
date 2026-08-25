from __future__ import annotations

from dataclasses import replace

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar,
    QVBoxLayout,
)

from ...config import persist_config
from ...i18n import t
from ..style import SUCCESS, WARNING_TEXT
from ..widgets import IconLabel, NavButton
from ..workers import SendThread


class TestSendDialog(QDialog):
    """Sends a single slip (the first one generated) to a test number,
    to check the message/image/reminder look right before sending to
    everyone."""

    def __init__(self, main_window, item, modo_recordatorio: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("comun.probar_conmigo"))
        self.resize(420, 200)
        self.main_window = main_window
        self.item = item
        self.modo_recordatorio = modo_recordatorio
        self._thread: SendThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        help_label = QLabel(t("test_send.ayuda_asignacion", nombre=item.assignment.name))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        row = QHBoxLayout()
        row.addWidget(QLabel(t("comun.tu_telefono")))
        self.phone_field = QLineEdit(main_window.config.test_number)
        self.phone_field.setPlaceholderText(t("comun.ejemplo_telefono"))
        row.addWidget(self.phone_field)
        layout.addLayout(row)

        self.status = QLabel("")
        self.status.setProperty("help", True)
        layout.addWidget(self.status)

        self.result_ok = IconLabel("check", SUCCESS)
        self.result_ok.hide()
        layout.addWidget(self.result_ok)
        self.result_fail = IconLabel("x", WARNING_TEXT)
        self.result_fail.hide()
        layout.addWidget(self.result_fail)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        buttons = QHBoxLayout()
        self.close_button = NavButton(t("comun.cerrar"), icon_name="x")
        self.close_button.clicked.connect(self.reject)
        buttons.addWidget(self.close_button)
        buttons.addStretch()
        self.send_button = NavButton(t("comun.enviar_prueba"), primary=True, icon_name="send")
        self.send_button.clicked.connect(self._send)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)

    def _send(self) -> None:
        phone = self.phone_field.text().strip()
        if not phone.isdigit():
            QMessageBox.warning(
                self, t("comun.telefono_no_valido_titulo"),
                t("comun.telefono_no_valido_msg"),
            )
            return

        self.main_window.config.test_number = phone
        persist_config(self.main_window.config)

        self.send_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.result_ok.hide()
        self.result_fail.hide()
        self.status.show()
        self.progress_bar.show()
        self.status.setText(t("comun.abriendo_whatsapp"))

        test_assignment = replace(self.item.assignment, phone=phone)
        items = [(test_assignment, self.item.jpg, self.item.ics)]

        from pathlib import Path
        self._thread = SendThread(
            items, self.modo_recordatorio,
            Path(self.main_window.config.paths.message_txt), self.main_window.config,
        )
        self._thread.waiting_qr.connect(
            lambda: self.status.setText(t("comun.escanea_qr"))
        )
        self._thread.result.connect(self._on_result)
        self._thread.completed.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_result(self, assignment, jpg, ics, success: bool, reason: str) -> None:
        self._success = success
        self._reason = reason

    def _on_finished(self) -> None:
        self.progress_bar.hide()
        self.close_button.setEnabled(True)
        self.send_button.setEnabled(True)
        self.status.hide()
        if getattr(self, "_success", False):
            self.result_ok.setText(t("comun.prueba_enviada"))
            self.result_ok.show()
        else:
            self.result_fail.setText(
                t("comun.prueba_fallo", motivo=getattr(self, "_reason", t("comun.error_desconocido")))
            )
            self.result_fail.show()

    def _on_error(self, message: str) -> None:
        self.progress_bar.hide()
        self.close_button.setEnabled(True)
        self.send_button.setEnabled(True)
        QMessageBox.critical(self, t("comun.error_enviar_prueba_titulo"), message)
