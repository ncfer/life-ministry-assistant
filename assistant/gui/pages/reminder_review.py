from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QMessageBox,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from ...contacts import MATCH_THRESHOLD, load_contacts, save_contacts
from ...history import load_history
from ...i18n import t
from ..widgets import NavButton, Pill, REMINDER_STEPS, StepHeader, WarningBanner
from ..workers import ResolveParticipantPhonesThread

# Same layout decisions as review_assignments.py — see the memory note
# on that screen's redesign for why Estado sits right after Enviar and
# why the fix-it actions live in Teléfono instead of a separate column.
COL_ENVIAR, COL_ESTADO, COL_ROLES, COL_NOMBRE, COL_TEL = range(5)

_COLUMN_CLAMP = {
    COL_ESTADO: (75, 145),
    COL_NOMBRE: (85, 140),
    COL_TEL: (85, 400),
}


class ReminderReviewPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread = None
        self._duplicate_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(10)

        layout.addWidget(StepHeader(t("rec_revisar.titulo"), 3, steps=REMINDER_STEPS))

        self.warning_banner = WarningBanner()
        self.warning_banner.hide()
        layout.addWidget(self.warning_banner)

        help_label = QLabel(t("rec_revisar.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("review.col_enviar"), t("review.col_estado"), t("rec_revisar.col_participacion"),
            t("review.col_nombre"), t("review.col_telefono"),
        ])
        self.table.setColumnWidth(COL_ENVIAR, 56)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_ROLES, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_ENVIAR, QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.hide()
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(8))
        buttons.addWidget(back_button)
        buttons.addStretch()
        self.next_button = NavButton(t("rec_revisar.continuar"), direction="next", primary=True)
        self.next_button.clicked.connect(self._next)
        self.next_button.setEnabled(False)
        buttons.addWidget(self.next_button)
        layout.addLayout(buttons)

    def enter(self) -> None:
        self.table.hide()
        self.progress_bar.show()
        self.next_button.setEnabled(False)
        self.warning_banner.hide()

        contacts_csv = Path(self.main_window.config.paths.contacts_csv)
        self._thread = ResolveParticipantPhonesThread(
            self.main_window.reminder_state.participants, contacts_csv
        )
        self._thread.done.connect(self._fill_table)
        self._thread.start()

    def _already_sent(self) -> dict[tuple[str, str], str]:
        history_csv = Path(self.main_window.config.paths.reminder_history_csv)
        already_sent = {}
        for row in load_history(history_csv):
            if row["status"] == "enviado":
                key = (row["name"], row["assignment_date"])
                already_sent.setdefault(key, row["timestamp"].split("T")[0])
        return already_sent

    def _fill_table(self, result: list) -> None:
        self.progress_bar.hide()
        self.table.show()
        self.next_button.setEnabled(True)

        already_sent = self._already_sent()
        self.table.setRowCount(len(result))
        self._duplicate_count = sum(
            1 for p, _m in result if already_sent.get((p.name, p.date.isoformat()))
        )

        self._size_estado_and_tel_columns(result, already_sent)

        for row, (participant, match) in enumerate(result):
            sent_date = already_sent.get((participant.name, participant.date.isoformat()))

            check = QCheckBox()
            check.setChecked(not sent_date)
            container = QWidget()
            hl = QHBoxLayout(container)
            hl.addWidget(check)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, COL_ENVIAR, container)

            self._set_estado_pill(row, no_phone=not participant.phone, sent_date=sent_date)

            self.table.setItem(row, COL_ROLES, self._make_item(" y ".join(participant.roles), editable=False))
            self.table.setItem(row, COL_NOMBRE, self._make_item(participant.name))
            self._set_tel_cell(row, participant.phone, match)

        self.table.resizeColumnToContents(COL_NOMBRE)
        lo, hi = _COLUMN_CLAMP[COL_NOMBRE]
        self.table.setColumnWidth(COL_NOMBRE, max(lo, min(self.table.columnWidth(COL_NOMBRE), hi)))

        self._update_warning()

    def _size_estado_and_tel_columns(self, result: list, already_sent: dict) -> None:
        fm = QFontMetrics(self.table.font())

        estado_texts = [
            t("review.pill_ok"), t("review.pill_sin_telefono"), t("review.pill_enviada_corta"),
        ]
        estado_width = max(fm.horizontalAdvance(s) for s in estado_texts) + 43
        lo, hi = _COLUMN_CLAMP[COL_ESTADO]
        self.table.setColumnWidth(COL_ESTADO, max(lo, min(estado_width, hi)))

        tel_width = 0
        for participant, match in result:
            if participant.phone:
                width = fm.horizontalAdvance(participant.phone) + 12
            else:
                width = 26 + 4
                if match.suggested_name and match.confidence < MATCH_THRESHOLD:
                    label = t("comun.usar_sugerencia", nombre=match.suggested_name)
                    width += fm.horizontalAdvance(label) + 24
            tel_width = max(tel_width, width + 8)
        lo, hi = _COLUMN_CLAMP[COL_TEL]
        self.table.setColumnWidth(COL_TEL, max(lo, min(tel_width, hi)))

    def _set_estado_pill(self, row: int, no_phone: bool, sent_date: str | None) -> None:
        if sent_date:
            pill = Pill(t("review.pill_enviada_corta"), "dup", icon_name="check-check")
            pill.setToolTip(t("rec_revisar.tooltip_duplicado", fecha=sent_date))
        elif no_phone:
            pill = Pill(t("review.pill_sin_telefono"), "warn", icon_name="triangle-alert")
        else:
            pill = Pill(t("review.pill_ok"), "ok", icon_name="check")

        cell = QWidget()
        h = QHBoxLayout(cell)
        h.setContentsMargins(4, 2, 4, 2)
        h.addWidget(pill)
        self.table.setCellWidget(row, COL_ESTADO, cell)

    def _set_tel_cell(self, row: int, phone: str | None, match=None) -> None:
        if phone:
            self.table.setCellWidget(row, COL_TEL, None)
            self.table.setItem(row, COL_TEL, self._make_item(phone))
            return

        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(2, 2, 2, 2)
        h.setSpacing(4)

        new_button = QPushButton("+")
        new_button.setToolTip(t("comun.anadir_contacto_tooltip"))
        new_button.setFixedWidth(22)
        new_button.setStyleSheet("padding: 2px 4px;")
        new_button.clicked.connect(lambda _, r=row: self._quick_add_contact(r))
        h.addWidget(new_button)

        if match is not None and match.suggested_name and match.confidence < MATCH_THRESHOLD:
            use_button = QPushButton(t("comun.usar_sugerencia", nombre=match.suggested_name))
            use_button.setToolTip(t("comun.usar_sugerencia_tooltip", nombre=match.suggested_name))
            use_button.setStyleSheet("padding: 2px 6px;")
            use_button.clicked.connect(
                lambda _, r=row, tel=match.suggested_phone, nom=match.suggested_name:
                    self._use_suggestion(r, nom, tel)
            )
            h.addWidget(use_button)

        # See review_assignments.py's _set_tel_cell for why this stretch
        # is needed: without it a lone "+" drifts to the right edge of
        # the column instead of sitting flush left.
        h.addStretch()

        self.table.setItem(row, COL_TEL, None)
        self.table.setCellWidget(row, COL_TEL, container)

    def _phone_text(self, row: int) -> str:
        item = self.table.item(row, COL_TEL)
        return item.text().strip() if item is not None else ""

    def _show_warning(self, no_phone: int, duplicates: int) -> None:
        parts = []
        if no_phone:
            parts.append(t("review.aviso_sin_telefono", n=no_phone))
        if duplicates:
            parts.append(t("rec_revisar.aviso_duplicado", n=duplicates))
        if parts:
            self.warning_banner.setText(" — ".join(parts) + t("review.revisalas"))
            self.warning_banner.show()
        else:
            self.warning_banner.hide()

    def _quick_add_contact(self, row: int) -> None:
        name = self.table.item(row, COL_NOMBRE).text().strip()
        phone, ok = QInputDialog.getText(
            self, t("comun.nuevo_contacto_titulo"),
            t("comun.telefono_para", nombre=name),
        )
        if not ok or not phone.strip():
            return
        phone = phone.strip()
        if not phone.isdigit():
            QMessageBox.warning(
                self, t("comun.telefono_no_valido_titulo"),
                t("comun.telefono_no_valido_msg"),
            )
            return

        csv_path = Path(self.main_window.config.paths.contacts_csv)
        contacts = load_contacts(csv_path)
        contacts[name] = phone
        save_contacts(csv_path, contacts)

        self._set_tel_cell(row, phone)
        self._set_estado_pill(row, no_phone=False, sent_date=None)
        self._update_warning()

    def _use_suggestion(self, row: int, name: str, phone: str) -> None:
        self.table.item(row, COL_NOMBRE).setText(name)
        self._set_tel_cell(row, phone)
        self._set_estado_pill(row, no_phone=False, sent_date=None)
        self._update_warning()

    def _update_warning(self) -> None:
        no_phone = sum(
            1 for row in range(self.table.rowCount())
            if not self._phone_text(row)
        )
        self._show_warning(no_phone, self._duplicate_count)

    @staticmethod
    def _make_item(text: str, editable: bool = True) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _next(self) -> None:
        participants = self.main_window.reminder_state.participants
        selected = []
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, COL_ENVIAR)
            check = container.findChild(QCheckBox)
            if not check.isChecked():
                continue
            original = participants[row]
            edited = replace(
                original,
                name=self.table.item(row, COL_NOMBRE).text().strip(),
                phone=self._phone_text(row) or None,
            )
            selected.append(edited)

        if not selected:
            QMessageBox.warning(self, t("rec_revisar.nadie_titulo"), t("rec_revisar.nadie_msg"))
            return

        self.main_window.reminder_state.participants = selected
        self.main_window.go_to(10)  # -> confirm and send
