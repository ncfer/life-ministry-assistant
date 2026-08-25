"""Widgets reused by several of the assistant's pages."""
from __future__ import annotations

import re

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QStyle, QStyleOption, QVBoxLayout, QWidget,
)

from ..i18n import t
from .icons import svg_renderer
from .style import (
    BORDER, BUBBLE_TEXT, DISABLED_TEXT, DUPLICATE_TEXT, PRIMARY,
    PRIMARY_DISABLED_TEXT, SUCCESS, TEXT, TEXT_MUTED, WARNING_TEXT,
)

_PILL_ICON_COLOR = {"warn": WARNING_TEXT, "dup": DUPLICATE_TEXT, "ok": SUCCESS}

STEPS = [t("pasos.vmc"), t("pasos.semana"), t("pasos.revisar"), t("pasos.vista_previa"), t("pasos.confirmar")]
REMINDER_STEPS = [t("pasos.vmc"), t("pasos.semana"), t("pasos.revisar"), t("pasos.confirmar")]


class StepHeader(QWidget):
    """Page title + thin "Step X of N" progress bar."""

    def __init__(self, title: str, current_step: int, parent=None, steps: list[str] | None = None):
        super().__init__(parent)
        steps = steps or STEPS
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        step_label = QLabel(t("widgets.paso_de", actual=current_step, total=len(steps), nombre=steps[current_step - 1].upper()))
        step_label.setProperty("subtitle", True)
        layout.addWidget(step_label)

        bar = QHBoxLayout()
        bar.setSpacing(4)
        for i in range(1, len(steps) + 1):
            segment = QWidget()
            segment.setFixedHeight(3)
            color = PRIMARY if i <= current_step else BORDER
            segment.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            bar.addWidget(segment)
        layout.addLayout(bar)

        title_label = QLabel(title)
        title_label.setProperty("title", True)
        layout.addWidget(title_label)


class IconBadge(QWidget):
    """Paints an SVG icon centered in itself, re-rasterized on every
    paint via the QPainter Qt hands to paintEvent() — which is always
    already tied to the real target's actual device pixel ratio. See
    icons.svg_renderer()'s docstring for why this replaced baking the
    icon into a fixed-size QPixmap ahead of time (that approach can't
    know the real screen's DPR in advance, and got the icon clipped or
    undersized when its guess was wrong)."""

    def __init__(self, icon_name: str, color: str, icon_size: int = 22, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("iconbadge", True)
        self._icon_name = icon_name
        self._renderer = svg_renderer(icon_name, color)
        self._icon_size = icon_size

    def set_color(self, color: str) -> None:
        self._renderer = svg_renderer(self._icon_name, color)
        self.update()

    def paintEvent(self, event) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        x = (self.width() - self._icon_size) / 2
        y = (self.height() - self._icon_size) / 2
        self._renderer.render(painter, QRectF(x, y, self._icon_size, self._icon_size))


class IconRow(QFrame):
    """A clickable row: colored icon badge on the left, label, and a
    chevron on the right — used instead of a plain QPushButton wherever a
    list of named actions benefits from an icon (Home screen, and
    wherever else adopts the same style). `primary` fills the row with
    the accent color for the one action per group that matters most."""

    clicked = pyqtSignal()

    def __init__(
        self, icon_name: str, text: str, subtitle: str | None = None,
        primary: bool = False, parent=None,
    ):
        super().__init__(parent)
        self.setProperty("iconrow", True)
        self.setProperty("primary", primary)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 14, 9)
        layout.setSpacing(12)

        badge_color = "#ffffff" if primary else PRIMARY
        badge = IconBadge(icon_name, badge_color, icon_size=18)
        badge.setFixedSize(36, 36)
        layout.addWidget(badge)

        if subtitle:
            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(1)
            label = QLabel(text)
            label.setProperty("iconrow_label", True)
            text_col.addWidget(label)
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setProperty("iconrow_subtitle", True)
            text_col.addWidget(self.subtitle_label)
            layout.addLayout(text_col)
        else:
            self.subtitle_label = None
            label = QLabel(text)
            label.setProperty("iconrow_label", True)
            layout.addWidget(label)
        layout.addStretch()

        chevron_color = "#ffffff" if primary else TEXT_MUTED
        layout.addWidget(InlineIcon("chevron-right", chevron_color, icon_size=15))

    def set_subtitle(self, subtitle: str) -> None:
        if self.subtitle_label is not None:
            self.subtitle_label.setText(subtitle)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


