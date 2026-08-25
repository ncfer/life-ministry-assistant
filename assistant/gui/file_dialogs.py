"""File/folder dialogs with a guaranteed theme.

QFileDialog.getOpenFileName() with DontUseNativeDialog uses Qt's own
widget, but that widget mixes our global QSS (which only covers QLabel,
QPushButton, etc.) with the system palette for the parts we don't cover
(the file view is an internal QTreeView/QListView) — on a system with a
dark theme that can result in dark text on a dark background again. To
avoid this entirely, the dialog is built by hand and given its own
stylesheet that explicitly covers ALL the relevant internal widgets.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QWidget

from .style import BORDER, CARD_BG, PRIMARY, TEXT

_DIALOG_STYLE = f"""
QFileDialog, QWidget {{
    background-color: {CARD_BG};
    color: {TEXT};
}}
QListView, QTreeView {{
    background-color: {CARD_BG};
    color: {TEXT};
    alternate-background-color: {CARD_BG};
}}
QTreeView::item, QListView::item {{
    color: {TEXT};
}}
QTreeView::item:selected, QListView::item:selected {{
    background-color: {PRIMARY};
    color: white;
}}
QHeaderView::section {{
    background-color: #eef0f3;
    color: {TEXT};
    border: none;
    padding: 6px;
}}
QLineEdit, QComboBox {{
    background-color: {CARD_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px;
}}
QPushButton {{
    background-color: {CARD_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 14px;
}}
QLabel {{
    color: {TEXT};
    background-color: transparent;
}}
QToolButton {{
    color: {TEXT};
    background-color: transparent;
}}
"""


def _prepare(dialog: QFileDialog) -> None:
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    dialog.setStyleSheet(_DIALOG_STYLE)


def choose_file(parent: QWidget, title: str, directory: str, file_filter: str) -> str:
    dialog = QFileDialog(parent, title, directory, file_filter)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    _prepare(dialog)
    if dialog.exec():
        files = dialog.selectedFiles()
        return files[0] if files else ""
    return ""


def choose_folder(parent: QWidget, title: str, directory: str) -> str:
    dialog = QFileDialog(parent, title, directory)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    _prepare(dialog)
    if dialog.exec():
        files = dialog.selectedFiles()
        return files[0] if files else ""
    return ""
