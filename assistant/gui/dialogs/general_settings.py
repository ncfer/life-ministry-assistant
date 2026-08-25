from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)

from ...config import Config, PadletConfig
from ...i18n import AVAILABLE_LANGUAGES, t
from ..file_dialogs import choose_file, choose_folder
from ..widgets import CollapsibleSection, NavButton

# A per-section accent color (blue/green/purple/amber) was tried and
# explicitly rejected by the user — "rompe la estética del programa",
# every other screen in the app uses a single PRIMARY accent throughout,
# so these sections stay PRIMARY too instead of introducing their own
# palette.


class GeneralSettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("config_general.titulo_ventana"))
        self.resize(540, 560)
        self.config = config

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 26, 30, 18)
        layout.setSpacing(10)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        help_label = QLabel(t("config_general.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        layout.addSpacing(6)

        # Rutas and Padlet start expanded (the two most commonly touched
        # groups); Drive and Idioma/Tema start collapsed — matches the
        # direction the user picked from the mockup comparison.
        paths_section = CollapsibleSection("file-up", t("config_general.rutas_titulo"), expanded=True)
        form = QFormLayout()
        form.setVerticalSpacing(14)
        self.s89_field = self._file_field(
            config.paths.pdf_template, t("config_general.s89_pdf_dialogo"), "PDF (*.pdf)"
        )
        form.addRow(t("config_general.s89_pdf"), self.s89_field["row"])
        self.output_field = self._folder_field(config.paths.output_folder)
        form.addRow(t("config_general.carpeta_salida"), self.output_field["row"])
        paths_section.body_layout.addLayout(form)
        # Contacts, message and reminder-message paths are no longer
        # editable here on purpose: all three already have their own
        # dedicated editor in the app (Contacts / Message / Reminder
        # message), and since 2026-08-24 they always live next to the app
        # itself — a path picker for them was redundant. This button
        # covers the one real remaining reason to leave the app: opening
        # the files directly (e.g. in a spreadsheet) or checking output/.
        open_folder_button = NavButton(t("config_general.abrir_carpeta"), icon_name="folder-open")
        open_folder_button.clicked.connect(self._open_install_folder)
        paths_section.body_layout.addWidget(open_folder_button)
        layout.addWidget(paths_section)

        padlet_section = CollapsibleSection("link", t("config_general.padlet_titulo_corto"), expanded=True)
        padlet_form = QFormLayout()
        padlet_form.setVerticalSpacing(14)
        self.padlet_url_field = QLineEdit(config.padlet.url)
        self.padlet_url_field.setPlaceholderText("https://padlet.com/username/board-...")
        padlet_form.addRow(t("config_general.padlet_url"), self.padlet_url_field)
        self.padlet_password_field = QLineEdit(config.padlet.password)
        self.padlet_password_field.setEchoMode(QLineEdit.EchoMode.Password)
        padlet_form.addRow(t("config_general.padlet_password"), self.padlet_password_field)
        self.padlet_title_field = QLineEdit(config.padlet.workbook_title)
        self.padlet_title_field.setPlaceholderText("VIDA Y MINISTERIO")
        padlet_form.addRow(t("config_general.padlet_workbook_title"), self.padlet_title_field)
        padlet_section.body_layout.addLayout(padlet_form)
        layout.addWidget(padlet_section)

        drive_section = CollapsibleSection("cloud", t("config_general.drive_titulo_corto"), expanded=False)
        drive_form = QFormLayout()
        drive_form.setVerticalSpacing(14)
        self.drive_link_field = QLineEdit(config.drive_link)
        self.drive_link_field.setPlaceholderText("https://drive.google.com/file/d/...")
        drive_form.addRow(t("config_general.drive_link"), self.drive_link_field)
        drive_section.body_layout.addLayout(drive_form)
        drive_note = QLabel(t("config_general.drive_nota"))
        drive_note.setProperty("help", True)
        drive_section.body_layout.addWidget(drive_note)
        layout.addWidget(drive_section)

        prefs_section = CollapsibleSection("sliders", t("config_general.preferencias_titulo"), expanded=False)

        language_row = QHBoxLayout()
        language_row.addWidget(QLabel(t("config_general.idioma")))
        self.language_combo = QComboBox()
        self._language_codes: list[str] = list(AVAILABLE_LANGUAGES.keys())
        for name in AVAILABLE_LANGUAGES.values():
            self.language_combo.addItem(name)
        try:
            current_index = self._language_codes.index(config.language)
        except ValueError:
            current_index = self._language_codes.index("es")
        self.language_combo.setCurrentIndex(current_index)
        language_row.addWidget(self.language_combo)
        language_row.addStretch()
        prefs_section.body_layout.addLayout(language_row)

        language_note = QLabel(t("config_general.idioma_nota"))
        language_note.setProperty("help", True)
        prefs_section.body_layout.addWidget(language_note)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel(t("config_general.tema")))
        self.theme_combo = QComboBox()
        self._theme_codes = ["claro", "oscuro", "sistema"]
        theme_labels = {
            "claro": t("config_general.tema_claro"),
            "oscuro": t("config_general.tema_oscuro"),
            "sistema": t("config_general.tema_sistema"),
        }
        for code in self._theme_codes:
            self.theme_combo.addItem(theme_labels[code])
        try:
            theme_index = self._theme_codes.index(config.theme)
        except ValueError:
            theme_index = self._theme_codes.index("sistema")
        self.theme_combo.setCurrentIndex(theme_index)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        prefs_section.body_layout.addLayout(theme_row)

        theme_note = QLabel(t("config_general.tema_nota"))
        theme_note.setProperty("help", True)
        prefs_section.body_layout.addWidget(theme_note)
        layout.addWidget(prefs_section)

        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.setContentsMargins(30, 12, 30, 18)
        cancel_button = NavButton(t("comun.cancelar"), icon_name="x")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)
        buttons.addStretch()
        save_button = NavButton(t("comun.guardar"), primary=True, icon_name="check")
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)
        outer.addLayout(buttons)

    def _file_field(self, value: str, title: str, file_filter: str) -> dict:
        edit = QLineEdit(value)
        button = NavButton(t("comun.elegir"), icon_name="folder-open")
        button.clicked.connect(lambda: self._choose_file(edit, title, file_filter))
        row = QHBoxLayout()
        row.addWidget(edit)
        row.addWidget(button)
        return {"edit": edit, "row": self._wrap(row)}

    def _folder_field(self, value: str) -> dict:
        edit = QLineEdit(value)
        button = NavButton(t("comun.elegir"), icon_name="folder-open")
        button.clicked.connect(lambda: self._choose_folder(edit))
        row = QHBoxLayout()
        row.addWidget(edit)
        row.addWidget(button)
        return {"edit": edit, "row": self._wrap(row)}

    @staticmethod
    def _wrap(layout: QHBoxLayout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def _choose_file(self, edit: QLineEdit, title: str, file_filter: str) -> None:
        path = choose_file(self, title, edit.text(), file_filter)
        if path:
            edit.setText(path)

    def _choose_folder(self, edit: QLineEdit) -> None:
        path = choose_folder(self, t("config_general.carpeta_salida_dialogo"), edit.text())
        if path:
            edit.setText(path)

    def _open_install_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path.cwd())))

    def _save(self) -> None:
        theme = self._theme_codes[self.theme_combo.currentIndex()]
        language = self._language_codes[self.language_combo.currentIndex()]

        self.config = replace(
            self.config,
            paths=replace(
                self.config.paths,
                pdf_template=self.s89_field["edit"].text().strip(),
                output_folder=self.output_field["edit"].text().strip(),
            ),
            padlet=PadletConfig(
                url=self.padlet_url_field.text().strip(),
                password=self.padlet_password_field.text(),
                workbook_title=self.padlet_title_field.text().strip() or "VIDA Y MINISTERIO",
            ),
            drive_link=self.drive_link_field.text().strip(),
            theme=theme,
            language=language,
        )
        self.accept()
