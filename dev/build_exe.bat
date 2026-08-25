@echo off
REM Generates LifeMinistryAssistant.exe with the whole app inside (PyQt6,
REM pymupdf, playwright...) from app_entry.py. Does NOT include any
REM browser: Playwright never bundles Chromium via pip/PyInstaller, that's
REM always a separate download ("playwright install chromium") or, better,
REM uses whatever Chrome/Edge the recipient already has installed (see
REM whatsapp_send.open_session in the code) - if none is found when
REM sending over WhatsApp, the app itself warns with clear instructions,
REM it doesn't download anything on its own.
REM
REM Run ONCE on a real Windows machine (PyInstaller doesn't cross-compile
REM from Linux/Mac). Only needs repeating if the app's code changes - not
REM on every use.
setlocal
REM This script now lives in dev/, but everything it builds from
REM (app_entry.py, requirements.txt, assets/) is one level up, at the
REM project root — so it cd's to the parent, not to its own folder.
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
    echo Falta Python para poder compilar. Instalalo desde https://www.python.org/downloads/
    pause
    exit /b 1
)

python -m pip install --quiet --upgrade pip pyinstaller
if errorlevel 1 (
    echo No se pudo instalar PyInstaller. Revisa la conexion a internet.
    pause
    exit /b 1
)

python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo No se pudieron instalar las dependencias de la app. Revisa la conexion a internet.
    pause
    exit /b 1
)

python -m PyInstaller --onefile --windowed --name LifeMinistryAssistant --add-data "assets;assets" app_entry.py
if errorlevel 1 (
    echo La compilacion ha fallado, revisa el mensaje de arriba.
    pause
    exit /b 1
)

move /y "dist\LifeMinistryAssistant.exe" "LifeMinistryAssistant.exe" >nul
rmdir /s /q build >nul 2>nul
rmdir /s /q dist >nul 2>nul
del /q LifeMinistryAssistant.spec >nul 2>nul

echo.
echo Listo: LifeMinistryAssistant.exe generado en esta misma carpeta (pesa unos 150-200 MB,
echo lleva la app entera dentro - no hace falta tener Python instalado para usarlo).
echo A partir de ahora, para abrir la app usa ese archivo en vez de launch_gui.bat.
pause
