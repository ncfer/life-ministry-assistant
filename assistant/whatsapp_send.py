"""Sends the slips (JPG) and the reminder (ICS and/or Google Calendar
link) over WhatsApp Web, using Playwright instead of the original
SendKeys-based VBA macro.

Requires having logged in once by scanning the QR: the session is saved
in a persistent browser profile (SESSION_DIR) and reused on later runs
without asking for the QR again.

Account safety: by default the same wait times the original VBA macro
(EnviarWhatsAppDesdeTabla) used between each action are respected, except
the pause between contacts, which is deliberately longer here — the
macro had "00:00:4" (4 seconds, probably a typo for "00:00:40") with the
comment "pausa larga entre contactos" ("long pause between contacts"),
which didn't add up. All these wait times are configurable (see
assistant/config.py and the GUI's advanced settings screen), no need
to touch this file to adjust them.

Note: WhatsApp Web's DOM selectors can change with WhatsApp's own
updates. If some step stops finding an element, this is the first place
to check.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Callable, Literal

from playwright.sync_api import Page, sync_playwright

from .config import TimingConfig, load_config
from .dates import long_date
from .gcal_link import generate_gcal_link
from .i18n import t
from .models import Assignment

SESSION_DIR = Path.home() / ".local" / "share" / "life-ministry-assistant" / "whatsapp-session"
DEFAULT_MESSAGE_TEMPLATE = Path("message.txt")

TIMEOUT_QR_MS = 120_000
TIMEOUT_CHAT_MS = 30_000

ReminderMode = Literal["ics", "gcal", "ambos"]
ProgressCallback = Callable[[str, int, int], None]
ResultCallback = Callable[[Assignment, Path, Path, bool, str], None]


def load_message_template(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(t("errores.plantilla_no_encontrada", ruta=path))
    return path.read_text(encoding="utf-8").strip()


def format_message(assignment: Assignment, template: str, mode: ReminderMode) -> str:
    link = generate_gcal_link(assignment) if mode in ("gcal", "ambos") else ""
    # This dict's keys are the {placeholders} the user types by hand into
    # their message.txt (see README) — external, persisted format, not
    # Python identifiers. Both a Spanish and an English name are provided
    # for each one (same pattern as config.py's legacy-key migration) so
    # an existing Spanish template keeps working untouched AND an
    # English-language congregation can write their own template using
    # English placeholder names.
    first_name = assignment.name.split()[0]
    fields = {
        "nombre": assignment.name, "name": assignment.name,
        "nombre_pila": first_name, "first_name": first_name,
        "ayudante": assignment.helper, "helper": assignment.helper,
        "fecha": long_date(assignment.date), "date": long_date(assignment.date),
        "numero": assignment.number, "number": assignment.number,
        "tipo": assignment.part, "type": assignment.part,
        "link": link,
    }
    text = template.format(**fields)
    # If the template doesn't include {link} but the mode asks for the link, append it.
    if link and "{link}" not in template:
        text = f"{text}\n\n{link}"
    return text


def _wait_for_chat_ready(page: Page, tiempos: TimingConfig) -> None:
    # NOTE: the selector must be specific to the real message box
    # (aria-label "Escribir un mensaje para ..."), not just any
    # contenteditable with data-tab — the side search box also has one,
    # so a generic selector gives a false "chat ready" positive when the
    # target chat hasn't actually finished opening (seen with
    # send?phone=... failing on back-to-back sends).
    page.wait_for_selector(
        'div[contenteditable="true"][data-tab][aria-label^="Escribir un mensaje"]',
        timeout=TIMEOUT_CHAT_MS,
    )
    page.wait_for_timeout(tiempos.open_chat_wait_s * 1000)


def _write_in_box(box, text: str) -> None:
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line:
            box.type(line)
        if i < len(lines) - 1:
            box.press("Shift+Enter")


def _attach_file(
    page: Page, path: Path, tiempos: TimingConfig, *, es_imagen: bool, leyenda: str | None = None
) -> None:
    """Attaches and sends a file from the attach menu (the clip/+).

    The menu has several entries (Document, Photos and videos, New
    sticker...) and each one adds its own hidden <input type="file"> to
    the DOM. Before the right menu item is clicked, the only input
    present is the "New sticker" one (accept="image/*", single file) — if
    that's used by mistake, the image gets sent as a sticker instead of a
    normal photo. That's why the matching menu entry has to be clicked
    first so the right input appears, then selected with a selector that
    can't be confused with the sticker one:
      - "Fotos y videos" adds an input with multiple and an accept that
        includes video types (the sticker one only accepts images).
      - "Documento" adds an input with accept="*" (exact match, not an
        entry that merely contains the "*" character).

    If `leyenda` is given, it's typed into the preview's text box
    (aria-label="Escribe un mensaje", different from the normal
    conversation box) before sending, so the file and the text travel as
    a single message.

    Clicking "Fotos y videos"/"Documento" makes WhatsApp call click() on
    the <input type="file">, which in a real (non-headless) browser opens
    the operating system's NATIVE file picker — which blocks everything
    and Playwright can't close it (or even see it: it doesn't show up in
    a screenshot, since it isn't part of the page). That's why this
    dialog has to be captured with expect_file_chooser() BEFORE the
    click, so Playwright intercepts it and the native one never even
    opens.
    """
    page.locator('span[data-icon="plus-rounded"], span[data-icon="clip"]').first.click()
    with page.expect_file_chooser() as fc_info:
        if es_imagen:
            page.get_by_text("Fotos y videos", exact=True).click()
        else:
            page.get_by_text("Documento", exact=True).click()
    fc_info.value.set_files(str(path))
    page.wait_for_timeout(tiempos.after_attach_wait_s * 1000)

    page.wait_for_selector('span[data-icon="send"], span[data-icon="wds-ic-send-filled"]',
                            timeout=TIMEOUT_CHAT_MS)
    page.wait_for_timeout(tiempos.after_upload_wait_s * 1000)

    if leyenda:
        box = page.locator('div[contenteditable="true"][aria-label="Escribe un mensaje"]')
        box.click()
        _write_in_box(box, leyenda)

    page.locator('span[data-icon="send"], span[data-icon="wds-ic-send-filled"]').first.click()
    page.wait_for_timeout(tiempos.after_send_wait_s * 1000)


def _find_system_chromium() -> str | None:
    """Looks for a Chromium installed by the system's package manager
    (common on Linux), trying the most usual binary names."""
    for name in ("chromium", "chromium-browser", "chromium-freeworld"):
        path = shutil.which(name)
        if path:
            return path
    return None


def open_session(playwright, on_esperando_qr: Callable[[], None] | None = None):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Try Chrome first (most common), then Edge (comes preinstalled on
    # every Windows machine, nothing to download even if the user never
    # touched Chrome/Chromium), then the system's Chromium (typical on
    # many Linux distros, e.g. Arch/CachyOS) and, if none is installed,
    # Playwright's own bundled Chromium (downloaded once with 'playwright
    # install chromium') — this last one is the only case that needs to
    # download anything extra.
    attempts = [
        {"channel": "chrome"},
        {"channel": "msedge"},
        {"executable_path": _find_system_chromium()},
        {},  # Chromium bundled with Playwright
    ]

    last_error: Exception | None = None
    for kwargs in attempts:
        if kwargs.get("executable_path") is None and "executable_path" in kwargs:
            continue  # no system chromium, no point trying it
        try:
            context = playwright.chromium.launch_persistent_context(
                str(SESSION_DIR), headless=False, **kwargs
            )
            break
        except Exception as e:
            last_error = e
    else:
        raise RuntimeError(t("errores.sin_navegador")) from last_error

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.whatsapp.com")

    qr = page.locator('canvas[aria-label], div[data-testid="qrcode"]')
    try:
        qr.first.wait_for(timeout=5000)
        if on_esperando_qr:
            on_esperando_qr()
        else:
            print(t("envio.escanea_qr"))
        qr.first.wait_for(state="detached", timeout=TIMEOUT_QR_MS)
    except Exception:
        pass  # session was already open, no QR appeared

    page.wait_for_timeout(2000)
    return context, page


def send_assignments(
    items: list[tuple[Assignment, Path, Path]],
    modo_recordatorio: ReminderMode = "ambos",
    plantilla_mensaje: Path = DEFAULT_MESSAGE_TEMPLATE,
    tiempos: TimingConfig | None = None,
    on_progreso: ProgressCallback | None = None,
    on_resultado: ResultCallback | None = None,
    debe_cancelar: Callable[[], bool] | None = None,
    on_esperando_qr: Callable[[], None] | None = None,
) -> None:
    """items: list of (assignment_with_phone, jpg_path, ics_path).

    on_progreso(name, index, total) is called after each send (or when
    skipping someone), so a GUI can show progress. on_resultado(assignment,
    jpg, ics, success, reason) is called after each attempt, to keep a
    log/history or retry only the failed ones. debe_cancelar() is checked
    between contacts to allow stopping partway through from the GUI.
    on_esperando_qr() is called if the QR code needs to be scanned (first
    time, or an expired session).
    """
    tiempos = tiempos or load_config().timing
    template = load_message_template(plantilla_mensaje)
    total = len(items)

    with sync_playwright() as p:
        context, page = open_session(p, on_esperando_qr=on_esperando_qr)

        for i, (assignment, jpg, ics) in enumerate(items, start=1):
            if debe_cancelar and debe_cancelar():
                print(t("envio.cancelado_usuario"))
                break

            print(t("envio.enviando_a", nombre=assignment.name, telefono=assignment.phone))
            final_error: Exception | None = None
            for attempt in (1, 2):
                if page.is_closed():
                    # The browser crashed (seen in practice after several
                    # attachments in a row) — reopen the session and retry
                    # this same contact once before giving up on it,
                    # instead of dragging the failure into everyone still
                    # left to send.
                    print(t("envio.navegador_reabriendo"))
                    context, page = open_session(p, on_esperando_qr=on_esperando_qr)
                try:
                    text = format_message(assignment, template, modo_recordatorio)
                    page.goto(f"https://web.whatsapp.com/send?phone={assignment.phone}")
                    _wait_for_chat_ready(page, tiempos)
                    _attach_file(page, jpg, tiempos, es_imagen=True, leyenda=text)
                    if modo_recordatorio in ("ics", "ambos"):
                        _attach_file(page, ics, tiempos, es_imagen=False)
                    final_error = None
                    break
                except Exception as e:
                    final_error = e
                    if attempt == 1 and page.is_closed():
                        continue
                    break

            if final_error is not None:
                print(t("envio.aviso_fallo", nombre=assignment.name, error=final_error))
                if on_progreso:
                    on_progreso(f"{assignment.name} (falló, se omite)", i, total)
                if on_resultado:
                    on_resultado(assignment, jpg, ics, False, str(final_error))
                continue

            print(t("envio.ok", nombre=assignment.name))
            if on_progreso:
                on_progreso(assignment.name, i, total)
            if on_resultado:
                on_resultado(assignment, jpg, ics, True, "")
            time.sleep(tiempos.between_contacts_pause_s)

        context.close()
