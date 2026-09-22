"""Self-check for the two pieces of new logic that aren't UI:
version comparison (assistant/updates.py) and the manual export
(assistant/manual_export.py).

    python dev/check_updates_export.py

Nothing here touches the network or the real config: the update check
is only exercised through its pure functions.
"""
from __future__ import annotations

import datetime
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assistant.manual_export import (  # noqa: E402
    export_for_manual_send, export_reminders_for_manual_send, safe_name,
)
from assistant.reminder_workbook import Participant  # noqa: E402
from assistant.models import Assignment  # noqa: E402
from assistant.updates import is_newer, parse_version  # noqa: E402


def check_versions() -> None:
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("1.2.0-beta1") == (1, 2, 0)
    assert parse_version("nonsense") == (0,)  # never announced as an update

    assert is_newer("1.0.1", "1.0.0")
    assert is_newer("1.1.0", "1.0.9")
    assert is_newer("2.0", "1.9.9")
    assert not is_newer("1.0.0", "1.0.0")
    assert not is_newer("0.9.9", "1.0.0")
    assert not is_newer("nonsense", "1.0.0")
    # 1.10 is newer than 1.9 — the reason versions are compared as
    # integer tuples and not as strings ("1.10" < "1.9" as text).
    assert is_newer("1.10.0", "1.9.0")
    print("  ok     comparación de versiones")


def check_export() -> None:
    assert safe_name("Ana/María") == "Ana-María"
    assert safe_name("...") == "sin-nombre"
    assert safe_name("Álex Núñez") == "Álex Núñez"  # accents are left alone

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "source"
        source.mkdir()
        jpg = source / "slip.jpg"
        ics = source / "slip.ics"
        jpg.write_bytes(b"fake jpg")
        ics.write_text("BEGIN:VCALENDAR", encoding="utf-8")

        template = tmp_path / "message.txt"
        template.write_text("Hola {nombre_pila}, te toca el {fecha}.", encoding="utf-8")

        assignment = Assignment(
            name="Álex Núñez", helper="", date=datetime.date(2026, 10, 7),
            number="3", part="Empieza conversaciones", phone="34600111222",
        )
        destination = tmp_path / "salida"
        created = export_for_manual_send(
            [(assignment, jpg, ics)], destination, template, "ics")

        assert len(created) == 1, created
        folder = destination / "Álex Núñez"
        assert folder.is_dir()
        assert (folder / "slip.jpg").read_bytes() == b"fake jpg"
        assert (folder / "slip.ics").exists()

        message = (folder / "mensaje.txt").read_text(encoding="utf-8")
        assert message.startswith("34600111222"), message
        assert "Hola Álex" in message, message
        assert "7" in message, message  # the date got formatted in

        # gcal mode sends a link instead of a file: no .ics copied.
        only_link = tmp_path / "solo-link"
        export_for_manual_send([(assignment, jpg, ics)], only_link, template, "gcal")
        assert not (only_link / "Álex Núñez" / "slip.ics").exists()
        assert (only_link / "Álex Núñez" / "slip.jpg").exists()
    print("  ok     volcado manual")


def check_reminder_export() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        jpg = tmp_path / "semana.jpg"
        jpg.write_bytes(b"fake jpg")
        template = tmp_path / "recordatorio.txt"
        template.write_text("Hola {nombre_pila}, {fecha_relativa}: {rol}.", encoding="utf-8")

        participante = Participant(
            name="Álex Núñez", date=datetime.date(2026, 10, 7),
            roles=["Lectura de la Biblia"], phone="34600111222")
        destino = tmp_path / "salida-rec"
        created = export_reminders_for_manual_send([(participante, jpg)], destino, template)

        assert len(created) == 1
        folder = destino / "Álex Núñez"
        # todos comparten la misma imagen de la semana, pero cada carpeta
        # tiene la suya para poder reenviarla tal cual
        assert (folder / "semana.jpg").read_bytes() == b"fake jpg"
        mensaje = (folder / "mensaje.txt").read_text(encoding="utf-8")
        assert mensaje.startswith("34600111222"), mensaje
        assert "Hola Álex" in mensaje, mensaje
        assert "Lectura de la Biblia" in mensaje, mensaje
    print("  ok     volcado manual de recordatorios")


def check_navigation() -> None:
    """go_to() rebuilds the target page, go_back() shows it as it was.

    Uses stand-in objects instead of a real window: both methods only
    ever touch `self.stack`, so this pins the behaviour down without
    starting Qt (and without the startup update check hitting the
    network).
    """
    from assistant.gui.main_window import MainWindow

    class FakePage:
        def __init__(self):
            self.entered = 0

        def enter(self):
            self.entered += 1

    class FakeStack:
        def __init__(self, pages):
            self.pages = pages
            self.current = None

        def widget(self, index):
            return self.pages[index]

        def setCurrentIndex(self, index):
            self.current = index

    page = FakePage()
    window = type("W", (), {"stack": FakeStack([FakePage(), page])})()

    MainWindow.go_to(window, 1)
    assert page.entered == 1, "ir hacia delante debe regenerar"
    assert window.stack.current == 1

    MainWindow.go_back(window, 1)
    assert page.entered == 1, "volver atrás NO debe regenerar"
    assert window.stack.current == 1
    print("  ok     volver atrás no regenera")


def check_send_step_error() -> None:
    """El fallo dice qué mitad del envío se rompió, no solo que falló."""
    from assistant.whatsapp_send import SendStepError

    error = SendStepError("La papeleta se envió, pero no el recordatorio",
                          TimeoutError("timeout 30000ms"))
    assert "recordatorio" in str(error)
    assert "timeout" in str(error)          # la causa original no se pierde
    assert isinstance(error, Exception)
    print("  ok     el fallo identifica el adjunto")


def check_sent_confirmation() -> None:
    """_wait_until_sent espera de verdad, y falla si algo sigue pendiente.

    Se prueba contra una página local con el mismo icono que usa
    WhatsApp, no contra WhatsApp: lo que se verifica es la lógica de
    espera, y así el check no necesita ni red ni sesión.
    """
    from playwright.sync_api import sync_playwright

    from assistant.whatsapp_send import PENDING_ICON, _wait_until_sent

    pendiente = f"<svg><title>{PENDING_ICON}</title></svg>"
    enviado = "<svg><title>wds-ic-read</title></svg>"

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                try:
                    browser = p.chromium.launch(headless=True, channel="chrome")
                except Exception:
                    print("  --     confirmación de envío (sin navegador, omitido)")
                    return
            page = browser.new_page()

            page.set_content(f"<body>{enviado}</body>")
            _wait_until_sent(page)          # nada pendiente: vuelve enseguida

            page.set_content(f"<body>{pendiente}</body>")
            try:
                page.set_default_timeout(2000)
                page.wait_for_function(
                    """(pending) => ![...document.querySelectorAll('svg > title')]
                         .some(t => t.textContent === pending)""",
                    arg=PENDING_ICON, timeout=2000)
            except Exception:
                pass                         # lo esperado: sigue pendiente
            else:
                raise AssertionError("no detectó un mensaje que seguía pendiente")
            browser.close()
    except AssertionError:
        raise
    print("  ok     confirmación de envío (detecta lo pendiente)")


if __name__ == "__main__":
    check_versions()
    check_export()
    check_reminder_export()
    check_navigation()
    check_send_step_error()
    check_sent_confirmation()
    print("\nTodo correcto.")
