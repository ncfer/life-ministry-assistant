from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ...history import load_history
from ...i18n import t
from ..widgets import NavButton, Pill, SearchField

COL_WHEN, COL_DATE, COL_NAME, COL_TEL, COL_STATUS, COL_REASON = range(6)


class HistoryDialog(QDialog):
    def __init__(self, history_csv: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("historial.titulo_ventana"))
        self.resize(620, 460)
        self.history_csv = Path(history_csv)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        help_label = QLabel(t("historial.ayuda"))
        help_label.setProperty("help", True)
        layout.addWidget(help_label)

        search_row = QHBoxLayout()
        self.search_box = SearchField()
        self.search_box.setPlaceholderText(t("contactos.buscar_placeholder"))
        self.search_box.textChanged.connect(self._filter)
        search_row.addWidget(self.search_box)
        self.count_label = QLabel("")
        self.count_label.setProperty("help", True)
        search_row.addWidget(self.count_label)
        layout.addLayout(search_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("historial.col_cuando"), t("historial.col_asignacion"), t("historial.col_nombre"),
            t("historial.col_telefono"), t("historial.col_estado"), t("historial.col_motivo"),
        ])
        self.table.setColumnWidth(COL_WHEN, 130)
        self.table.setColumnWidth(COL_DATE, 85)
        self.table.setColumnWidth(COL_NAME, 130)
        self.table.setColumnWidth(COL_TEL, 100)
        self.table.setColumnWidth(COL_STATUS, 95)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_button = NavButton(t("comun.cerrar"), primary=True, icon_name="x")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self._load()

    def _load(self) -> None:
        rows = load_history(self.history_csv)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            when = row["timestamp"].replace("T", " ")
            self.table.setItem(i, COL_WHEN, QTableWidgetItem(when))
            self.table.setItem(i, COL_DATE, QTableWidgetItem(row["assignment_date"]))
            self.table.setItem(i, COL_NAME, QTableWidgetItem(row["name"]))
            self.table.setItem(i, COL_TEL, QTableWidgetItem(row["phone"]))
            self.table.setCellWidget(i, COL_STATUS, self._status_cell(row["status"]))
            self.table.setItem(i, COL_REASON, QTableWidgetItem(row.get("reason", "")))

        self.count_label.setText(t("historial.n_resultados", n=len(rows)))

        if not rows:
            self.table.setRowCount(1)
            item = QTableWidgetItem(t("historial.vacio"))
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 6)

    @staticmethod
    def _status_cell(status: str) -> QWidget:
        # `status` on disk is always the raw "enviado"/"fallido" string
        # (see history.py) regardless of the app's current UI language —
        # only the pill's displayed label is translated.
        if status == "enviado":
            pill = Pill(t("review.pill_enviada_corta"), "ok", icon_name="check")
        else:
            pill = Pill(t("historial.pill_fallido"), "warn", icon_name="x")
        cell = QWidget()
        h = QHBoxLayout(cell)
        h.setContentsMargins(4, 2, 4, 2)
        h.addWidget(pill)
        h.addStretch()
        return cell

    def _filter(self, text: str) -> None:
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NAME)
            name = item.text().lower() if item else ""
            self.table.setRowHidden(row, text not in name)
