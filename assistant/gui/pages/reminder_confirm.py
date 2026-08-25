from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QMessageBox, QProgressBar,
    QVBoxLayout, QWidget,
)

from ...send_reminders import format_reminder_message
from ...i18n import t
from ...whatsapp_send import load_message_template
from ..dialogs.test_send_reminder import TestSendReminderDialog
from ..style import SUCCESS
from ..widgets import Card, IconLabel, MessageBubble, NavButton, REMINDER_STEPS, StepHeader
from ..workers import GenerateCropThread

ADJUST_STEP_PT = 15.0


class ReminderConfirmPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread: GenerateCropThread | None = None
        self._adjust_buttons: list[NavButton] = []
        # Incremental id of the last crop request launched — if "Show
        # more"/"Crop more" gets clicked several times in a row before the
        # previous thread finishes, this counter lets a now-stale request's
        # result be ignored instead of the displayed image ending up being
        # whichever earlier click arrived last.
        self._current_request = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(10)

        layout.addWidget(StepHeader(t("rec_confirmar.titulo"), 4, steps=REMINDER_STEPS))

        self.summary = IconLabel("check", SUCCESS)
        layout.addWidget(self.summary)

        self.progress_label = QLabel(t("rec_confirmar.generando_imagen"))
        self.progress_label.setProperty("help", True)
        layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        content = QHBoxLayout()
        content.setSpacing(14)

        left_card = Card()
        left = QVBoxLayout(left_card)
        left.setContentsMargins(14, 14, 14, 14)
        self.image = QLabel()
        self.image.setFixedWidth(240)
        left.addWidget(self.image)

        adjust_help = QLabel(t("rec_confirmar.se_ve_mal"))
        adjust_help.setProperty("help", True)
        left.addWidget(adjust_help)

        left.addLayout(self._adjust_row(t("rec_confirmar.borde_superior"), "top"))
        left.addLayout(self._adjust_row(t("rec_confirmar.borde_inferior"), "bottom"))

        self.reset_button = NavButton(t("rec_confirmar.restablecer"), icon_name="rotate-ccw")
        self.reset_button.clicked.connect(self._reset_adjust)
        self.reset_button.hide()
        self._adjust_buttons.append(self.reset_button)
        left.addWidget(self.reset_button)
        left.addStretch()
        content.addWidget(left_card)

        right_card = Card()
        right = QVBoxLayout(right_card)
        right.setContentsMargins(14, 14, 14, 14)
        right.addWidget(QLabel(t("rec_confirmar.asi_quedara_para")))
        self.participant_selector = QComboBox()
        self.participant_selector.currentIndexChanged.connect(self._update_preview)
        right.addWidget(self.participant_selector)
        self.preview = MessageBubble()
        right.addWidget(self.preview)
        right.addStretch()
        content.addWidget(right_card, 1)
        layout.addLayout(content)

        self.check_reviewed = QCheckBox(t("rec_confirmar.revisado"))
        self.check_reviewed.stateChanged.connect(self._update_buttons)
        layout.addWidget(self.check_reviewed)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(9))
        buttons.addWidget(back_button)
        self.test_button = NavButton(t("comun.probar_conmigo"), icon_name="wand-sparkles")
        self.test_button.clicked.connect(self._try_it)
        self.test_button.setEnabled(False)
        buttons.addWidget(self.test_button)
        buttons.addStretch()
        self.send_button = NavButton(t("rec_confirmar.enviar"), primary=True, icon_name="send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._send)
        buttons.addWidget(self.send_button)
        layout.addLayout(buttons)

    def _adjust_row(self, label: str, edge: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        more_button = NavButton(t("rec_confirmar.mostrar_mas"), icon_name="chevron-up")
        more_button.setToolTip(t("rec_confirmar.mostrar_mas_tooltip"))
        more_button.clicked.connect(lambda: self._adjust(edge, ADJUST_STEP_PT))
        row.addWidget(more_button)
        less_button = NavButton(t("rec_confirmar.recortar_mas"), icon_name="chevron-down")
        less_button.setToolTip(t("rec_confirmar.recortar_mas_tooltip"))
        less_button.clicked.connect(lambda: self._adjust(edge, -ADJUST_STEP_PT))
        row.addWidget(less_button)
        self._adjust_buttons.extend([more_button, less_button])
        return row

    def enter(self) -> None:
        state = self.main_window.reminder_state
        total = len(state.participants)
        self.summary.setText(t("rec_confirmar.se_van_a_enviar", n=total))
        self.check_reviewed.setChecked(False)

        self.participant_selector.blockSignals(True)
        self.participant_selector.clear()
        for p in state.participants:
            self.participant_selector.addItem(f"{p.name} — {' y '.join(p.roles)}")
        self.participant_selector.blockSignals(False)

        self._generate_crop()

    def _generate_crop(self) -> None:
        state = self.main_window.reminder_state
        self._current_request += 1
        request = self._current_request

        self.image.clear()
        self.preview.set_content("", "")
        self.progress_bar.show()
        self.progress_label.setText(t("rec_confirmar.generando_imagen"))
        self.test_button.setEnabled(False)
        self.send_button.setEnabled(False)
        for button in self._adjust_buttons:
            button.setEnabled(False)

        output_folder = Path(self.main_window.config.paths.output_folder)
        # `workbook_paths_by_date` knows which PDF this particular week comes
        # from (there can be several if it was searched via the Padlet, see
        # DownloadReminderWorkbookPadletThread); `workbook_path` is the usual
        # fallback for the single-file case.
        workbook_path = state.workbook_paths_by_date.get(state.selected_date, state.workbook_path)
        self._thread = GenerateCropThread(
            workbook_path, state.selected_date, output_folder,
            ajuste_arriba_pt=state.top_adjust_pt, ajuste_abajo_pt=state.bottom_adjust_pt,
        )
        self._thread.done.connect(lambda jpg: self._on_done(jpg, request))
        self._thread.error.connect(lambda message: self._on_error(message, request))
        self._thread.start()

    def _adjust(self, edge: str, delta: float) -> None:
        state = self.main_window.reminder_state
        if edge == "top":
            state.top_adjust_pt = max(0.0, state.top_adjust_pt + delta)
        else:
            state.bottom_adjust_pt = max(0.0, state.bottom_adjust_pt + delta)
        self._generate_crop()

    def _reset_adjust(self) -> None:
        state = self.main_window.reminder_state
        state.top_adjust_pt = 0.0
        state.bottom_adjust_pt = 0.0
        self._generate_crop()

    def _on_done(self, jpg: Path, request: int) -> None:
        if request != self._current_request:
            return  # a more recent adjustment click arrived while this one was being generated

        state = self.main_window.reminder_state
        state.week_jpg = jpg
        self.progress_bar.hide()
        self.progress_label.setText("")
        for button in self._adjust_buttons:
            button.setEnabled(True)
        self.reset_button.setVisible(bool(state.top_adjust_pt or state.bottom_adjust_pt))

        pixmap = QPixmap(str(jpg)).scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
        self.image.setPixmap(pixmap)

        self._update_preview()
        self._update_buttons()

    def _update_preview(self) -> None:
        state = self.main_window.reminder_state
        index = self.participant_selector.currentIndex()
        if not state.participants or index < 0 or index >= len(state.participants):
            return
        jpg = state.week_jpg
        try:
            template = load_message_template(Path(self.main_window.config.paths.reminder_message_txt))
            text = format_reminder_message(state.participants[index], template)
        except Exception as e:
            text = t("send_confirm.error_vista_previa", error=e)
        self.preview.set_content(Path(jpg).name if jpg else "", text)

    def _update_buttons(self) -> None:
        ready = self.main_window.reminder_state.week_jpg is not None
        self.test_button.setEnabled(ready)
        self.send_button.setEnabled(ready and self.check_reviewed.isChecked())

    def _on_error(self, message: str, request: int) -> None:
        if request != self._current_request:
            return
        self.progress_bar.hide()
        for button in self._adjust_buttons:
            button.setEnabled(True)
        QMessageBox.critical(self, t("rec_confirmar.error_imagen_titulo"), message)

    def _try_it(self) -> None:
        state = self.main_window.reminder_state
        index = self.participant_selector.currentIndex()
        if not state.participants or not state.week_jpg or index < 0:
            return
        dialog = TestSendReminderDialog(self.main_window, state.participants[index], state.week_jpg, self)
        dialog.exec()

    def _send(self) -> None:
        self.main_window.go_to(11)  # -> sending
