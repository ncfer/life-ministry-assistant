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
from ...models import ROOM_LABEL
from ..widgets import NavButton, Pill, StepHeader, WarningBanner
from ..workers import ResolvePhonesThread

# Estado sits right after Enviar (not at the far right) so it's always
# visible even on a narrower window, instead of being the first thing
# scrolled off — see the memory note on this screen for why. Teléfono is
# last: when a phone is missing, that cell itself becomes the place to
# fix it (see _set_tel_cell), so it reads as "the field with the
# problem", not a separate unrelated column.
COL_ENVIAR, COL_ESTADO, COL_FECHA, COL_NUM, COL_TIPO, COL_SALA, COL_NOMBRE, COL_AYUDANTE, COL_TEL = range(9)

# Interactive columns get an initial width from resizeColumnsToContents()
# (see _fill_table), then get clamped into this (min, max) range so one
# unusually long value (a long part title, a long suggested name) can't
# blow the whole table out sideways — the user can still drag them wider
# by hand afterward, this only sets a sane starting point.
_COLUMN_CLAMP = {
    COL_ESTADO: (75, 145),
    COL_NOMBRE: (85, 140),
    COL_AYUDANTE: (75, 120),
    COL_TEL: (85, 400),
}


class ReviewAssignmentsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread = None
        self._duplicate_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(10)

        layout.addWidget(StepHeader(t("review.titulo"), 3))

        self.warning_banner = WarningBanner()
        self.warning_banner.hide()
        layout.addWidget(self.warning_banner)

        help_label = QLabel(t("review.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            t("review.col_enviar"), t("review.col_estado"), t("review.col_fecha"), t("review.col_num"),
            t("review.col_tipo"), t("review.col_sala"), t("review.col_nombre"), t("review.col_ayudante"),
            t("review.col_telefono"),
        ])
        # Column widths are set once real content is loaded (see
        # _fill_table's resizeColumnsToContents() + clamp), so a short
        # VMC (few long names) and a long one (many short ones) both get
        # sensible starting widths instead of one fixed guess for both.
        # COL_TIPO stretches to absorb whatever width is left over, so
        # the table doesn't end with an empty gap on a wide window.
        self.table.setColumnWidth(COL_ENVIAR, 56)
        self.table.setColumnWidth(COL_FECHA, 88)
        self.table.setColumnWidth(COL_NUM, 32)
        self.table.setColumnWidth(COL_SALA, 105)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_TIPO, QHeaderView.ResizeMode.Stretch)
        # Enviar/Fecha/Nº/Sala are narrow utility columns that don't
        # benefit from dragging anyway — Fixed (rather than Interactive)
        # stops Qt's own layout pass from quietly shrinking them to make
        # room elsewhere, which is what was happening here.
        for col in (COL_ENVIAR, COL_FECHA, COL_NUM, COL_SALA):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.hide()
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(2))
        buttons.addWidget(back_button)
        buttons.addStretch()
        self.next_button = NavButton(t("review.generar_vista_previa"), direction="next", primary=True)
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
        self._thread = ResolvePhonesThread(self.main_window.state.assignments, contacts_csv)
        self._thread.done.connect(self._fill_table)
        self._thread.start()

    def _already_sent(self) -> dict[tuple[str, str], str]:
        """{(name, fecha_asignacion_iso): send_date} for what was already sent successfully."""
        history_csv = Path(self.main_window.config.paths.history_csv)
        already_sent = {}
        for row in load_history(history_csv):
            if row["status"] == "enviado":
                key = (row["name"], row["assignment_date"])
                # load_history already comes sorted most-recent-first
                already_sent.setdefault(key, row["timestamp"].split("T")[0])
        return already_sent

    def _fill_table(self, result: list) -> None:
        self.progress_bar.hide()
        self.table.show()
        self.next_button.setEnabled(True)

        already_sent = self._already_sent()
        self.table.setRowCount(len(result))
        self._duplicate_count = sum(1 for a, _m in result if already_sent.get((a.name, a.date.isoformat())))

        # Estado/Teléfono get their column width computed from the real
        # text up front (see _size_estado_and_tel_columns), and ONLY
        # then do the row loop below create their cell widgets. Doing it
        # the other way around — create the widgets, then call
        # resizeColumnsToContents() — measured them while they still had
        # their initial (undersized) geometry, and widening the column
        # afterward didn't reliably resize the already-placed widget: the
        # column grew but the widget's own contents stayed clipped at the
        # old size. A widget created once the column is already the
        # right width doesn't hit that.
        self._size_estado_and_tel_columns(result, already_sent)

        for row, (assignment, match) in enumerate(result):
            sent_date = already_sent.get((assignment.name, assignment.date.isoformat()))

            check = QCheckBox()
            check.setChecked(not sent_date)
            container = QWidget()
            hl = QHBoxLayout(container)
            hl.addWidget(check)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, COL_ENVIAR, container)

            self._set_estado_pill(row, no_phone=not assignment.phone, sent_date=sent_date)

            self.table.setItem(row, COL_FECHA, self._make_item(assignment.date.strftime("%d/%m/%Y"), editable=False))
            self.table.setItem(row, COL_NUM, self._make_item(assignment.number, editable=False))
            part_item = self._make_item(assignment.part, editable=False)
            part_item.setToolTip(assignment.part)
            self.table.setItem(row, COL_TIPO, part_item)
            self.table.setItem(row, COL_SALA, self._make_item(ROOM_LABEL[assignment.room], editable=False))

            self.table.setItem(row, COL_NOMBRE, self._make_item(assignment.name))
            self.table.setItem(row, COL_AYUDANTE, self._make_item(assignment.helper))
            self._set_tel_cell(row, assignment.phone, match)

        self.table.resizeColumnToContents(COL_NOMBRE)
        self.table.resizeColumnToContents(COL_AYUDANTE)
        for col in (COL_NOMBRE, COL_AYUDANTE):
            lo, hi = _COLUMN_CLAMP[col]
            self.table.setColumnWidth(col, max(lo, min(self.table.columnWidth(col), hi)))

        self._update_warning()

    def _size_estado_and_tel_columns(self, result: list, already_sent: dict) -> None:
        fm = QFontMetrics(self.table.font())

        estado_texts = [
            t("review.pill_ok"), t("review.pill_sin_telefono"), t("review.pill_enviada_corta"),
        ]
        # icon (11) + icon-text spacing (3) + pill padding (6+7) + cell margins (4+4)
        estado_width = max(fm.horizontalAdvance(s) for s in estado_texts) + 43
        lo, hi = _COLUMN_CLAMP[COL_ESTADO]
        self.table.setColumnWidth(COL_ESTADO, max(lo, min(estado_width, hi)))

        tel_width = 0
        for assignment, match in result:
            if assignment.phone:
                width = fm.horizontalAdvance(assignment.phone) + 12
            else:
                width = 26 + 4  # "+" button (fixed 22 wide) + spacing
                if match.suggested_name and match.confidence < MATCH_THRESHOLD:
                    label = t("comun.usar_sugerencia", nombre=match.suggested_name)
                    width += fm.horizontalAdvance(label) + 24  # button padding
            tel_width = max(tel_width, width + 8)  # cell margins
        lo, hi = _COLUMN_CLAMP[COL_TEL]
        self.table.setColumnWidth(COL_TEL, max(lo, min(tel_width, hi)))

    def _set_estado_pill(self, row: int, no_phone: bool, sent_date: str | None) -> None:
        if sent_date:
            pill = Pill(t("review.pill_enviada_corta"), "dup", icon_name="check-check")
            pill.setToolTip(t("review.tooltip_duplicado", fecha=sent_date))
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
        # An empty phone cell doubles as the fix-it spot: instead of a
        # blank cell the user has to know to double-click, it shows the
        # actions that resolve it directly (see the review-screen
        # rework in the memory for why these moved out of Estado).
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

        # Without an explicit trailing stretch, a single fixed-width "+"
        # alone in this layout ends up flush against the RIGHT edge of
        # the (often much wider) column instead of sitting next to the
        # text like the two-button case does — Qt's QHBoxLayout doesn't
        # reliably default to left-aligning a lone non-expanding widget
        # when there's leftover space and no stretch item telling it
        # where that space should go.
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
            parts.append(t("review.aviso_duplicado", n=duplicates))
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
        assignments = self.main_window.state.assignments
        selected = []
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, COL_ENVIAR)
            check = container.findChild(QCheckBox)
            if not check.isChecked():
                continue
            original = assignments[row]
            edited = replace(
                original,
                name=self.table.item(row, COL_NOMBRE).text().strip(),
                helper=self.table.item(row, COL_AYUDANTE).text().strip(),
                phone=self._phone_text(row) or None,
            )
            selected.append(edited)

        self.main_window.state.assignments = selected
        self.main_window.go_to(4)  # -> preview
