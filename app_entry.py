"""Entry point for compiling the whole app with PyInstaller.

`assistant/gui/app.py` uses relative imports (`from ..config import
...`), which fail if PyInstaller takes it directly as the entry script.
This file only exists to give it an entry point with an absolute import —
it doesn't duplicate any logic, it just re-exports `main()`.
"""
from assistant.gui.app import main

if __name__ == "__main__":
    main()
