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

from assistant.manual_export import export_for_manual_send, safe_name  # noqa: E402
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


if __name__ == "__main__":
    check_versions()
    check_export()
    check_navigation()
    print("\nTodo correcto.")
