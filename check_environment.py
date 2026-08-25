"""Lightweight check run before launching the app — meant to be compiled
into a small .exe with PyInstaller (only depends on the standard library:
it doesn't bundle PyQt6/pymupdf/playwright, those still live in the
project's own venv as always). Its only job is: if something's missing
(Python, a browser), tell the user with a clear window instead of a
console message or silence — and if everything's fine, prepare the venv
(first time) and actually start the app.

Deliberately split into two layers:
- DETECTION functions (from here down to `prepare_environment`): pure, no
  tkinter, checkable without opening any window.
- `main()` at the end: the only part that touches tkinter.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

# `Path(__file__)` doesn't work when this is compiled with PyInstaller in
# --onefile mode: the .exe self-extracts to a temp folder at runtime and
# __file__ would point there, not to where the real .exe is. `sys.executable`
# does point to the real .exe in that case (PyInstaller sets
# `sys.frozen = True`); running normally as a script, it's the interpreter
# itself, so the two cases have to be told apart.
if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent
VENV = ROOT / "venv"
REQUIREMENTS = ROOT / "requirements.txt"

IS_WINDOWS = sys.platform == "win32"


# --- Detection ----------------------------------------------------------

def system_python() -> str | None:
    """Returns the path to a usable system Python 3, or None if there
    isn't one. Doesn't count this checker's own interpreter (which, in
    the compiled .exe version, has its own embedded Python that can't be
    used to create the project's venv)."""
    for name in ("python3", "python"):
        path = shutil.which(name)
        if not path:
            continue
        try:
            result = subprocess.run(
                [path, "--version"], capture_output=True, text=True, timeout=10
            )
        except OSError:
            continue
        version = (result.stdout or result.stderr).strip()
        if version.startswith("Python 3"):
            return path
    return None


def available_browser() -> str | None:
    """Name of the first Chrome/Edge/Chromium browser found, or None.
    Same criteria as `whatsapp_send.open_session()`'s cascade (Chrome →
    Edge → system Chromium) — only need to know if there's ANY browser
    here, not which one to use (the app decides that at send time)."""
    windows_paths = {
        "Google Chrome": [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ],
        "Microsoft Edge": [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ],
    }
    if IS_WINDOWS:
        for name, paths in windows_paths.items():
            if any(Path(p).exists() for p in paths):
                return name

    for binary_name, label in (
        ("google-chrome", "Google Chrome"),
        ("google-chrome-stable", "Google Chrome"),
        ("chromium", "Chromium"),
        ("chromium-browser", "Chromium"),
        ("chromium-freeworld", "Chromium"),
        ("microsoft-edge-stable", "Microsoft Edge"),
    ):
        if shutil.which(binary_name):
            return label

    return None


def playwright_chromium_already_downloaded() -> bool:
    """If `playwright install chromium` already ran before (on this PC,
    or in an earlier launch), no need to ask/download again."""
    cache = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ms-playwright" \
        if IS_WINDOWS else Path.home() / ".cache" / "ms-playwright"
    return cache.exists() and any(cache.iterdir()) if cache.exists() else False


def venv_python() -> Path:
    if IS_WINDOWS:
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def venv_ready() -> bool:
    return venv_python().exists()


class SetupError(RuntimeError):
    pass


def prepare_venv(inform: Callable[[str], None]) -> None:
    """Creates the venv and installs dependencies if they don't already
    exist. `inform` is called with each step so the GUI layer can show
    progress — this function itself doesn't know anything about
    windows."""
    if venv_ready():
        return

    python_path = system_python()
    if not python_path:
        raise SetupError("No hay Python instalado en este equipo.")

    inform("Preparando la aplicación por primera vez (puede tardar unos minutos)...")
    try:
        subprocess.run(
            [python_path, "-m", "venv", str(VENV)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            [str(venv_python()), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            [str(venv_python()), "-m", "pip", "install", "--quiet", "-r", str(REQUIREMENTS)],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        shutil.rmtree(VENV, ignore_errors=True)
        detail = (e.stderr or e.stdout or "").strip()[-800:]
        raise SetupError(
            f"No se pudo preparar la aplicación (revisa la conexión a internet).\n\n{detail}"
        ) from e


def prepare_browser(inform: Callable[[str], None]) -> None:
    """Only downloads Playwright's own Chromium if there's really NO
    usable browser at all and it wasn't already downloaded before — never
    silently, always warning first (that's `main()`'s call, this function
    only runs the download itself)."""
    inform("Descargando un navegador para poder enviar por WhatsApp (una sola vez)...")
    try:
        subprocess.run(
            [str(venv_python()), "-m", "playwright", "install", "chromium"],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip()[-800:]
        raise SetupError(f"No se pudo descargar el navegador.\n\n{detail}") from e


def launch_app() -> None:
    subprocess.Popen(
        [str(venv_python()), "-m", "assistant.gui.app"],
        cwd=str(ROOT),
    )


# --- Interface (tkinter) -------------------------------------------------

def main() -> None:
    import tkinter as tk
    from tkinter import messagebox

    tk_root = tk.Tk()
    tk_root.withdraw()  # only dialogs are used, no need for its own window

    python_path = system_python()
    if not python_path and not venv_ready():
        messagebox.showerror(
            "Life & Ministry Assistant",
            "Falta Python, necesario para ejecutar esta aplicación.\n\n"
            "Descárgalo de https://www.python.org/downloads/\n"
            "(marca la casilla 'Add python.exe to PATH' durante la instalación)\n"
            "y vuelve a abrir Life & Ministry Assistant.",
        )
        return

    progress_window = None

    def inform(message: str) -> None:
        nonlocal progress_window
        if progress_window is None:
            progress_window = tk.Toplevel(tk_root)
            progress_window.title("Life & Ministry Assistant")
            progress_window.resizable(False, False)
            label = tk.Label(progress_window, text="", padx=24, pady=20, wraplength=360)
            label.pack()
            progress_window._label = label
        progress_window._label.config(text=message)
        progress_window.update()

    try:
        prepare_venv(inform)

        if not available_browser() and not playwright_chromium_already_downloaded():
            if progress_window is not None:
                progress_window.withdraw()
            download = messagebox.askyesno(
                "Life & Ministry Assistant",
                "No se ha encontrado Google Chrome, Microsoft Edge ni Chromium "
                "en este equipo — hace falta uno para poder enviar por WhatsApp.\n\n"
                "¿Descargar un navegador propio solo para esta app? "
                "(única vez, unos 200 MB, hace falta internet)\n\n"
                "Si prefieres instalar Google Chrome o usar Edge en vez de esto, "
                "pulsa 'No' y ábrelos primero.",
            )
            if download:
                prepare_browser(inform)
    except SetupError as e:
        if progress_window is not None:
            progress_window.destroy()
        messagebox.showerror("Life & Ministry Assistant", str(e))
        return

    if progress_window is not None:
        progress_window.destroy()
    launch_app()


if __name__ == "__main__":
    main()
