"""Background threads so the window doesn't freeze during VMC parsing,
document generation, or WhatsApp sending.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from ..config import Config, PadletConfig
from ..contacts import find_phone, load_contacts
from ..drive import DriveError, download_pdf as download_drive_pdf
from ..fill_pdf import fill_pdf
from ..gen_ics import write_ics
from ..i18n import t
from ..models import Assignment
from ..padlet import PadletError, list_pdfs_by_title
from ..parse_workbook import parse_workbook
from ..to_jpg import pdf_to_jpg
from ..reminder_workbook import Participant, parse_reminder_workbook, crop_week_jpg
from .state import GeneratedItem


def _slug_title(text: str) -> str:
    import re
    return re.sub(r'[\\/:*?"<>|]', "_", text).strip()


def _download_padlet_documents(padlet: PadletConfig, output_folder: Path) -> list[tuple[str, Path]]:
    """Downloads ALL Padlet posts that match `padlet.workbook_title` (there can
    be more than one at once — VMC for the current bimester and the next
    one published together, seen in real production) and saves them into
    `output_folder`. Returns [(title, local_path), ...]."""
    documents = list_pdfs_by_title(padlet.url, padlet.workbook_title, padlet.password or None)
    output_folder.mkdir(parents=True, exist_ok=True)
    result = []
    for title, content in documents:
        path = output_folder / f"VMC del Padlet - {_slug_title(title)}.pdf"
        path.write_bytes(content)
        result.append((title, path))
    return result


class DownloadWorkbookPadletThread(QThread):
    """Downloads ALL VMCs published on the Padlet whose title matches and
    merges every one's weeks into a single dict — so it doesn't matter if
    the board has the current bimester's VMC and the next one published at
    the same time, every available week shows up without risking picking
    the wrong document by mistake (see `_download_padlet_documents`)."""

    done = pyqtSignal(dict, object)  # dict[date, list[Assignment]], Path (first document, display only)
    error = pyqtSignal(str)

    def __init__(self, padlet: PadletConfig, output_folder: Path, parent=None):
        super().__init__(parent)
        self.padlet = padlet
        self.output_folder = output_folder

    def run(self) -> None:
        try:
            documents = _download_padlet_documents(self.padlet, self.output_folder)
        except PadletError as e:
            self.error.emit(str(e))
            return
        except OSError as e:
            self.error.emit(t("errores.no_se_pudo_guardar_pdf", error=e))
            return

        weeks: dict = {}
        try:
            for _title, path in documents:
                weeks.update(parse_workbook(path))
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc_padlet", error=e))
            return

        if not weeks:
            self.error.emit(t("errores.padlet_sin_semanas_asignaciones"))
            return
        self.done.emit(weeks, documents[0][1])


class DownloadReminderWorkbookPadletThread(QThread):
    """Same as `DownloadWorkbookPadletThread` but for VMC reminders: instead
    of a single Path, each week's source document needs to be tracked
    (`workbook_paths_by_date`), because that week's image crop has to open the
    PDF that actually contains it."""

    done = pyqtSignal(dict, dict)  # dict[date, list[Participant]], dict[date, Path]
    error = pyqtSignal(str)

    def __init__(self, padlet: PadletConfig, output_folder: Path, parent=None):
        super().__init__(parent)
        self.padlet = padlet
        self.output_folder = output_folder

    def run(self) -> None:
        try:
            documents = _download_padlet_documents(self.padlet, self.output_folder)
        except PadletError as e:
            self.error.emit(str(e))
            return
        except OSError as e:
            self.error.emit(t("errores.no_se_pudo_guardar_pdf", error=e))
            return

        weeks: dict = {}
        paths_by_date: dict = {}
        try:
            for _title, path in documents:
                partial = parse_reminder_workbook(path)
                weeks.update(partial)
                for fecha in partial:
                    paths_by_date[fecha] = path
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc_padlet", error=e))
            return

        if not weeks:
            self.error.emit(t("errores.padlet_sin_semanas_participantes"))
            return
        self.done.emit(weeks, paths_by_date)


class DownloadWorkbookDriveThread(QThread):
    """Downloads the single PDF at the configured Drive link and parses
    it — unlike Padlet there's no title-based search across several
    documents, just the one file the link points to."""

    done = pyqtSignal(dict, object)  # dict[date, list[Assignment]], Path
    error = pyqtSignal(str)

    def __init__(self, drive_link: str, output_folder: Path, parent=None):
        super().__init__(parent)
        self.drive_link = drive_link
        self.output_folder = output_folder

    def run(self) -> None:
        try:
            content = download_drive_pdf(self.drive_link)
        except DriveError as e:
            self.error.emit(str(e))
            return

        try:
            self.output_folder.mkdir(parents=True, exist_ok=True)
            path = self.output_folder / "VMC de Drive.pdf"
            path.write_bytes(content)
        except OSError as e:
            self.error.emit(t("errores.no_se_pudo_guardar_pdf", error=e))
            return

        try:
            weeks = parse_workbook(path)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc", error=e))
            return

        if not weeks:
            self.error.emit(t("errores.pdf_sin_semanas_asignaciones"))
            return
        self.done.emit(weeks, path)


class DownloadReminderWorkbookDriveThread(QThread):
    """Same as `DownloadWorkbookDriveThread` but for VMC reminders —
    parses with `parse_reminder_workbook` and reports back
    `workbook_paths_by_date` like `DownloadReminderWorkbookPadletThread`
    does, so `GenerateCropThread` knows which PDF each week came from."""

    done = pyqtSignal(dict, dict)  # dict[date, list[Participant]], dict[date, Path]
    error = pyqtSignal(str)

    def __init__(self, drive_link: str, output_folder: Path, parent=None):
        super().__init__(parent)
        self.drive_link = drive_link
        self.output_folder = output_folder

    def run(self) -> None:
        try:
            content = download_drive_pdf(self.drive_link)
        except DriveError as e:
            self.error.emit(str(e))
            return

        try:
            self.output_folder.mkdir(parents=True, exist_ok=True)
            path = self.output_folder / "VMC de Drive.pdf"
            path.write_bytes(content)
        except OSError as e:
            self.error.emit(t("errores.no_se_pudo_guardar_pdf", error=e))
            return

        try:
            weeks = parse_reminder_workbook(path)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc", error=e))
            return

        if not weeks:
            self.error.emit(t("errores.pdf_sin_semanas_participantes"))
            return
        self.done.emit(weeks, {fecha: path for fecha in weeks})


class ParseWorkbookThread(QThread):
    done = pyqtSignal(dict)   # dict[date, list[Assignment]]
    error = pyqtSignal(str)

    def __init__(self, workbook_path: Path, parent=None):
        super().__init__(parent)
        self.workbook_path = workbook_path

    def run(self) -> None:
        try:
            result = parse_workbook(self.workbook_path)
            if not result:
                self.error.emit(t("errores.pdf_sin_semanas_asignaciones"))
                return
            self.done.emit(result)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc", error=e))


class GenerateThread(QThread):
    progress = pyqtSignal(int, int, str)  # current, total, name
    done = pyqtSignal(list)               # list[GeneratedItem]
    error = pyqtSignal(str)

    def __init__(self, assignments: list[Assignment], config: Config, parent=None):
        super().__init__(parent)
        self.assignments = assignments
        self.config = config

    def run(self) -> None:
        try:
            template = Path(self.config.paths.pdf_template)
            base_folder = Path(self.config.paths.output_folder)
            result: list[GeneratedItem] = []
            total = len(self.assignments)

            for i, a in enumerate(self.assignments, start=1):
                self.progress.emit(i, total, a.name)
                folder = base_folder / a.date.strftime("%Y-%m")
                base = folder / f"{a.date.isoformat()} - {a.number} - {_slug(a.name)}"
                pdf_path = base.with_suffix(".pdf")
                jpg_path = base.with_suffix(".jpg")
                ics_path = base.with_suffix(".ics")

                fill_pdf(template, a, pdf_path)
                pdf_to_jpg(pdf_path, jpg_path)
                write_ics(a, ics_path)

                result.append(GeneratedItem(a, pdf_path, jpg_path, ics_path))

            self.done.emit(result)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudieron_generar_documentos", error=e))


class ResolvePhonesThread(QThread):
    done = pyqtSignal(list)  # list[tuple[Assignment, Match]]

    def __init__(self, assignments: list[Assignment], contacts_csv: Path, parent=None):
        super().__init__(parent)
        self.assignments = assignments
        self.contacts_csv = contacts_csv

    def run(self) -> None:
        contacts = load_contacts(self.contacts_csv)
        result = []
        for a in self.assignments:
            match = find_phone(a.name, contacts)
            updated = replace(a, phone=match.phone)
            result.append((updated, match))
        self.done.emit(result)


class SendThread(QThread):
    progress = pyqtSignal(str, int, int)  # name, index, total
    result = pyqtSignal(object, object, object, bool, str)  # assignment, jpg, ics, success, reason
    waiting_qr = pyqtSignal()
    completed = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, items, reminder_mode: str, message_txt: Path, config: Config, parent=None):
        super().__init__(parent)
        self.items = items
        self.reminder_mode = reminder_mode
        self.message_txt = message_txt
        self.config = config
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        from ..whatsapp_send import send_assignments  # late import: Playwright is heavy to load

        try:
            send_assignments(
                self.items,
                modo_recordatorio=self.reminder_mode,
                plantilla_mensaje=self.message_txt,
                tiempos=self.config.timing,
                on_progreso=lambda name, i, total: self.progress.emit(name, i, total),
                on_resultado=lambda a, jpg, ics, ok, reason: self.result.emit(a, jpg, ics, ok, reason),
                debe_cancelar=lambda: self._cancel_requested,
                on_esperando_qr=lambda: self.waiting_qr.emit(),
            )
            self.completed.emit()
        except Exception as e:
            self.error.emit(t("errores.error_enviando_mensajes", error=e))


def _slug(text: str) -> str:
    import re
    return re.sub(r'[\\/:*?"<>|]', "_", text).strip()


class ParseReminderWorkbookThread(QThread):
    done = pyqtSignal(dict)   # dict[date, list[Participant]]
    error = pyqtSignal(str)

    def __init__(self, workbook_path: Path, parent=None):
        super().__init__(parent)
        self.workbook_path = workbook_path

    def run(self) -> None:
        try:
            result = parse_reminder_workbook(self.workbook_path)
            if not result:
                self.error.emit(t("errores.pdf_sin_semanas_participantes"))
                return
            self.done.emit(result)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_leer_vmc", error=e))


class ResolveParticipantPhonesThread(QThread):
    done = pyqtSignal(list)  # list[tuple[Participant, Match]]

    def __init__(self, participants: list[Participant], contacts_csv: Path, parent=None):
        super().__init__(parent)
        self.participants = participants
        self.contacts_csv = contacts_csv

    def run(self) -> None:
        contacts = load_contacts(self.contacts_csv)
        result = []
        for p in self.participants:
            match = find_phone(p.name, contacts)
            updated = replace(p, phone=match.phone)
            result.append((updated, match))
        self.done.emit(result)


class GenerateCropThread(QThread):
    done = pyqtSignal(Path)
    error = pyqtSignal(str)

    def __init__(
        self, workbook_path: Path, fecha, output_folder: Path, parent=None,
        ajuste_arriba_pt: float = 0.0, ajuste_abajo_pt: float = 0.0,
    ):
        super().__init__(parent)
        self.workbook_path = workbook_path
        self.fecha = fecha
        self.output_folder = output_folder
        self.top_adjust_pt = ajuste_arriba_pt
        self.bottom_adjust_pt = ajuste_abajo_pt

    def run(self) -> None:
        try:
            folder = self.output_folder / self.fecha.strftime("%Y-%m")
            destination = folder / f"{self.fecha.isoformat()} - recordatorio VMC.jpg"
            crop_week_jpg(
                self.workbook_path, self.fecha, destination,
                ajuste_arriba_pt=self.top_adjust_pt, ajuste_abajo_pt=self.bottom_adjust_pt,
            )
            self.done.emit(destination)
        except Exception as e:
            self.error.emit(t("errores.no_se_pudo_generar_imagen", error=e))


class SendRemindersThread(QThread):
    progress = pyqtSignal(str, int, int)  # name, index, total
    result = pyqtSignal(object, bool, str)  # participant, success, reason
    waiting_qr = pyqtSignal()
    completed = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, items, message_txt: Path, config: Config, parent=None):
        super().__init__(parent)
        self.items = items
        self.message_txt = message_txt
        self.config = config
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        from ..send_reminders import send_reminders  # late import: Playwright is heavy to load

        try:
            send_reminders(
                self.items,
                plantilla_mensaje=self.message_txt,
                tiempos=self.config.timing,
                on_progreso=lambda name, i, total: self.progress.emit(name, i, total),
                on_resultado=lambda p, ok, reason: self.result.emit(p, ok, reason),
                debe_cancelar=lambda: self._cancel_requested,
                on_esperando_qr=lambda: self.waiting_qr.emit(),
            )
            self.completed.emit()
        except Exception as e:
            self.error.emit(t("errores.error_enviando_recordatorios", error=e))
