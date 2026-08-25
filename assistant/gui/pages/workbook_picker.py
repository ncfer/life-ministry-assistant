from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QProgressBar, QVBoxLayout, QWidget,
)

from ...i18n import t
from ..file_dialogs import choose_file
from ..widgets import NavButton, SourceCard, StepHeader
from ..workers import (
    DownloadWorkbookDriveThread, DownloadWorkbookPadletThread, ParseWorkbookThread,
)


class WorkbookPickerPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread: ParseWorkbookThread | DownloadWorkbookPadletThread | DownloadWorkbookDriveThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(14)

        layout.addWidget(StepHeader(t("workbook_picker.titulo"), 1))

        help_label = QLabel(t("workbook_picker.ayuda_asignaciones"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.file_row = SourceCard("file-up", t("workbook_picker.fuente_archivo_titulo"), t("workbook_picker.fuente_archivo_desc"))
        self.file_row.clicked.connect(self._choose_file)
        cards_row.addWidget(self.file_row)

        self.padlet_row = SourceCard("link", t("workbook_picker.fuente_padlet_titulo"), t("workbook_picker.fuente_padlet_desc_sin_configurar"))
        self.padlet_row.clicked.connect(self._search_padlet)
        cards_row.addWidget(self.padlet_row)

        self.drive_row = SourceCard("cloud", t("workbook_picker.fuente_drive_titulo"), t("workbook_picker.fuente_drive_desc_sin_configurar"))
        self.drive_row.clicked.connect(self._search_drive)
        cards_row.addWidget(self.drive_row)

        layout.addLayout(cards_row)

        self.file_label = QLabel(t("workbook_picker.ningun_archivo"))
        self.file_label.setProperty("help", True)
        layout.addWidget(self.file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(0))
        buttons.addWidget(back_button)
        buttons.addStretch()
        layout.addLayout(buttons)

    def enter(self) -> None:
        self.file_label.setText(t("workbook_picker.ningun_archivo"))
        self.progress_bar.hide()
        self._set_buttons_enabled(True)

        padlet_configured = bool(self.main_window.config.padlet.url)
        self.padlet_row.set_subtitle(
            t("workbook_picker.fuente_padlet_desc_configurado") if padlet_configured
            else t("workbook_picker.fuente_padlet_desc_sin_configurar")
        )
        self.padlet_row.set_configured(padlet_configured)
        drive_configured = bool(self.main_window.config.drive_link)
        self.drive_row.set_subtitle(
            t("workbook_picker.fuente_drive_desc_configurado") if drive_configured
            else t("workbook_picker.fuente_drive_desc_sin_configurar")
        )
        self.drive_row.set_configured(drive_configured)

    def _choose_file(self) -> None:
        path = choose_file(self, t("workbook_picker.dialogo_seleccionar"), str(Path.home()), "PDF (*.pdf)")
        if not path:
            return
        path = Path(path)
        self.file_label.setText(path.name)
        self.main_window.state.workbook_path = path
        self.main_window.state.reset_from_workbook()

        self._set_buttons_enabled(False)
        self.progress_bar.show()
        self._thread = ParseWorkbookThread(path)
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _search_padlet(self) -> None:
        padlet = self.main_window.config.padlet
        if not padlet.url:
            QMessageBox.information(
                self, t("workbook_picker.padlet_falta_titulo"),
                t("workbook_picker.padlet_falta_msg"),
            )
            return

        self.file_label.setText(t("workbook_picker.buscando_padlet"))
        self._set_buttons_enabled(False)
        self.progress_bar.show()
        folder = Path(self.main_window.config.paths.output_folder)
        self._thread = DownloadWorkbookPadletThread(padlet, folder)
        self._thread.done.connect(self._on_padlet_downloaded)
        self._thread.error.connect(self._on_padlet_error)
        self._thread.start()

    def _on_padlet_downloaded(self, weeks: dict, path: Path) -> None:
        self.file_label.setText(t("workbook_picker.descargado_padlet", nombre=path.name))
        self.main_window.state.workbook_path = path
        self.main_window.state.reset_from_workbook()
        self._on_done(weeks)

    def _on_padlet_error(self, message: str) -> None:
        self._set_buttons_enabled(True)
        self.progress_bar.hide()
        self.file_label.setText(t("workbook_picker.ningun_archivo"))
        QMessageBox.critical(self, t("workbook_picker.padlet_error_titulo"), message)

    def _search_drive(self) -> None:
        drive_link = self.main_window.config.drive_link
        if not drive_link:
            QMessageBox.information(
                self, t("workbook_picker.drive_falta_titulo"),
                t("workbook_picker.drive_falta_msg"),
            )
            return

        self.file_label.setText(t("workbook_picker.buscando_drive"))
        self._set_buttons_enabled(False)
        self.progress_bar.show()
        folder = Path(self.main_window.config.paths.output_folder)
        self._thread = DownloadWorkbookDriveThread(drive_link, folder)
        self._thread.done.connect(self._on_drive_downloaded)
        self._thread.error.connect(self._on_drive_error)
        self._thread.start()

    def _on_drive_downloaded(self, weeks: dict, path: Path) -> None:
        self.file_label.setText(t("workbook_picker.descargado_drive", nombre=path.name))
        self.main_window.state.workbook_path = path
        self.main_window.state.reset_from_workbook()
        self._on_done(weeks)

    def _on_drive_error(self, message: str) -> None:
        self._set_buttons_enabled(True)
        self.progress_bar.hide()
        self.file_label.setText(t("workbook_picker.ningun_archivo"))
        QMessageBox.critical(self, t("workbook_picker.drive_error_titulo"), message)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self.file_row.setEnabled(enabled)
        self.padlet_row.setEnabled(enabled)
        self.drive_row.setEnabled(enabled)

    def _on_done(self, weeks: dict) -> None:
        self._set_buttons_enabled(True)
        self.progress_bar.hide()
        self.main_window.state.weeks = weeks
        self.main_window.go_to(2)  # -> pick week

    def _on_error(self, message: str) -> None:
        self._set_buttons_enabled(True)
        self.progress_bar.hide()
        QMessageBox.critical(self, t("workbook_picker.error_leer_titulo"), message)
