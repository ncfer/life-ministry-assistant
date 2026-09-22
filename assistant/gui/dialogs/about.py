from __future__ import annotations

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QVBoxLayout

from ... import __version__
from ...i18n import t
from ...updates import RELEASES_URL, REPO
from ..style import SUCCESS
from ..widgets import IconLabel, NavButton
from ..workers import CheckUpdateThread


class AboutDialog(QDialog):
    """Version, a link to the repository, and the update check.

    The checkbox only governs the check made on startup (main_window);
    opening this dialog always checks, since that's what someone came
    here to find out."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("acerca.titulo"))
        self.resize(440, 260)
        self.main_window = main_window
        self._thread: CheckUpdateThread | None = None
        self._download_url = RELEASES_URL

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel(t("app.titulo"))
        title.setProperty("title", True)
        layout.addWidget(title)

        version_label = QLabel(t("acerca.version", version=__version__))
        version_label.setProperty("subtitle", True)
        layout.addWidget(version_label)

        self.status = QLabel(t("acerca.comprobando"))
        self.status.setProperty("help", True)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.up_to_date = IconLabel("check", SUCCESS)
        self.up_to_date.hide()
        layout.addWidget(self.up_to_date)

        self.download_button = NavButton(
            t("acerca.ver_descarga"), primary=True, icon_name="file-up")
        self.download_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self._download_url)))
        self.download_button.hide()
        # In a plain QVBoxLayout a NavButton stretches to the full dialog
        # width; the row keeps it at its natural size, left-aligned.
        download_row = QHBoxLayout()
        download_row.addWidget(self.download_button)
        download_row.addStretch()
        layout.addLayout(download_row)

        self.check_box = QCheckBox(t("acerca.buscar_actualizaciones"))
        self.check_box.setChecked(main_window.config.check_updates)
        self.check_box.toggled.connect(self._toggle_check_updates)
        layout.addWidget(self.check_box)

        layout.addStretch()

        buttons = QHBoxLayout()
        repo_button = NavButton(t("acerca.repo"), icon_name="link")
        repo_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(f"https://github.com/{REPO}")))
        buttons.addWidget(repo_button)
        buttons.addStretch()
        close_button = NavButton(t("comun.cerrar"), icon_name="x")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self._start_check()

    def _toggle_check_updates(self, checked: bool) -> None:
        self.main_window.config.check_updates = checked
        self.main_window.save_config()

    def _start_check(self) -> None:
        self._thread = CheckUpdateThread(self)
        self._thread.done.connect(self._show_result)
        self._thread.start()

    def _show_result(self, state: str, version: str, url: str) -> None:
        if state == "error":
            self.status.setText(t("acerca.sin_conexion"))
            return
        if state == "al_dia":
            self.status.setText("")
            self.up_to_date.label.setText(t("acerca.al_dia"))
            self.up_to_date.show()
            return
        self._download_url = url
        self.status.setText(t("acerca.hay_nueva", version=version))
        self.download_button.show()
