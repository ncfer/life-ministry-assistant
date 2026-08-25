from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QMessageBox, QScrollArea,
    QVBoxLayout, QWidget,
)

from ...dates import date_with_weekday, week_start
from ...i18n import t
from ...reminder_workbook import week_warnings
from ..widgets import Card, NavButton, REMINDER_STEPS, StepHeader, WeekRow


class ReminderWeekPickerPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._rows: list[tuple[date, WeekRow]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(12)

        layout.addWidget(StepHeader(t("rec_semana.titulo"), 2, steps=REMINDER_STEPS))

        help_label = QLabel(t("rec_semana.ayuda"))
        help_label.setProperty("help", True)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        quick_select = QHBoxLayout()
        current_week_button = NavButton(t("rec_semana.semana_actual"), icon_name="calendar")
        current_week_button.clicked.connect(lambda: self._select_week(date.today()))
        quick_select.addWidget(current_week_button)
        next_week_button = NavButton(t("rec_semana.semana_siguiente"), icon_name="calendar")
        next_week_button.clicked.connect(lambda: self._select_week(date.today() + timedelta(days=7)))
        quick_select.addWidget(next_week_button)
        quick_select.addStretch()
        layout.addLayout(quick_select)

        # QButtonGroup(exclusive=True) makes this a single-select list —
        # checking one row's checkbox auto-unchecks whichever other one
        # was checked, same as a set of radio buttons. Unlike the
        # assignments week picker (week_picker.py), only one reminder
        # batch is sent at a time.
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.card = Card()
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(4, 6, 4, 6)
        self.card_layout.setSpacing(0)
        # Kept last always (see enter()) so leftover vertical space goes
        # here instead of QVBoxLayout stretching the rows themselves
        # tall when there are few of them (see the same fix in
        # week_picker.py for the full story on this bug).
        self.card_layout.addStretch()
        self.scroll.setWidget(self.card)
        layout.addWidget(self.scroll)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(7))
        buttons.addWidget(back_button)
        buttons.addStretch()
        next_button = NavButton(t("comun.siguiente"), direction="next", primary=True)
        next_button.clicked.connect(self._next)
        buttons.addWidget(next_button)
        layout.addLayout(buttons)

    def enter(self) -> None:
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for _fecha, row in self._rows:
            self.group.removeButton(row.checkbox)
        self.card_layout.addStretch()
        self._rows = []

        weeks = self.main_window.reminder_state.weeks
        for fecha in sorted(weeks):
            participants = weeks[fecha]
            date_text = date_with_weekday(fecha)
            date_text = date_text[0].upper() + date_text[1:]
            count_text = t("rec_semana.n_participantes", n=len(participants))

            warnings = week_warnings(weeks, fecha)
            row = WeekRow(
                date_text, count_text,
                warning_text=t("rec_semana.pill_incompleta") if warnings else None,
                warning_tooltip="\n".join(warnings) if warnings else None,
                exclusive=True,
            )
            self.group.addButton(row.checkbox)
            last = self.card_layout.count() - 1  # index of the trailing stretch
            self.card_layout.insertWidget(last, row)
            self._rows.append((fecha, row))

        # Default to this week's meeting if it's in the list — falls back
        # to the earliest available week otherwise (e.g. only past or only
        # future weeks in this workbook), same as before this feature.
        if not self._select_week(date.today()) and self._rows:
            self._rows[0][1].set_checked(True)

    def _select_week(self, reference_date: date) -> bool:
        """Checks the row whose meeting date falls in the same
        Monday-Sunday week as `reference_date`, if there is one. Returns
        whether a match was found (so `enter()` can fall back to the
        first row when there isn't)."""
        target = week_start(reference_date)
        for fecha, row in self._rows:
            if week_start(fecha) == target:
                row.set_checked(True)
                return True
        return False

    def _selected_date(self) -> date | None:
        for fecha, row in self._rows:
            if row.is_checked():
                return fecha
        return None

    def _next(self) -> None:
        fecha = self._selected_date()
        if fecha is None:
            QMessageBox.warning(self, t("week_picker.ninguna_titulo"), t("rec_semana.elige_msg"))
            return

        weeks = self.main_window.reminder_state.weeks
        warnings = week_warnings(weeks, fecha)
        if warnings:
            answer = QMessageBox.question(
                self, t("rec_semana.incompleta_titulo"),
                "\n".join(warnings) + "\n\n" + t("rec_semana.incompleta_continuar"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.main_window.reminder_state.selected_date = fecha
        self.main_window.reminder_state.participants = weeks[fecha]
        self.main_window.go_to(9)  # -> review recipients
