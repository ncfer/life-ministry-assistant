from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ...i18n import t
from ...whatsapp_send import load_message_template, format_message
from ..dialogs.test_send import TestSendDialog
from ..style import SUCCESS
from ..widgets import IconLabel, MessageBubble, NavButton, OptionCard, StepHeader

# (value, icon, i18n key) — order matches the old radio order, "ambos" stays
# the default per the previous `row_both.radio.setChecked(True)`.
_CALENDAR_MODES = [
    ("ics", "paperclip", "send_confirm.opcion_ics"),
    ("gcal", "link", "send_confirm.opcion_gcal"),
    ("ambos", "calendar_check", "send_confirm.opcion_ambos"),
]


class SendConfirmPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(14)

        layout.addWidget(StepHeader(t("send_confirm.titulo"), 5))

        self.summary = IconLabel("check", SUCCESS)
        layout.addWidget(self.summary)

        columns = QHBoxLayout()
        columns.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_col.addWidget(QLabel(t("send_confirm.pregunta_recordatorio")))
        self._mode = "ambos"
        self._options: list[tuple[str, OptionCard]] = []
        for value, icon, text_key in _CALENDAR_MODES:
            opt = OptionCard(icon, t(text_key))
            opt.clicked.connect(lambda v=value: self._select_mode(v))
            opt.set_selected(value == self._mode)
            left_col.addWidget(opt)
            self._options.append((value, opt))
        left_col.addStretch()
        left_widget = QWidget()
        left_widget.setLayout(left_col)
        columns.addWidget(left_widget)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        preview_label = QLabel(t("send_confirm.vista_previa_ejemplo"))
        preview_label.setWordWrap(True)
        right_col.addWidget(preview_label)
        self.preview = MessageBubble()
        right_col.addWidget(self.preview)
        right_col.addStretch()
        right_widget = QWidget()
        right_widget.setLayout(right_col)
        right_widget.setMaximumWidth(440)
        columns.addWidget(right_widget, 1)

        layout.addLayout(columns, 1)

        self.check_reviewed = QCheckBox(t("send_confirm.revisado"))
        self.check_reviewed.stateChanged.connect(self._update_send_button)
        layout.addWidget(self.check_reviewed)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(4))
        buttons.addWidget(back_button)
        test_button = NavButton(t("comun.probar_conmigo"), icon_name="wand-sparkles")
        test_button.clicked.connect(self._try_it)
        buttons.addWidget(test_button)
        buttons.addStretch()
        self.send_button = NavButton(t("send_confirm.enviar"), primary=True, icon_name="send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._send)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)

    def enter(self) -> None:
        total = len(self.main_window.state.generated)
        self.summary.setText(t("send_confirm.se_van_a_enviar", n=total))
        self.check_reviewed.setChecked(False)
        self._update_preview()

    def _update_send_button(self) -> None:
        self.send_button.setEnabled(self.check_reviewed.isChecked())

    def _select_mode(self, value: str) -> None:
        self._mode = value
        for opt_value, opt in self._options:
            opt.set_selected(opt_value == value)
        self._update_preview()

    def _current_mode(self) -> str:
        return self._mode

    def _update_preview(self) -> None:
        if not self.main_window.state.generated:
            self.preview.set_content("", "")
            return
        item = self.main_window.state.generated[0]
        try:
            template = load_message_template(Path(self.main_window.config.paths.message_txt))
            text = format_message(item.assignment, template, self._current_mode())
        except Exception as e:
            text = t("send_confirm.error_vista_previa", error=e)
        self.preview.set_content(item.jpg.name, text)

    def _try_it(self) -> None:
        if not self.main_window.state.generated:
            return
        dialog = TestSendDialog(self.main_window, self.main_window.state.generated[0], self._current_mode(), self)
        dialog.exec()

    def _send(self) -> None:
        self.main_window.state.reminder_mode = self._current_mode()
        self.main_window.go_to(6)  # -> sending
