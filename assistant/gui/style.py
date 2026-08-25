"""App visual theme: minimalist, compact, with light/dark mode support
(manual or automatic based on the system). No emojis or decoration —
plain text and buttons.

Important: never use a `*` selector for `color`/`background-color` in the
stylesheet. That style applies to EVERYTHING living in the same
QApplication, including native system dialogs (the file picker, for
example) — a `*` that's too broad once broke the file picker (dark text
forced over its own dark background, unreadable). The selectors here only
target the widgets this app itself draws.

How the theme changes at startup time: `apply_theme()` is called in
app.py BEFORE importing main_window (and therefore before
widgets.py/review_assignments.py/etc. do `from .style import PRIMARY` —
that import only reads the value once, the first time it runs). Changing
the theme requires restarting the app.
"""
from __future__ import annotations

from pathlib import Path

# Absolute path (QSS url() resolution isn't reliably relative to cwd
# across platforms) to the checkmark glyph used inside a checked
# checkbox — see build_stylesheet() below.
_CHECK_ICON = (Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "check-white.png").as_posix()

# PRIMARY is a neutral institutional blue, chosen by hand (it doesn't
# follow any third-party brand guideline); change it here if you want a
# different tone.
LIGHT_PALETTE = dict(
    BG="#f6f5f2",
    CARD_BG="#ffffff",
    BORDER="#e4e1da",
    BORDER_SHADE="#d6d2c8",
    TEXT="#20242c",
    TEXT_MUTED="#767e8c",
    PRIMARY="#1c5c85",
    PRIMARY_DEEP="#123f5c",
    PRIMARY_HOVER="#154b6c",
    PRIMARY_DISABLED_BG="#a7c2d3",
    PRIMARY_DISABLED_TEXT="#47494b",
    ACCENT="#c07a3e",
    ACCENT_TINT="#f7ecdf",
    SUCCESS="#1f9254",
    WARNING_BG="#fbeceb",
    WARNING_TEXT="#a8342a",
    WARNING_BORDER="#f0c9c6",
    DUPLICATE_BG="#fdf1d6",
    DUPLICATE_TEXT="#8a6a1f",
    DUPLICATE_BORDER="#eeddab",
    SUCCESS_PILL_BG="#e8f5ee",
    SUCCESS_PILL_BORDER="#c3e3d2",
    SELECTION="#d7e6ee",
    DISABLED_BG="#eef0f3",
    DISABLED_TEXT="#65686e",
    HEADER_BG="#eef0f0",
    ICON_BADGE_BG="#e5eef4",
    ROW_HOVER_BG="#eef1ef",
    BUBBLE_WRAP_BG="#eef2f6",
    BUBBLE_BG="#d8e8f5",
    BUBBLE_BORDER="#b3d0e8",
    BUBBLE_TEXT="#173853",
    BUBBLE_ATTACH_BG="rgba(0, 0, 0, 0.05)",
)

DARK_PALETTE = dict(
    BG="#1c1e22",
    CARD_BG="#26292e",
    BORDER="#383c43",
    BORDER_SHADE="#464b53",
    TEXT="#e7e9ec",
    TEXT_MUTED="#9aa1ab",
    PRIMARY="#5aa3d6",
    PRIMARY_DEEP="#3d7ba8",
    PRIMARY_HOVER="#75b4e0",
    PRIMARY_DISABLED_BG="#33475a",
    PRIMARY_DISABLED_TEXT="#b0b8c0",
    ACCENT="#d99a5f",
    ACCENT_TINT="#3a2e1f",
    SUCCESS="#3fbd75",
    WARNING_BG="#3a2523",
    WARNING_TEXT="#e58a80",
    WARNING_BORDER="#5a332f",
    DUPLICATE_BG="#3a3220",
    DUPLICATE_TEXT="#e0c069",
    DUPLICATE_BORDER="#5a4d2c",
    SUCCESS_PILL_BG="#1f3327",
    SUCCESS_PILL_BORDER="#2c4536",
    SELECTION="#2d4356",
    DISABLED_BG="#2c2f34",
    DISABLED_TEXT="#979ba1",
    HEADER_BG="#202226",
    ICON_BADGE_BG="#233240",
    ROW_HOVER_BG="#2a2e34",
    BUBBLE_WRAP_BG="#141a20",
    BUBBLE_BG="#163f5c",
    BUBBLE_BORDER="#1f5678",
    BUBBLE_TEXT="#dcedf7",
    BUBBLE_ATTACH_BG="rgba(255, 255, 255, 0.08)",
)

