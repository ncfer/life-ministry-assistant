"""Checks that WhatsApp Web's DOM still matches the selectors used in
assistant/whatsapp_send.py, WITHOUT sending anything.

WhatsApp changes these selectors on its own schedule (the attach button
alone has been `clip`, `plus-rounded` and now `ic-attach-file`), and when
one breaks, the app fails with a 30-second timeout per contact and an
error that says nothing useful. This walks the same steps a real send
does — open chat, attach menu, pick a photo, reach the preview — and
reports which specific selector is gone.

    python dev/check_whatsapp_selectors.py [phone]

`phone` defaults to config.json's `test_number`. The chat it opens is
only used to look at the DOM: the preview is discarded, never sent.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from assistant.config import load_config  # noqa: E402
from assistant.whatsapp_send import open_session  # noqa: E402

# Each entry is (what it's for, the selector as whatsapp_send.py writes it).
# Keep this list in sync with that module — it's the point of the check.
CHECKS = [
    ("caja de mensaje del chat",
     'div[contenteditable="true"][data-tab][aria-label^="Escribir un mensaje"]'),
    ("botón de adjuntar",
     'span[data-icon="ic-attach-file"], span[data-icon="plus-rounded"], span[data-icon="clip"]'),
]
PREVIEW_CHECKS = [
    ("caja de leyenda del adjunto",
     'div[contenteditable="true"][aria-label="Escribe un mensaje"]'),
    ("botón de enviar",
     'span[data-icon="send"], span[data-icon="wds-ic-send-filled"]'),
]
MENU_ENTRIES = ("Fotos y videos", "Documento")

fallos: list[str] = []


def comprobar(page, descripcion: str, selector: str, timeout: int = 15_000) -> bool:
    try:
        page.wait_for_selector(selector, timeout=timeout)
    except Exception:
        print(f"  FALLA  {descripcion}\n         {selector}")
        fallos.append(descripcion)
        return False
    print(f"  ok     {descripcion}")
    return True


def main() -> int:
    phone = sys.argv[1] if len(sys.argv) > 1 else load_config().test_number
    if not phone:
        print("No hay número: pásalo como argumento o pon test_number en config.json")
        return 2

    # A 1x1 JPG is enough to reach the preview screen; no need for a real slip.
    tmp = Path(tempfile.mkdtemp()) / "check.jpg"
    tmp.write_bytes(bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb004300ff"
        "ffffffffffffffffffffffffffffffffffffffffffffffffffff"
        "ffffffffffffffffffffffffffffffffffffffffffffffffffff"
        "ffffffffffffffffffffffffffffffffffffffffffffffffffff"
        "ffffffffffffffffffffffffffffc2000b080001000101011100"
        "ffc40014100100000000000000000000000000000000ffda0008"
        "01010000010500fe9fe0ffd9"))

    print(f"Comprobando selectores de WhatsApp Web con {phone}...")
    with sync_playwright() as p:
        context, page = open_session(p)
        try:
            page.goto(f"https://web.whatsapp.com/send?phone={phone}")
            if not comprobar(page, *CHECKS[0], timeout=30_000):
                return 1
            page.wait_for_timeout(3000)
            if not comprobar(page, *CHECKS[1]):
                return 1

            page.locator(CHECKS[1][1]).first.click()
            page.wait_for_timeout(1500)
            for entrada in MENU_ENTRIES:
                if page.get_by_text(entrada, exact=True).count():
                    print(f"  ok     entrada del menú «{entrada}»")
                else:
                    print(f"  FALLA  entrada del menú «{entrada}»")
                    fallos.append(f"menú: {entrada}")

            with page.expect_file_chooser() as fc:
                page.get_by_text("Fotos y videos", exact=True).click()
            fc.value.set_files(str(tmp))
            page.wait_for_timeout(4000)
            for descripcion, selector in PREVIEW_CHECKS:
                comprobar(page, descripcion, selector)

            # El envío se confirma esperando a que desaparezca el icono
            # wds-ic-status-pending (ver _wait_until_sent). Si WhatsApp
            # cambiara ese esquema de nombres, los mensajes ya enviados
            # dejarían de mostrar wds-ic-read y la confirmación se
            # quedaría esperando para siempre.
            page.keyboard.press("Escape")
            page.wait_for_timeout(1500)
            tiene_estados = page.evaluate(
                """() => [...document.querySelectorAll('svg > title')]
                     .some(t => t.textContent.startsWith('wds-ic-'))""")
            if tiene_estados:
                print("  ok     esquema de iconos de estado (wds-ic-*)")
            else:
                print("  FALLA  esquema de iconos de estado (wds-ic-*)")
                fallos.append("iconos de estado")
        finally:
            context.close()  # the preview is thrown away, nothing is sent

    if fallos:
        print(f"\n{len(fallos)} selector(es) rotos: " + ", ".join(fallos))
        print("Arréglalos en assistant/whatsapp_send.py y actualiza este fichero.")
        return 1
    print("\nTodo correcto: el envío debería funcionar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