class InlineIcon(QWidget):
    """A small SVG icon with no background/badge — for sitting directly
    next to a line of text (e.g. in a summary bar), unlike IconBadge
    which always paints its own rounded background square."""

    def __init__(self, icon_name: str, color: str, icon_size: int = 14, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._renderer = svg_renderer(icon_name, color)
        self._icon_size = icon_size
        self.setFixedSize(icon_size, icon_size)

    def set_color(self, color: str) -> None:
        self._renderer = svg_renderer(self._icon_name, color)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._renderer.render(painter, QRectF(0, 0, self._icon_size, self._icon_size))


class IconLabel(QWidget):
    """A small icon + text pair, inline — used in the week picker's
    summary bar ("✓ N weeks selected", people-icon "M assignments")."""

    def __init__(self, icon_name: str, color: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        layout.addWidget(InlineIcon(icon_name, color, icon_size=14))
        self.label = QLabel()
        self.label.setProperty("summarybar_text", True)
        layout.addWidget(self.label)

    def setText(self, text: str) -> None:
        self.label.setText(text)


class MonthEyebrow(QLabel):
    """Small caps section label grouping a run of weeks by calendar
    month — see week_picker.py."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("montheyebrow", True)


class WeekRow(QFrame):
    """A checkable row for the week picker: checkbox, date, an optional
    small pill tag (e.g. "next month"), and an assignment-count badge on
    the right. Clicking anywhere on the row toggles the checkbox, not
    just its small native hitbox — `toggled` fires either way, so a
    summary elsewhere can stay in sync live."""

    toggled = pyqtSignal()

    def __init__(
        self, date_text: str, count_text: str, tag_text: str | None = None,
        recommended: bool = False, warning_text: str | None = None,
        warning_tooltip: str | None = None, exclusive: bool = False, parent=None,
    ):
        super().__init__(parent)
        self.setProperty("weekrow", True)
        self.setProperty("recommended", recommended)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # In a single-select (radio-like) list, clicking the row that's
        # ALREADY selected must stay selected, not toggle off — Qt's own
        # exclusive-QButtonGroup logic only guarantees "checking one
        # unchecks the others", it doesn't stop this checkbox from being
        # unchecked by a raw .toggle() call, which is what a body click
        # normally does (see mousePressEvent below).
        self._exclusive = exclusive

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(11)

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(lambda _: self.toggled.emit())
        layout.addWidget(self.checkbox)

        label = QLabel(date_text)
        label.setProperty("weekrow_label", True)
        layout.addWidget(label)

        if tag_text:
            tag = QLabel(tag_text)
            tag.setProperty("weekrow_tag", True)
            layout.addWidget(tag)

        if warning_text:
            warning_pill = Pill(warning_text, "warn", icon_name="triangle-alert")
            if warning_tooltip:
                warning_pill.setToolTip(warning_tooltip)
            layout.addWidget(warning_pill)

        layout.addStretch()

        badge = QLabel(count_text)
        badge.setProperty("weekrow_badge", True)
        layout.addWidget(badge)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, value: bool) -> None:
        self.checkbox.setChecked(value)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self.checkbox.geometry().contains(event.pos()):
            if self._exclusive:
                self.checkbox.setChecked(True)
            else:
                self.checkbox.toggle()
        super().mousePressEvent(event)


class Pill(QWidget):
    """A small rounded status badge — `kind` is "warn", "dup" or "ok" (see
    style.py for the matching QSS/colors). Used in the review table's
    Estado column instead of tinting a whole cell's background, so the
    editable Name/Helper/Phone cells stay visually calm even when a row
    has a warning. `icon_name` is optional — a leading icon plus a short
    label (e.g. "OK", "Sin tel.") reads faster than text alone."""

    def __init__(self, text: str, kind: str, icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("pill", kind)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 7, 1)
        layout.setSpacing(3)
        if icon_name:
            layout.addWidget(InlineIcon(icon_name, _PILL_ICON_COLOR[kind], icon_size=11))
        label = QLabel(text)
        label.setProperty("pill_text", True)
        layout.addWidget(label)


class StatusDot(QWidget):
    """A small circular icon badge with no text — `kind` is "warn" or
    "ok" (reuses Pill's color tokens). Used in the sending-progress log
    instead of a plain "✓"/"✗" text prefix on each row."""

    def __init__(self, icon_name: str, kind: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("statusdot", kind)
        self.setFixedSize(20, 20)
        self._renderer = svg_renderer(icon_name, _PILL_ICON_COLOR[kind])

    def paintEvent(self, event) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 12
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        self._renderer.render(painter, QRectF(x, y, size, size))


class WarningBanner(QWidget):
    """Icon + word-wrapped text box for a page-level warning — replaces a
    plain QLabel[warning="true"] where the message can get long enough to
    wrap (an un-wrapped QLabel just overflows/clips instead of wrapping
    cleanly inside the box)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("warningbanner", True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(9)
        icon = InlineIcon("triangle-alert", WARNING_TEXT, icon_size=15)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setProperty("warningbanner_text", True)
        layout.addWidget(self.label, 1)

    def setText(self, text: str) -> None:
        self.label.setText(text)


def _break_long_tokens(text: str, max_len: int = 40) -> str:
    """QLabel's word-wrap only breaks at whitespace — a Google Calendar
    link (one long token, no spaces) just overflows past the bubble's
    edge instead of wrapping. Inserting a zero-width space (invisible,
    doesn't change what's copied/read) every `max_len` characters inside
    any very long token gives Qt real places to break the line."""
    def _break(match: re.Match) -> str:
        word = match.group(0)
        return "​".join(word[i:i + max_len] for i in range(0, len(word), max_len))
    return re.sub(rf"\S{{{max_len + 1},}}", _break, text)


class MessageBubble(QWidget):
    """A WhatsApp-style outgoing bubble (attachment chip + message text)
    standing in for a plain QTextEdit — it's a preview of a real
    WhatsApp message, so it reads clearer looking like one. Shared by
    send_confirm.py and reminder_confirm.py."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("bubblewrap", True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)

        row = QHBoxLayout()
        row.addStretch()

        bubble = QWidget()
        bubble.setProperty("bubble", True)
        bubble.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bubble.setMaximumWidth(420)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(5)

        self.attach = QWidget()
        self.attach.setProperty("bubble_attach", True)
        self.attach.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        attach_layout = QHBoxLayout(self.attach)
        attach_layout.setContentsMargins(6, 3, 8, 3)
        attach_layout.setSpacing(5)
        attach_layout.addWidget(InlineIcon("paperclip", BUBBLE_TEXT, icon_size=11))
        self.attach_label = QLabel()
        self.attach_label.setProperty("bubble_attach_text", True)
        attach_layout.addWidget(self.attach_label)
        attach_layout.addStretch()
        bubble_layout.addWidget(self.attach)

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        # A long unbroken token (the Google Calendar link has no spaces)
        # doesn't get forced to wrap just because an ANCESTOR widget has
        # a maximumWidth — the label needs its own, or its sizeHint just
        # overflows the bubble's rounded box instead of wrapping inside it.
        self.text_label.setMaximumWidth(390)
        self.text_label.setProperty("bubble_text", True)
        bubble_layout.addWidget(self.text_label)

        row.addWidget(bubble)
        outer.addLayout(row)

    def set_content(self, attachment_name: str, text: str) -> None:
        self.attach.setVisible(bool(attachment_name))
        self.attach_label.setText(attachment_name)
        self.text_label.setText(_break_long_tokens(text))


class Card(QFrame):
    """A `QFrame[card="true"]` (see style.py) — a bordered surface used
    anywhere content (a list, a table, a form) should read as sitting on
    its own card rather than directly on the page background, same
    visual language as Home's section cards.

    An earlier version also attached a QGraphicsDropShadowEffect for a
    soft elevation look — QSS alone can't do box-shadow. Removed: that
    combination (QGraphicsDropShadowEffect + a QSS border-radius) is a
    known-fragile one in Qt — the effect's own rasterization doesn't
    reliably follow the stylesheet's rounding, and left a small dark
    wedge poking out of the top-right corner on the user's real screen
    (never showed up in this dev environment's offscreen renders). A
    flat bordered card is worth more than a shadow that can silently
    glitch like that."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("card", True)


# A small fixed palette, not the app's own accent colors — picked so
# initials stay legible in white text and don't clash with the
# pill/warning colors used elsewhere for STATUS (these are purely
# decorative, one per person, not meaningful).
_AVATAR_COLORS = ["#0e6ba8", "#1f9254", "#8a6a1f", "#6a4c93", "#c4562a", "#146c72", "#a83e6c"]


class Avatar(QWidget):
    """A small rounded-square badge with a person's initials,
    live-painted (no pre-baked QPixmap, same reasoning as IconBadge) —
    the fill color is picked deterministically from the name so the
    same person always gets the same color across a session, without
    needing to store one. Square rather than circular on purpose: a
    circle drawn flush against its own widget bounds reads as clipped
    at the edges (the antialiased curve touches the exact boundary),
    where a rounded square with a small inset margin doesn't have that
    problem."""

    def __init__(self, name: str, size: int = 26, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self.set_name(name)

    def set_name(self, name: str) -> None:
        parts = name.split()
        self._initials = "".join(p[0] for p in parts[:2]).upper() if parts else "?"
        color_index = sum(ord(c) for c in name) % len(_AVATAR_COLORS) if name else 0
        self._color = QColor(_AVATAR_COLORS[color_index])
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        inset = max(1.0, self._size * 0.06)
        rect = QRectF(inset, inset, self._size - 2 * inset, self._size - 2 * inset)
        painter.drawRoundedRect(rect, self._size * 0.28, self._size * 0.28)
        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(max(9, int(self._size * 0.36)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._initials)


class _ClickableFrame(QFrame):
    """A QFrame whose whole area emits `clicked` on a left click — plain
    instance-level `widget.mousePressEvent = lambda: ...` assignment
    doesn't reliably hook into Qt's C++ virtual dispatch, so this
    overrides it the same way every other clickable row in this module
    does (WeekRow, IconRow, CalendarChoiceRow)."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class IconButton(_ClickableFrame):
    """A small icon-only clickable button, live-painted (see
    icons.svg_renderer for why) — used for compact toolbar actions like
    "add"/"delete" instead of a full QPushButton with text, where a
    dedicated icon reads faster than a word."""

    def __init__(self, icon_name: str, color: str = TEXT_MUTED, size: int = 30, icon_size: int = 15, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("iconbutton", True)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._renderer = svg_renderer(icon_name, color)
        self._icon_size = icon_size

    def paintEvent(self, event) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        x = (self.width() - self._icon_size) / 2
        y = (self.height() - self._icon_size) / 2
        self._renderer.render(painter, QRectF(x, y, self._icon_size, self._icon_size))


class NavButton(_ClickableFrame):
    """A wizard "back"/"next" button — a real chevron icon (left or
    right) next to the label, instead of a "←"/"→" character baked into
    the button text (read thin and blurry compared to the app's other
    live-painted icons). `primary=True` gives it the same accent look as
    the app's primary QPushButtons ("Siguiente", "Continuar", etc.);
    plain "Atrás" buttons stay neutral. `icon_name` overrides the
    chevron with an arbitrary leading icon (e.g. "wand-sparkles" for
    "Probar conmigo") for non-navigation actions that still want this
    button's look. Reimplements QPushButton's hover/disabled states by
    hand (QSS on `navbutton`/`primary` properties, see style.py) since a
    composed icon+label frame can't reuse QPushButton's own painting."""

    def __init__(
        self, text: str, direction: str = "next", primary: bool = False,
        icon_name: str | None = None, parent=None,
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._primary = primary
        self.setProperty("navbutton", "primary" if primary else "plain")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        if primary:
            layout.setContentsMargins(16, 9, 16, 9)
        else:
            layout.setContentsMargins(13, 6, 13, 6)
        layout.setSpacing(6)

        # An explicit icon_name (e.g. "wand-sparkles" for "Probar
        # conmigo") always sits left-of-text, like a "back" chevron —
        # only the direction-driven chevron alternates sides, since
        # that's what signals navigation flow.
        if icon_name is None:
            icon_name = "chevron-left" if direction == "back" else "chevron-right"
        else:
            direction = "back"
        self._icon = InlineIcon(icon_name, self._icon_color(), icon_size=15)
        self._label = QLabel(text)
        self._label.setProperty("navbutton_text", True)
        # Color set directly here (not via the QSS descendant selector
        # `QFrame[navbutton="primary"] QLabel[...]`) because that
        # compound cross-widget selector proved unreliable in practice —
        # on the user's real screen it kept resolving to the :disabled
        # color even on an enabled, non-hovered button. Same class of
        # QSS-cascade fragility as the navbutton background bug earlier
        # this session; same fix, do it in Python instead.
        self._apply_label_color()

        if direction == "back":
            layout.addWidget(self._icon)
            layout.addWidget(self._label)
        else:
            layout.addWidget(self._label)
            layout.addWidget(self._icon)

    def _icon_color(self) -> str:
        if not self.isEnabled():
            return PRIMARY_DISABLED_TEXT if self._primary else DISABLED_TEXT
        return "#ffffff" if self._primary else TEXT_MUTED

    def _label_color(self) -> str:
        if not self.isEnabled():
            return PRIMARY_DISABLED_TEXT if self._primary else DISABLED_TEXT
        return "#ffffff" if self._primary else TEXT

    def _apply_label_color(self) -> None:
        self._label.setStyleSheet(f"color: {self._label_color()}; font-size: 13px;")

    def paintEvent(self, event) -> None:
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self._icon.set_color(self._icon_color())
        self._apply_label_color()
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if not self.isEnabled():
            return
        super().mousePressEvent(event)


def _soft_shadow(x_offset: float = 0, y_offset: float = 3, blur: float = 18, alpha: int = 40) -> QGraphicsDropShadowEffect:
    """A shared shadow recipe for the app's few STATIC cards (never
    resized/regenerated after creation — OptionCard, SourceCard). Card
    itself deliberately does NOT use this: an earlier attempt combining
    QGraphicsDropShadowEffect with a rounded QSS border on Card (which
    backs dynamic, frequently-resized lists like WeekRow) left a small
    dark wedge poking out of a corner on the user's real screen, not
    reproducible offscreen. A handful of fixed, never-resized tiles is a
    much narrower/safer surface for the same effect — but if the wedge
    ever reappears here too, revert to Card's flat two-tone-border look
    instead of chasing this further."""
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    effect.setOffset(x_offset, y_offset)
    effect.setColor(QColor(20, 30, 40, alpha))
    return effect


class _CheckMark(QWidget):
    """Circular selection indicator for OptionCard — an empty ring when
    unselected, filled with a check icon when selected. A plain
    QRadioButton's indicator can't be restyled this richly without a
    pre-baked QIcon/QPixmap, so this hand-paints both states instead."""

    def __init__(self, size: int = 22, parent=None):
        super().__init__(parent)
        self._size = size
        self._checked = False
        self._check_renderer = svg_renderer("check", "#ffffff")
        self.setFixedSize(size, size)

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1, 1, self._size - 2, self._size - 2)
        if self._checked:
            painter.setBrush(QColor(PRIMARY))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            icon_size = self._size * 0.5
            x = (self._size - icon_size) / 2
            y = (self._size - icon_size) / 2
            self._check_renderer.render(painter, QRectF(x, y, icon_size, icon_size))
        else:
            pen = painter.pen()
            pen.setColor(QColor(BORDER))
            pen.setWidthF(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)


class OptionCard(_ClickableFrame):
    """A selectable option tile — icon badge, label, optional subtitle,
    and a check-circle marker that fills in when selected. Used for a
    small set of mutually-exclusive choices (e.g. send_confirm's
    calendar-format picker) instead of a QRadioButton, which can't carry
    a leading icon without a pre-baked QIcon/QPixmap. Exclusivity across
    a group is the caller's job (same division of responsibility as
    WeekRow's `exclusive` pattern) — this widget only knows its own
    selected/unselected look and emits `clicked` (inherited from
    `_ClickableFrame`) on press."""

    def __init__(self, icon_name: str, text: str, subtitle: str | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("optioncard", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setGraphicsEffect(_soft_shadow())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(12)

        self._badge = IconBadge(icon_name, PRIMARY, icon_size=17)
        self._badge.setFixedSize(34, 34)
        self._badge.setProperty("optioncard_badge", "true")
        layout.addWidget(self._badge)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        label = QLabel(text)
        label.setProperty("optioncard_label", True)
        text_col.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("optioncard_subtitle", True)
            text_col.addWidget(sub)
        layout.addLayout(text_col)
        layout.addStretch()

        self._mark = _CheckMark()
        layout.addWidget(self._mark)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("optioncard", "selected" if selected else "true")
        self._badge.setProperty("optioncard_badge", "selected" if selected else "true")
        self._badge.set_color("#ffffff" if selected else PRIMARY)
        self._mark.set_checked(selected)
        for w in (self, self._badge):
            w.style().unpolish(w)
            w.style().polish(w)

    def isSelected(self) -> bool:
        return self.property("optioncard") == "selected"


class SourceCard(_ClickableFrame):
    """One VMC-source choice (archivo local / Padlet / Google Drive) as
    its own tile instead of a row in a shared list — a big icon, title,
    subtitle, and an optional "configured" pill. `accent` is purely
    decorative (like Avatar's fixed palette), not semantic, so each
    source reads distinctly at a glance."""

    def __init__(self, icon_name: str, title: str, subtitle: str, accent: str = PRIMARY, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("sourcecard", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setGraphicsEffect(_soft_shadow(y_offset=4, blur=22))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(3)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        c = QColor(accent)
        badge = IconBadge(icon_name, accent, icon_size=22)
        badge.setFixedSize(48, 48)
        badge.setStyleSheet(
            f"background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 0.15); border-radius: 13px;"
        )
        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_row.addWidget(badge)
        badge_row.addStretch()
        layout.addLayout(badge_row)
        layout.addSpacing(8)

        title_label = QLabel(title)
        title_label.setProperty("sourcecard_title", True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("sourcecard_subtitle", True)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.subtitle_label)

        self._status_row = QHBoxLayout()
        self._status_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(self._status_row)
        self._pill: Pill | None = None

    def set_subtitle(self, subtitle: str) -> None:
        self.subtitle_label.setText(subtitle)

    def set_configured(self, configured: bool) -> None:
        self.setProperty("sourcecard", "configured" if configured else "true")
        self.style().unpolish(self)
        self.style().polish(self)
        if self._pill is not None:
            self._status_row.removeWidget(self._pill)
            self._pill.deleteLater()
            self._pill = None
        if configured:
            self._pill = Pill(t("workbook_picker.listo"), "ok", icon_name="check")
            self._status_row.addWidget(self._pill)


class _FramelessLineEdit(QLineEdit):
    """A QLineEdit that reports its own focus in/out — used only by
    SearchField, which needs to mirror that state onto its OWN border
    (the QLineEdit here has no frame of its own, see below), something
    plain QSS `:focus` can't express across two separate widgets."""

    focused = pyqtSignal(bool)

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.focused.emit(True)

    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.focused.emit(False)


class SearchField(QFrame):
    """A search box with a leading magnifying-glass icon baked into its
    own bordered box. QLineEdit has a built-in `addAction()` slot for
    exactly this, but it takes a QIcon — and this codebase deliberately
    stopped pre-baking icons into QIcon/QPixmap after two real HiDPI bugs
    (see icons.svg_renderer's docstring: fine in offscreen dev renders,
    clipped/misaligned on the user's real screen). Composing a
    live-painted InlineIcon next to a frameless QLineEdit sidesteps that
    while still reading as one seamless field."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("searchfield", "true")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 0, 9, 0)
        layout.setSpacing(7)
        layout.addWidget(InlineIcon("search", TEXT_MUTED, icon_size=15))

        self.line_edit = _FramelessLineEdit()
        self.line_edit.setFrame(False)
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setProperty("searchfield_input", True)
        self.line_edit.focused.connect(self._on_focus_change)
        layout.addWidget(self.line_edit)

        self.textChanged = self.line_edit.textChanged

    def _on_focus_change(self, focused: bool) -> None:
        self.setProperty("searchfield", "focused" if focused else "true")
        self.style().unpolish(self)
        self.style().polish(self)

    def setPlaceholderText(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    def text(self) -> str:
        return self.line_edit.text()


class CollapsibleSection(QFrame):
    """An expand/collapse group for a settings dialog — icon badge +
    title + chevron header (click anywhere on it to toggle), body shown
    only while expanded. Used to break a long flat settings form into
    named groups the user opens on demand, iOS-Settings style.

    `accent` gives each section its own color (icon + a left border
    stripe) instead of every section looking identical in plain
    PRIMARY blue — purely decorative grouping color, not a semantic
    one, same spirit as Avatar's fixed palette."""

    def __init__(self, icon_name: str, title: str, expanded: bool = False, accent: str = PRIMARY, parent=None):
        super().__init__(parent)
        self.setProperty("card", True)
        self._expanded = expanded
        c = QColor(accent)
        # A selector-less setStyleSheet() on a widget cascades to ALL its
        # descendants matching the property, not just the widget itself —
        # without an object-name-scoped selector this painted every
        # QLineEdit/QPushButton inside the section with the same colored
        # left border. #objectName scopes it to exactly this one frame.
        self.setObjectName(f"collapsible_{id(self)}")
        self.setStyleSheet(f"QFrame#{self.objectName()} {{ border-left: 3px solid {accent}; }}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = _ClickableFrame()
        self.header.setProperty("collapsible_header", True)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.clicked.connect(self.toggle)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 11, 14, 11)
        header_layout.setSpacing(10)

        badge = IconBadge(icon_name, accent, icon_size=15)
        badge.setFixedSize(26, 26)
        badge.setStyleSheet(f"background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 0.16); border-radius: 8px;")
        header_layout.addWidget(badge)

        title_label = QLabel(title)
        title_label.setProperty("iconrow_label", True)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._chevron = InlineIcon("chevron-down", TEXT_MUTED, icon_size=13)
        header_layout.addWidget(self._chevron)
        outer.addWidget(self.header)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(14, 4, 14, 14)
        self.body_layout.setSpacing(10)
        self.body.setVisible(self._expanded)
        outer.addWidget(self.body)

        self._update_chevron()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self.body.setVisible(self._expanded)
        self._update_chevron()

    def _update_chevron(self) -> None:
        # A plain rotation transform would need re-rendering the SVG at
        # an angle; simplest correct fix is just flipping which way the
        # chevron points, reusing the same live-painted icon either way.
        self._chevron._renderer = svg_renderer(
            "chevron-down" if self._expanded else "chevron-right", TEXT_MUTED,
        )
        self._chevron.update()