# Filled in by calling apply_theme() — defaults = light, so an accidental
# uninitialized import doesn't break anything.
globals().update(LIGHT_PALETTE)


def is_system_dark(app) -> bool:
    """Simple heuristic: if the system's window background color is dark,
    assume the user has dark mode enabled."""
    color = app.palette().window().color()
    return color.lightness() < 128


def resolve_theme(theme_config: str, app) -> bool:
    """Returns True if the dark palette should be used."""
    if theme_config == "oscuro":
        return True
    if theme_config == "claro":
        return False
    return is_system_dark(app)  # "sistema"


def apply_theme(dark: bool) -> None:
    globals().update(DARK_PALETTE if dark else LIGHT_PALETTE)


def build_stylesheet() -> str:
    return f"""
QMainWindow, QDialog {{
    background-color: {BG};
}}

QLabel, QPushButton, QCheckBox, QRadioButton, QLineEdit, QTextEdit,
QSpinBox, QComboBox, QTableWidget, QListWidget, QHeaderView::section {{
    font-family: "Inter", "Noto Sans", "DejaVu Sans", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {TEXT};
}}

QLabel[title="true"] {{
    font-family: "Fraunces", "Georgia", "Noto Serif", serif;
    font-size: 21px;
    font-weight: 600;
}}

QLabel[subtitle="true"] {{
    font-size: 10px;
    font-weight: 600;
    color: {TEXT_MUTED};
}}

QLabel[warning="true"] {{
    background-color: {WARNING_BG};
    color: {WARNING_TEXT};
    border: 1px solid {WARNING_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
}}

QWidget[warningbanner="true"] {{
    background-color: {WARNING_BG};
    border: 1px solid {WARNING_BORDER};
    border-radius: 8px;
}}
QLabel[warningbanner_text="true"] {{
    color: {WARNING_TEXT};
    background: transparent;
    border: none;
    padding: 0;
}}

QWidget[pill="warn"] {{
    background-color: {WARNING_BG};
    border: 1px solid {WARNING_BORDER};
    border-radius: 9px;
}}
QWidget[pill="warn"] QLabel[pill_text="true"] {{ color: {WARNING_TEXT}; }}
QWidget[pill="dup"] {{
    background-color: {DUPLICATE_BG};
    border: 1px solid {DUPLICATE_BORDER};
    border-radius: 9px;
}}
QWidget[pill="dup"] QLabel[pill_text="true"] {{ color: {DUPLICATE_TEXT}; }}
QWidget[pill="ok"] {{
    background-color: {SUCCESS_PILL_BG};
    border: 1px solid {SUCCESS_PILL_BORDER};
    border-radius: 9px;
}}
QWidget[pill="ok"] QLabel[pill_text="true"] {{ color: {SUCCESS}; }}
QLabel[pill_text="true"] {{
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}}

QWidget[statusdot="warn"] {{
    background-color: {WARNING_BG};
    border-radius: 10px;
}}
QWidget[statusdot="ok"] {{
    background-color: {SUCCESS_PILL_BG};
    border-radius: 10px;
}}

QFrame[logrow="true"] {{
    background-color: transparent;
    border-bottom: 1px solid {BORDER};
}}
QLabel[logrow_reason="true"] {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QFrame[collapsible_header="true"] {{
    background-color: transparent;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
}}
QFrame[collapsible_header="true"]:hover {{
    background-color: {ROW_HOVER_BG};
}}

QFrame[iconbutton="true"] {{
    background-color: transparent;
    border: 1px solid {BORDER};
    border-radius: 7px;
}}
QFrame[iconbutton="true"]:hover {{
    background-color: {ROW_HOVER_BG};
}}

QPushButton[chip="true"] {{
    background-color: {ICON_BADGE_BG};
    color: {PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
    font-family: "DejaVu Sans Mono", "Consolas", monospace;
}}
QPushButton[chip="true"]:hover {{
    background-color: {SELECTION};
}}

QWidget[bubblewrap="true"] {{
    background-color: {BUBBLE_WRAP_BG};
    border-radius: 11px;
}}
QWidget[bubble="true"] {{
    background-color: {BUBBLE_BG};
    border: 1px solid {BUBBLE_BORDER};
    border-radius: 10px;
}}
QLabel[bubble_text="true"] {{
    color: {BUBBLE_TEXT};
    font-size: 13px;
    background: transparent;
}}
QWidget[bubble_attach="true"] {{
    background-color: {BUBBLE_ATTACH_BG};
    border-radius: 6px;
}}
QLabel[bubble_attach_text="true"] {{
    color: {BUBBLE_TEXT};
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}}

QLabel[help="true"] {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QPushButton {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 13px;
    color: {TEXT};
}}
QPushButton:hover {{
    border-color: {TEXT_MUTED};
}}
QPushButton:disabled {{
    color: {DISABLED_TEXT};
    background-color: {DISABLED_BG};
    border-color: {BORDER};
}}

QPushButton[large="true"] {{
    font-size: 13px;
    padding: 9px 16px;
}}

QPushButton[primary="true"] {{
    background-color: {PRIMARY_DEEP};
    color: white;
    border: none;
}}
QPushButton[primary="true"]:hover {{
    background-color: {PRIMARY_HOVER};
}}
QPushButton[primary="true"]:disabled {{
    background-color: {PRIMARY_DISABLED_BG};
    color: {PRIMARY_DISABLED_TEXT};
}}

QFrame[navbutton="plain"] {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 5px;
}}
QFrame[navbutton="plain"]:hover {{
    border-color: {TEXT_MUTED};
}}
QFrame[navbutton="plain"]:disabled {{
    background-color: {DISABLED_BG};
    border-color: {BORDER};
}}
QFrame[navbutton="primary"] {{
    background-color: {PRIMARY_DEEP};
    border: none;
    border-radius: 5px;
}}
QFrame[navbutton="primary"]:hover {{
    background-color: {PRIMARY_HOVER};
}}
QFrame[navbutton="primary"]:disabled {{
    background-color: {PRIMARY_DISABLED_BG};
}}
/* navbutton_text's color is set directly in Python (NavButton._apply_label_color)
   rather than via QSS here — a QFrame[navbutton="primary"] QLabel[...]
   descendant selector proved unreliable in practice, see NavButton's
   docstring/comment. Only layout-affecting properties belong here. */
QLabel[navbutton_text="true"] {{
    font-size: 13px;
}}

QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {CARD_BG};
    border: 2px solid {BORDER};
    border-radius: 4px;
    padding: 4px 7px;
    color: {TEXT};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border: 2px solid {PRIMARY};
}}

QFrame[searchfield="true"] {{
    background-color: {CARD_BG};
    border: 2px solid {BORDER};
    border-radius: 4px;
}}
QFrame[searchfield="focused"] {{
    background-color: {CARD_BG};
    border: 2px solid {PRIMARY};
    border-radius: 4px;
}}
QLineEdit[searchfield_input="true"] {{
    background-color: transparent;
    border: none;
    padding: 4px 0;
}}

/* QComboBox's dropdown list is a separate top-level popup — without
explicitly styling it, its background falls back to the OS/system theme
instead of this app's, while its text color still inherits from the
QComboBox rule above. If the app's theme is set to the opposite of the
OS theme (e.g. app "Claro" on a dark desktop), that mismatch produces
unreadable text (dark text forced onto the OS's own dark popup
background, or the reverse) — this makes the popup use the same palette
as everything else in the app regardless of the OS theme. */
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {SELECTION};
    selection-color: {TEXT};
    outline: none;
}}

QTableWidget, QListWidget {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 5px;
    gridline-color: {BORDER};
}}
QTableWidget::item, QListWidget::item {{
    padding: 5px;
}}
QTableWidget::item:selected, QListWidget::item:selected {{
    background-color: {SELECTION};
    color: {TEXT};
}}
QListWidget::indicator, QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px;
    height: 17px;
    border: 2px solid {TEXT_MUTED};
    background-color: {CARD_BG};
    border-radius: 5px;
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
QListWidget::indicator:checked, QCheckBox::indicator:checked {{
    background-color: {PRIMARY_DEEP};
    border-color: {PRIMARY_DEEP};
    image: url({_CHECK_ICON});
}}
QRadioButton::indicator:checked {{
    background-color: {PRIMARY_DEEP};
    border-color: {PRIMARY_DEEP};
}}
QListWidget::indicator:hover, QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {PRIMARY};
}}

QHeaderView {{
    background-color: {HEADER_BG};
}}
QHeaderView::section {{
    background-color: {HEADER_BG};
    color: {TEXT_MUTED};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 11px;
}}
QTableCornerButton::section {{
    background-color: {HEADER_BG};
    border: none;
}}

QProgressBar {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 5px;
    text-align: center;
    height: 15px;
    color: {TEXT};
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 4px;
}}

QScrollArea, QFrame {{
    border: none;
}}
/* QScrollArea's own internal viewport widget (the plain QWidget that
actually holds whatever's set via setWidget(), one level up from it —
NOT two, that would also match a QFrame[card] set as the scrolled
widget itself, since QFrame IS-A QWidget for selector purposes, and
overwrite ITS OWN background) has no background set by default — where
a rounded-corner Card recedes from the viewport's own square bounds,
that unstyled viewport was showing through underneath, looking like a
dark wedge cut into the card's corner. Making it transparent lets the
page's own background show there instead, same as everywhere else
outside the card. */
QScrollArea, QScrollArea > QWidget {{
    background: transparent;
}}

/* Same reason as QComboBox's popup below: without an explicit style,
the scrollbar falls back to the OS/system theme instead of the app's
own — on this machine that meant a native dark scrollbar showing up
inside an otherwise light-themed window. */
QScrollBar:vertical {{
    background: transparent;
    width: 11px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    border: none;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 11px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 5px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_MUTED};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    border: none;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QFrame[card="true"] {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-bottom: 2px solid {BORDER_SHADE};
    border-radius: 7px;
}}

QFrame[optioncard="true"] {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
}}
QFrame[optioncard="true"]:hover {{
    border-color: {TEXT_MUTED};
}}
QFrame[optioncard="selected"] {{
    background-color: {ICON_BADGE_BG};
    border: 1.5px solid {PRIMARY};
}}
QWidget[optioncard_badge="true"] {{
    background-color: {ICON_BADGE_BG};
    border-radius: 9px;
}}
QWidget[optioncard_badge="selected"] {{
    background-color: {PRIMARY_DEEP};
}}
QLabel[optioncard_label="true"] {{
    font-size: 13px;
    font-weight: 600;
}}
QLabel[optioncard_subtitle="true"] {{
    font-size: 11px;
    color: {TEXT_MUTED};
}}

QFrame[sourcecard="true"] {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame[sourcecard="true"]:hover {{
    border-color: {TEXT_MUTED};
}}
QFrame[sourcecard="configured"] {{
    border: 1.5px solid {SUCCESS};
}}
QFrame[sourcecard="true"]:disabled, QFrame[sourcecard="configured"]:disabled {{
    border-color: {BORDER};
}}
QLabel[sourcecard_title="true"] {{
    font-size: 14px;
    font-weight: 600;
}}
QLabel[sourcecard_subtitle="true"] {{
    font-size: 11px;
    color: {TEXT_MUTED};
}}

QFrame[iconrow="true"] {{
    background-color: transparent;
    border-radius: 9px;
}}
QFrame[iconrow="true"]:hover {{
    background-color: {ROW_HOVER_BG};
}}
QFrame[iconrow="true"][primary="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PRIMARY_DEEP}, stop:1 {PRIMARY});
}}
QFrame[iconrow="true"][primary="true"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PRIMARY_DEEP}, stop:1 {PRIMARY_HOVER});
}}

QWidget[iconbadge="true"] {{
    background-color: {ICON_BADGE_BG};
    border-radius: 10px;
}}
QFrame[iconrow="true"][primary="true"] QWidget[iconbadge="true"] {{
    background-color: rgba(255, 255, 255, 0.18);
}}

QLabel[iconrow_label="true"] {{
    font-size: 13px;
    font-weight: 500;
}}
QFrame[iconrow="true"][primary="true"] QLabel[iconrow_label="true"] {{
    color: white;
    font-weight: 600;
}}

QLabel[iconrow_subtitle="true"] {{
    font-size: 11px;
    color: {TEXT_MUTED};
}}
QFrame[iconrow="true"][primary="true"] QLabel[iconrow_subtitle="true"] {{
    color: rgba(255, 255, 255, 0.75);
}}

QLabel[montheyebrow="true"] {{
    color: {TEXT_MUTED};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 9px 14px 4px;
}}

QFrame[weekrow="true"] {{
    background-color: transparent;
}}
QFrame[weekrow="true"]:hover {{
    background-color: {ROW_HOVER_BG};
}}
QFrame[weekrow="true"][recommended="true"] {{
    background-color: {ICON_BADGE_BG};
    border-left: 3px solid {PRIMARY};
}}

QLabel[weekrow_label="true"] {{
    font-size: 13px;
}}
QLabel[weekrow_tag="true"] {{
    background-color: {PRIMARY_DEEP};
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
}}
QLabel[weekrow_badge="true"] {{
    background-color: {HEADER_BG};
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
}}

QWidget[summarybar="true"] {{
    background-color: {HEADER_BG};
    border-radius: 8px;
}}
QLabel[summarybar_text="true"] {{
    font-size: 12px;
}}
"""
