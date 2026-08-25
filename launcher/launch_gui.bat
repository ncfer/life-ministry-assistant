@echo off
setlocal enabledelayedexpansion
REM This file now lives in launcher\, but venv\, requirements.txt and the
REM assistant package it runs are all one level up, at the project root.
cd /d "%~dp0.."
set LOG=%TEMP%\life_ministry_assistant_setup.log

where python >nul 2>nul
if errorlevel 1 (
    call :warn "Falta Python, necesario para ejecutar esta aplicacion. Descargalo de https://www.python.org/downloads/ (marca 'Add python.exe to PATH' durante la instalacion) y vuelve a abrir Life & Ministry Assistant."
    exit /b 1
)

if exist "venv\Scripts\activate.bat" goto :browser

call :inform "Primera vez que abres Life & Ministry Assistant: se va a instalar todo lo necesario. Puede tardar unos minutos y hace falta conexion a internet. No cierres esta ventana hasta que termine."

python -m venv venv > "%LOG%" 2>&1
if errorlevel 1 (
    call :warn "No se pudo preparar la aplicacion. Revisa el archivo %LOG% para mas detalles."
    rmdir /s /q venv >nul 2>nul
    exit /b 1
)

venv\Scripts\python -m pip install --quiet --upgrade pip > "%LOG%" 2>&1
if errorlevel 1 (
    call :warn "No se pudo preparar la aplicacion (revisa que haya conexion a internet). Detalles en el archivo %LOG%."
    rmdir /s /q venv >nul 2>nul
    exit /b 1
)

venv\Scripts\python -m pip install --quiet -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
    call :warn "No se pudieron instalar las dependencias (revisa que haya conexion a internet). Detalles en el archivo %LOG%."
    rmdir /s /q venv >nul 2>nul
    exit /b 1
)

:browser
REM Sending over WhatsApp needs Chrome or Chromium. If it isn't found in
REM the usual paths, Playwright's own browser is downloaded once (not
REM needed if it was already downloaded in an earlier launch).
set CHROME_FOUND=0
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
REM Edge comes preinstalled on every Windows machine: if it's there,
REM nothing extra needs downloading (this used to only check Chrome).
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set CHROME_FOUND=1
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set CHROME_FOUND=1

if "%CHROME_FOUND%"=="0" if not exist "%LocalAppData%\ms-playwright" (
    call :inform "No se ha encontrado Google Chrome en este equipo: se va a descargar un navegador propio para el envio por WhatsApp (una sola vez, puede tardar un par de minutos)."
    venv\Scripts\python -m playwright install chromium > "%LOG%" 2>&1
    if errorlevel 1 (
        call :warn "No se pudo descargar el navegador necesario para WhatsApp (revisa %LOG%). Puedes instalar Google Chrome desde google.com/chrome y volver a abrir Life & Ministry Assistant."
    )
)

call venv\Scripts\activate.bat
python -m assistant.gui.app
exit /b 0

:warn
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('%~1', 'Life & Ministry Assistant', 'OK', 'Error')" >nul
exit /b 0

:inform
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('%~1', 'Life & Ministry Assistant', 'OK', 'Information')" >nul
exit /b 0
