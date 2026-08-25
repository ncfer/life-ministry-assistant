from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QScrollArea,
    QVBoxLayout, QWidget,
)

from ...history import log_entry
from ...i18n import t
from ..style import SUCCESS, WARNING_TEXT
from ..widgets import Card, IconLabel, NavButton, StatusDot, WarningBanner
from ..workers import SendThread


class LogRow(QFrame):
    """One line of the send log: a round check/x badge, the recipient's
    name, and — only on failure — the reason, replacing the old
    QListWidget's plain "✓ Name" / "✗ Name — reason" text rows."""

    def __init__(self, name: str, ok: bool, reason: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("logrow", True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 8, 13, 8)
        layout.setSpacing(9)
        layout.addWidget(StatusDot("check" if ok else "x", "ok" if ok else "warn"))
        layout.addWidget(QLabel(name))
        if reason:
            reason_label = QLabel(reason)
            reason_label.setProperty("logrow_reason", True)
            layout.addWidget(reason_label)
        layout.addStretch()


class SendingProgressPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._thread: SendThread | None = None
        self._failed: list[tuple] = []  # (assignment, jpg, ics)
        self._ok_count = 0
        self._fail_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(10)

        title = QLabel(t("sending.titulo"))
        title.setProperty("title", True)
        layout.addWidget(title)

        self.status_label = QLabel(t("comun.abriendo_whatsapp"))
        self.status_label.setProperty("help", True)
        layout.addWidget(self.status_label)

        self.qr_banner = WarningBanner()
        self.qr_banner.hide()
        layout.addWidget(self.qr_banner)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.summary_bar = self._build_summary_bar()
        layout.addWidget(self.summary_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.log_card = Card()
        self.log_layout = QVBoxLayout(self.log_card)
        self.log_layout.setContentsMargins(4, 4, 4, 4)
        self.log_layout.setSpacing(0)
        # Kept last always (see _clear_log/_on_result) so leftover
        # vertical space goes here instead of QVBoxLayout stretching the
        # rows themselves tall when there are few of them.
        self.log_layout.addStretch()
        self.scroll.setWidget(self.log_card)
        layout.addWidget(self.scroll)

        buttons = QHBoxLayout()
        self.cancel_button = NavButton(t("comun.cancelar_envio"), icon_name="x")
        self.cancel_button.clicked.connect(self._cancel)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch()
        self.retry_button = NavButton(t("comun.reintentar_fallidos"), icon_name="rotate-ccw")
        self.retry_button.clicked.connect(self._retry)
        self.retry_button.hide()
        buttons.addWidget(self.retry_button)
        self.home_button = NavButton(t("comun.volver_inicio"), primary=True, icon_name="house")
        self.home_button.setEnabled(False)
        self.home_button.clicked.connect(lambda: self.main_window.go_to(0))
        buttons.addWidget(self.home_button)
        layout.addLayout(buttons)

    def _build_summary_bar(self) -> QWidget:
        bar = QWidget()
        bar.setProperty("summarybar", True)
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 10, 14, 10)
        self.summary_ok_label = IconLabel("check", SUCCESS)
        h.addWidget(self.summary_ok_label)
        h.addStretch()
        self.summary_fail_label = IconLabel("x", WARNING_TEXT)
        h.addWidget(self.summary_fail_label)
        return bar

    def enter(self) -> None:
        self._clear_log()
        self._failed = []
        self.qr_banner.hide()
        self.retry_button.hide()
        items = [(gi.assignment, gi.jpg, gi.ics) for gi in self.main_window.state.generated]
        self._start_sending(items)

    def _clear_log(self) -> None:
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.log_layout.addStretch()
        self._ok_count = 0
        self._fail_count = 0
        self._update_summary()

    def _update_summary(self) -> None:
        self.summary_ok_label.setText(t("sending.resumen_enviados", n=self._ok_count))
        self.summary_fail_label.setText(t("sending.resumen_fallidos", n=self._fail_count))

    def _start_sending(self, items: list[tuple]) -> None:
        self.home_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.retry_button.hide()
        self.qr_banner.hide()

        self.progress_bar.setRange(0, len(items))
        self.progress_bar.setValue(0)

        self._thread = SendThread(
            items,
            self.main_window.state.reminder_mode,
            Path(self.main_window.config.paths.message_txt),
            self.main_window.config,
        )
        self._thread.progress.connect(self._on_progress)
        self._thread.result.connect(self._on_result)
        self._thread.waiting_qr.connect(self._on_waiting_qr)
        self._thread.completed.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_waiting_qr(self) -> None:
        self.qr_banner.setText(t("comun.escanea_qr"))
        self.qr_banner.show()

    def _on_progress(self, name: str, index: int, total: int) -> None:
        self.qr_banner.hide()
        self.progress_bar.setValue(index)
        self.status_label.setText(t("comun.enviado_n", i=index, total=total))

    def _on_result(self, assignment, jpg, ics, success: bool, reason: str) -> None:
        history_csv = Path(self.main_window.config.paths.history_csv)
        log_entry(history_csv, assignment.date, assignment.name, assignment.phone, success, reason)

        last = self.log_layout.count() - 1  # index of the trailing stretch
        if success:
            self._ok_count += 1
            self.log_layout.insertWidget(last, LogRow(assignment.name, ok=True))
            self._cleanup_generated(jpg, ics)
        else:
            self._fail_count += 1
            self.log_layout.insertWidget(last, LogRow(assignment.name, ok=False, reason=t("comun.no_se_pudo_enviar")))
            self._failed.append((assignment, jpg, ics))
        self._update_summary()

        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @staticmethod
    def _cleanup_generated(jpg: Path, ics: Path) -> None:
        """Deletes the slip's PDF/JPG/ICS once it's been sent successfully
        — otherwise they'd just pile up in output/ forever, and
        history.csv already keeps the record that it was sent. Only
        called for a successful send; a failed one keeps its files
        untouched, because "Retry failed" reuses these exact paths.
        pdf/jpg/ics share the same filename stem (see GenerateThread in
        workers.py), so the pdf path is derived from jpg instead of
        threading a 4th path through every callback."""
        for path in (jpg, ics, jpg.with_suffix(".pdf")):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def _on_finished(self) -> None:
        self.qr_banner.hide()
        if self._failed:
            self.status_label.setText(t("sending.terminado_n_fallidos", n=len(self._failed)))
            self.retry_button.setText(t("comun.reintentar_fallidos_n", n=len(self._failed)))
            self.retry_button.show()
        else:
            self.status_label.setText(t("sending.terminado_bien"))
        self.cancel_button.setEnabled(False)
        self.home_button.setEnabled(True)

    def _retry(self) -> None:
        pending = self._failed
        self._failed = []
        self._clear_log()
        self._start_sending(pending)

    def _cancel(self) -> None:
        if self._thread:
            self._thread.cancel()
        self.cancel_button.setEnabled(False)
        self.qr_banner.hide()
        self.status_label.setText(t("comun.cancelando"))

    def _on_error(self, message: str) -> None:
        self.qr_banner.hide()
        self.cancel_button.setEnabled(False)
        self.home_button.setEnabled(True)
        QMessageBox.critical(self, t("comun.error_enviar_titulo"), message)
