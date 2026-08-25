"""GUI entry point.

Usage:
    python -m assistant.gui.app
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase, QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from .. import i18n
from ..cleanup import cleanup_old_output
from ..config import load_config
from . import style

# `config.json`/`contacts.csv`/etc. are read with paths relative to the
# current working directory (see config.py). Running as a script that
# always matches the project root (the launchers `cd` there before
# starting), but a `.exe` compiled with PyInstaller can start with a
# different working directory depending on how Windows opens it (e.g. a
# shortcut without "Start in" set properly) — so if it's compiled
# (`sys.frozen`), the working directory is forced to wherever the .exe
# itself lives, same as `ROOT` does in check_environment.py.
if getattr(sys, "frozen", False):
    os.chdir(Path(sys.executable).resolve().parent)

# Same reason with `__file__`: inside a frozen .exe it doesn't point to a
# real on-disk path with this folder hierarchy — the icon has to be
# resolved from PyInstaller's bundled folder (`sys._MEIPASS`) when
# compiled, and from the file itself when running as a script.
if getattr(sys, "frozen", False):
    ICON = Path(getattr(sys, "_MEIPASS", ".")) / "assets" / "icon.png"
    _FONTS_DIR = Path(getattr(sys, "_MEIPASS", ".")) / "assets" / "fonts"
else:
    ICON = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.png"
    _FONTS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"


def _load_bundled_fonts() -> None:
    """Fraunces (SIL OFL) is bundled locally — the app has no internet
    access at runtime to pull it from Google Fonts, and system installs
    can't be relied on. Only the two weights the title style actually
    uses (500/600) are shipped, not the full variable font, to keep the
    .exe small."""
    for font_file in _FONTS_DIR.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))


def _choose_initial_language() -> str:
    """Deliberately bilingual dialog (only language names as buttons, no
    full sentences in a language the user might not speak) — it's the
    first thing an English-only speaker sees, before the app knows which
    language to speak to them in."""
    box = QMessageBox()
    box.setWindowTitle("Idioma / Language")
    box.setText("Elige tu idioma / Choose your language")
    es_button = box.addButton("Español", QMessageBox.ButtonRole.AcceptRole)
    box.addButton("English", QMessageBox.ButtonRole.AcceptRole)
    box.exec()
    return "es" if box.clickedButton() is es_button else "en"


def main() -> None:
    # The user's real screen runs a fractional Wayland scale factor
    # (125%) — by default Qt rounds that up to the nearest integer (2.0)
    # for its internal rendering, then the compositor scales the result
    # back down to the real 1.25x, and that extra non-integer resample is
    # what made icons look soft/blurry. PassThrough makes Qt use the
    # exact fractional factor everywhere instead of rounding, which
    # avoids the double conversion. Must be set before QApplication()
    # exists — Qt reads it once, at construction time.
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    if ICON.exists():
        app.setWindowIcon(QIcon(str(ICON)))
    _load_bundled_fonts()

    config = load_config()
    cleanup_old_output(config.paths.output_folder)
    if not config.paths.pdf_template:
        # Fresh install (same signal main_window uses for the "initial
        # setup" notice): no language has really been chosen yet,
        # config.language is just "es" because that's the dataclass
        # default. It has to be asked HERE, before building any page —
        # same as the theme: if it were asked after creating MainWindow,
        # the pages would already be built with the default-language
        # text and wouldn't refresh themselves.
        config.language = _choose_initial_language()
    i18n.set_language(config.language)
    dark = style.resolve_theme(config.theme, app)
    style.apply_theme(dark)
    app.setStyleSheet(style.build_stylesheet())

    # Deliberately deferred import: main_window (and the pages/dialogs it
    # imports) read the colors from style.py via "from .style import X"
    # the first time they're imported — that has to happen AFTER
    # apply_theme(), otherwise they'd always pick up the light palette.
    from .main_window import MainWindow

    window = MainWindow()
    if ICON.exists():
        window.setWindowIcon(QIcon(str(ICON)))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
