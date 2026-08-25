from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ...contacts import load_contacts, save_contacts
from ...i18n import t
from ..widgets import Avatar, IconButton, NavButton, SearchField

COL_AVATAR, COL_NOMBRE, COL_TEL = range(3)


class ContactsEditorDialog(QDialog):
    def __init__(self, contacts_csv: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("contactos.titulo_ventana"))
        self.resize(480, 480)
        self.csv_path = Path(contacts_csv)
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)
        help_label = QLabel(t("contactos.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
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

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["", t("contactos.col_nombre"), t("contactos.col_telefono")])
        self.table.setColumnWidth(COL_AVATAR, 38)
        self.table.setColumnWidth(COL_NOMBRE, 220)
        self.table.setColumnWidth(COL_TEL, 120)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.itemChanged.connect(self._on_edit)
        layout.addWidget(self.table)

        # A single row for every action instead of two stacked ones: the
        # add/delete icon buttons read as row-level tools (act on the
        # table), Cancelar/Guardar as the dialog-level ones (act on the
        # whole dialog) — grouping them this way needs no extra label.
        buttons = QHBoxLayout()
        add_button = IconButton("plus")
        add_button.setToolTip(t("contactos.anadir"))
        add_button.clicked.connect(self._add_row)
        buttons.addWidget(add_button)
        delete_button = IconButton("trash-2")
        delete_button.setToolTip(t("contactos.borrar_seleccionado"))
        delete_button.clicked.connect(self._delete_selected)
        buttons.addWidget(delete_button)
        buttons.addStretch()
        close_button = NavButton(t("comun.cerrar_sin_guardar"), icon_name="x")
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)
        save_button = NavButton(t("comun.guardar"), primary=True, icon_name="check")
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

        self._load()

    def _load(self) -> None:
        self._loading = True
        contacts = load_contacts(self.csv_path)
        self.table.setRowCount(0)
        for name, phone in sorted(contacts.items()):
            self._append_row(name, phone)
        self._loading = False
        self._update_count()

    def _append_row(self, name: str = "", phone: str = "") -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, COL_NOMBRE, QTableWidgetItem(name))
        self.table.setItem(row, COL_TEL, QTableWidgetItem(phone))
        self._set_avatar_cell(row, name)

    def _set_avatar_cell(self, row: int, name: str) -> None:
        cell = QWidget()
        h = QHBoxLayout(cell)
        h.setContentsMargins(0, 0, 0, 0)
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.addWidget(Avatar(name, size=22))
        self.table.setCellWidget(row, COL_AVATAR, cell)

    def _refresh_avatars(self) -> None:
        # Cell widgets set via setCellWidget() don't follow their row
        # when sortItems() reorders the underlying items — a known
        # QTableWidget limitation — so every avatar has to be rebuilt
        # from that row's CURRENT name after any sort, instead of
        # relying on the widget having "moved" with its contact.
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, COL_NOMBRE)
            self._set_avatar_cell(row, name_item.text() if name_item else "")

    def _add_row(self) -> None:
        self._append_row()
        self.table.setCurrentCell(self.table.rowCount() - 1, COL_NOMBRE)
        self._update_count()

    def _delete_selected(self) -> None:
        rows = {i.row() for i in self.table.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)
        self._update_count()

    def _update_count(self) -> None:
        self.count_label.setText(t("contactos.n_contactos", n=self.table.rowCount()))

    def _on_edit(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        self.table.sortItems(COL_NOMBRE, Qt.SortOrder.AscendingOrder)
        self._refresh_avatars()

    def _filter(self, text: str) -> None:
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_NOMBRE)
            name = item.text().lower() if item else ""
            self.table.setRowHidden(row, text not in name)

    def _save(self) -> None:
        contacts = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, COL_NOMBRE)
            phone_item = self.table.item(row, COL_TEL)
            name = name_item.text().strip() if name_item else ""
            phone = phone_item.text().strip() if phone_item else ""
            if not name or not phone:
                continue
            if not phone.isdigit():
                QMessageBox.warning(
                    self, t("comun.telefono_no_valido_titulo"),
                    t("contactos.telefono_invalido_de", nombre=name),
                )
                return
            contacts[name] = phone

        save_contacts(self.csv_path, contacts)
        QMessageBox.information(self, t("comun.guardado_titulo"), t("contactos.n_guardados", n=len(contacts)))
        self.accept()
