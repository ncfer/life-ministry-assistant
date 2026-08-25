from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from .. import i18n
from ..config import load_config, persist_config
from .dialogs.contacts_editor import ContactsEditorDialog
from .dialogs.general_settings import GeneralSettingsDialog
from .dialogs.history_dialog import HistoryDialog
from .dialogs.message_editor import REMINDER_HELP_TEXT, REMINDER_PLACEHOLDERS, MessageEditorDialog
from .dialogs.timing_settings import TimingSettingsDialog
from .pages.home import HomePage
from .pages.preview import PreviewPage
from .pages.reminder_confirm import ReminderConfirmPage
from .pages.reminder_sending import ReminderSendingPage
from .pages.reminder_review import ReminderReviewPage
from .pages.reminder_week_picker import ReminderWeekPickerPage
from .pages.reminder_workbook_picker import ReminderWorkbookPickerPage
from .pages.review_assignments import ReviewAssignmentsPage
from .pages.send_confirm import SendConfirmPage
from .pages.sending_progress import SendingProgressPage
from .pages.workbook_picker import WorkbookPickerPage
from .pages.week_picker import WeekPickerPage
from .state import ReminderState, WizardState

IDX_HOME, IDX_WORKBOOK, IDX_WEEK, IDX_REVIEW, IDX_PREVIEW, IDX_CONFIRM, IDX_SENDING = range(7)
IDX_REMINDER_WORKBOOK, IDX_REMINDER_WEEK, IDX_REMINDER_REVIEW, IDX_REMINDER_CONFIRM, IDX_REMINDER_SENDING = range(7, 12)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t("app.titulo"))
        self.resize(1060, 780)
        # With less height than the home screen's sizeHint asks for, Qt
        # compresses the layout instead of resizing the window (there's no
        # QScrollArea) — the cut comes out of the bottom card's own
        # padding, leaving it flush against the window edge with no
        # visible margin, or a row without room to draw a full icon badge.
        # 640 was enough for the old plain-text-button home screen; the
        # icon-row redesign (see widgets.IconRow) needs taller rows, so
        # this had to grow with it — if home.py's layout changes again,
        # re-check this is still tall enough.
        # Width grew 860→960→1060 as review_assignments.py's table got an
        # Estado column (pills) on top of the existing 8, and the Teléfono
        # column started showing full "Usar {nombre sugerido}" buttons
        # instead of a shortened label (explicit user request — the
        # suggested contact's name needs to actually be readable there).
        # At narrower widths that column alone pushed the table into a
        # horizontal scrollbar by default.
        self.setMinimumSize(800, 780)

        self.config = load_config()
        self.state = WizardState()
        self.reminder_state = ReminderState()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_page = HomePage(self)
        self.workbook_page = WorkbookPickerPage(self)
        self.week_page = WeekPickerPage(self)
        self.review_page = ReviewAssignmentsPage(self)
        self.preview_page = PreviewPage(self)
        self.confirm_page = SendConfirmPage(self)
        self.sending_page = SendingProgressPage(self)

        self.reminder_workbook_page = ReminderWorkbookPickerPage(self)
        self.reminder_week_page = ReminderWeekPickerPage(self)
        self.reminder_review_page = ReminderReviewPage(self)
        self.reminder_confirm_page = ReminderConfirmPage(self)
        self.reminder_sending_page = ReminderSendingPage(self)

        for page in (
            self.home_page, self.workbook_page, self.week_page,
            self.review_page, self.preview_page, self.confirm_page,
            self.sending_page,
            self.reminder_workbook_page, self.reminder_week_page, self.reminder_review_page,
            self.reminder_confirm_page, self.reminder_sending_page,
        ):
            self.stack.addWidget(page)

        self._check_initial_setup()
        self.go_to(IDX_HOME)

    # --- navigation ---------------------------------------------------
    def go_to(self, index: int) -> None:
        page = self.stack.widget(index)
        if hasattr(page, "enter"):
            page.enter()
        self.stack.setCurrentIndex(index)

    def new_assignment(self) -> None:
        self.state = WizardState()
        self.go_to(IDX_WORKBOOK)

    def new_reminder(self) -> None:
        self.reminder_state = ReminderState()
        self.go_to(IDX_REMINDER_WORKBOOK)

    # --- initial setup --------------------------------------------------
    def _check_initial_setup(self) -> None:
        # The language is already chosen before this point (see app.py,
        # decided BEFORE building this window and its pages — same as the
        # theme).
        if not self.config.paths.pdf_template:
            QMessageBox.information(
                self, i18n.t("config_inicial.titulo"),
                i18n.t("config_inicial.mensaje"),
            )
            self.open_general_settings()

    def save_config(self) -> None:
        persist_config(self.config)

    # --- settings dialogs -----------------------------------------------
    def open_general_settings(self) -> None:
        dialog = GeneralSettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.config
            self.save_config()

    def open_contacts_editor(self) -> None:
        dialog = ContactsEditorDialog(self.config.paths.contacts_csv, self)
        dialog.exec()

    def open_message_editor(self) -> None:
        dialog = MessageEditorDialog(self.config.paths.message_txt, self)
        dialog.exec()

    def open_reminder_message_editor(self) -> None:
        dialog = MessageEditorDialog(
            self.config.paths.reminder_message_txt, self,
            title=i18n.t("mensaje.titulo_ventana_recordatorio"), help_text=REMINDER_HELP_TEXT,
            default_template_key="mensaje.plantilla_defecto_recordatorio",
            placeholders=REMINDER_PLACEHOLDERS,
        )
        dialog.exec()

    def open_timing_settings(self) -> None:
        dialog = TimingSettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.config
            self.save_config()

    def open_history(self) -> None:
        dialog = HistoryDialog(self.config.paths.history_csv, self)
        dialog.exec()

    def open_reminder_history(self) -> None:
        dialog = HistoryDialog(self.config.paths.reminder_history_csv, self)
        dialog.setWindowTitle(i18n.t("historial.titulo_recordatorios"))
        dialog.exec()
