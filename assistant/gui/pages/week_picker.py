from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QScrollArea, QVBoxLayout,
    QWidget,
)

from ...dates import date_with_weekday, month_name, next_month
from ...i18n import t
from ..style import PRIMARY, TEXT_MUTED
from ..widgets import Card, IconLabel, MonthEyebrow, NavButton, StepHeader, WeekRow


class WeekPickerPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._rows: list[tuple[date, WeekRow]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(12)

        layout.addWidget(StepHeader(t("week_picker.titulo"), 2))

        help_label = QLabel(t("week_picker.ayuda"))
        help_label.setProperty("help", True)
        layout.addWidget(help_label)

        quick_select = QHBoxLayout()
        next_month_button = NavButton(t("week_picker.mes_siguiente"), icon_name="calendar")
        next_month_button.clicked.connect(self._select_next_month)
        quick_select.addWidget(next_month_button)
        quick_select.addStretch()
        layout.addLayout(quick_select)

        # Grouped rows aren't a native scrollable widget like the old
        # QListWidget was — a QScrollArea keeps that same "just scrolls
        # when there are more weeks than fit" behavior (up to 16 weeks in
        # real production, when the Padlet has two bimesters merged).
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.card = Card()
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(4, 6, 4, 6)
        self.card_layout.setSpacing(0)
        # Kept last always (see enter()) so leftover vertical space goes
        # here instead of QVBoxLayout stretching the rows themselves
        # tall when there are few of them — latent with a short week
        # list (e.g. right after downloading a single bimester), masked
        # in earlier testing by always having enough weeks to fill the
        # visible area.
        self.card_layout.addStretch()
        self.scroll.setWidget(self.card)
        layout.addWidget(self.scroll)

        self.summary_bar = self._build_summary_bar()
        layout.addWidget(self.summary_bar)

        buttons = QHBoxLayout()
        back_button = NavButton(t("comun.atras"), direction="back")
        back_button.clicked.connect(lambda: self.main_window.go_to(1))
        buttons.addWidget(back_button)
        buttons.addStretch()
        next_button = NavButton(t("comun.siguiente"), direction="next", primary=True)
        next_button.clicked.connect(self._next)
        buttons.addWidget(next_button)
        layout.addLayout(buttons)

    def _build_summary_bar(self) -> QWidget:
        bar = QWidget()
        bar.setProperty("summarybar", True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 10, 14, 10)

        self.summary_weeks_label = IconLabel("check", PRIMARY)
        h.addWidget(self.summary_weeks_label)
        h.addStretch()
        self.summary_assignments_label = IconLabel("users", TEXT_MUTED)
        h.addWidget(self.summary_assignments_label)

        return bar

    def enter(self) -> None:
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.card_layout.addStretch()
        self._rows = []

        target_month = next_month(date.today())
        weeks = self.main_window.state.weeks
        current_month_key = None

        for fecha in sorted(weeks):
            last = self.card_layout.count() - 1  # index of the trailing stretch
            month_key = (fecha.year, fecha.month)
            if month_key != current_month_key:
                current_month_key = month_key
                self.card_layout.insertWidget(last, MonthEyebrow(f"{month_name(fecha.month).upper()} {fecha.year}"))
                last += 1

            assignments = weeks[fecha]
            date_text = date_with_weekday(fecha)
            date_text = date_text[0].upper() + date_text[1:]
            count_text = t("week_picker.n_asignaciones", n=len(assignments))
            recommended = month_key == target_month
            tag_text = t("week_picker.mes_siguiente_tag") if recommended else None

            row = WeekRow(date_text, count_text, tag_text=tag_text, recommended=recommended)
            row.toggled.connect(self._update_summary)
            self.card_layout.insertWidget(last, row)
            self._rows.append((fecha, row))

        # Default to next month's weeks already checked — the common case
        # (generating slips ahead of time for the upcoming month) needs no
        # clicking; the button above re-applies this if the person has
        # since unchecked something.
        self._select_next_month()

    def _select_next_month(self) -> None:
        target = next_month(date.today())
        for fecha, row in self._rows:
            row.set_checked((fecha.year, fecha.month) == target)
        self._update_summary()

    def _update_summary(self) -> None:
        weeks = self.main_window.state.weeks
        selected = [fecha for fecha, row in self._rows if row.is_checked()]
        total_assignments = sum(len(weeks[fecha]) for fecha in selected)
        self.summary_weeks_label.setText(t("week_picker.resumen_semanas", n=len(selected)))
        self.summary_assignments_label.setText(t("week_picker.resumen_asignaciones", n=total_assignments))

    def _next(self) -> None:
        selected = [fecha for fecha, row in self._rows if row.is_checked()]

        if not selected:
            QMessageBox.warning(self, t("week_picker.ninguna_titulo"), t("week_picker.ninguna_msg"))
            return

        self.main_window.state.selected_dates = selected
        assignments = []
        for fecha in sorted(selected):
            assignments.extend(self.main_window.state.weeks[fecha])
        self.main_window.state.assignments = assignments
        self.main_window.go_to(3)  # -> review assignments
