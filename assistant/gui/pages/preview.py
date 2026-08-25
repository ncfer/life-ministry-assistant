from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from ...i18n import t
from ...models import ROOM_LABEL
from ..style import SUCCESS, TEXT_MUTED
from ..widgets import Card, IconLabel, NavButton, Pill, StepHeader
from ..workers import GenerateThread

# A grid (not a single horizontal strip) so several weeks' worth of
# slips are visible at once, wrapping to as many columns as the window's
# width allows instead of forcing a long sideways scroll — see the memory
# note on this screen's redesign for the two directions that were
# compared before picking this one.
_CARD_WIDTH = 148
_CARD_GAP = 14


class PreviewPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread: GenerateThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(10)

        layout.addWidget(StepHeader(t("preview.titulo"), 4))

        help_label = QLabel(t("preview.ayuda"))
        help_label.setProperty("help", True)
        layout.addWidget(help_label)

        self.progress_label = QLabel(t("preview.generando"))
        self.progress_label.setProperty("help", True)
        layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.done_label = IconLabel("check", SUCCESS)
        self.done_label.hide()
        layout.addWidget(self.done_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QGridLayout(self.content)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(_CARD_GAP)
        self.scroll.setWidget(self.content)
        self.scroll.hide()
        layout.addWidget(self.scroll)

        buttons = QHBoxLayout()
        back_button = NavButton(t("preview.atras_corregir"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(3))
        buttons.addWidget(back_button)
        buttons.addStretch()
        self.next_button = NavButton(t("preview.todo_correcto"), direction="next", primary=True)
        self.next_button.clicked.connect(lambda: self.main_window.go_to(5))
        self.next_button.setEnabled(False)
        buttons.addWidget(self.next_button)
        layout.addLayout(buttons)

    def enter(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.scroll.hide()
        self.done_label.hide()
        self.progress_label.show()
        self.progress_bar.show()
        self.progress_label.setText(t("preview.generando"))
        self.progress_bar.setRange(0, len(self.main_window.state.assignments))
        self.next_button.setEnabled(False)

        if not Path(self.main_window.config.paths.pdf_template).exists():
            QMessageBox.critical(
                self, t("preview.falta_s89_titulo"),
                t("preview.falta_s89_msg"),
            )
            self.main_window.go_to(0)
            return

        self._thread = GenerateThread(self.main_window.state.assignments, self.main_window.config)
        self._thread.progress.connect(self._on_progress)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, current: int, total: int, name: str) -> None:
        self.progress_bar.setValue(current)
        self.progress_label.setText(t("preview.generando_n", i=current, total=total, nombre=name))

    def _on_done(self, generated: list) -> None:
        self.main_window.state.generated = generated
        self.progress_bar.hide()
        self.progress_label.hide()
        self.done_label.setText(t("preview.n_papeletas_generadas", n=len(generated)))
        self.done_label.show()
        self.scroll.show()
        self.next_button.setEnabled(True)

        viewport_width = self.scroll.viewport().width() or 900
        columns = max(2, min(8, (viewport_width + _CARD_GAP) // (_CARD_WIDTH + _CARD_GAP)))
        for i, item in enumerate(generated):
            row, col = divmod(i, columns)
            self.content_layout.addWidget(self._card(item), row, col)

    def _card(self, item) -> Card:
        card = Card()
        card.setFixedWidth(_CARD_WIDTH)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(4)

        image = QLabel()
        pixmap = QPixmap(str(item.jpg)).scaledToWidth(
            _CARD_WIDTH - 24, Qt.TransformationMode.SmoothTransformation,
        )
        image.setPixmap(pixmap)
        v.addWidget(image)

        name = QLabel(f"<b>{item.assignment.name}</b>")
        name.setWordWrap(True)
        v.addWidget(name)

        room = IconLabel("house", TEXT_MUTED)
        room.setText(ROOM_LABEL[item.assignment.room])
        v.addWidget(room)

        if item.assignment.phone:
            phone = IconLabel("phone", TEXT_MUTED)
            phone.setText(item.assignment.phone)
            v.addWidget(phone)
        else:
            v.addWidget(Pill(t("review.pill_sin_telefono"), "warn", icon_name="triangle-alert"))

        return card

    def _on_error(self, message: str) -> None:
        self.progress_bar.hide()
        QMessageBox.critical(self, t("preview.error_titulo"), message)
