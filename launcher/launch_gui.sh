#!/usr/bin/env bash
# Opens the Life & Ministry Assistant GUI. The first time it runs it
# installs itself (virtual environment + dependencies + browser if
# needed); after that it just opens the window.
# This file now lives in launcher/, but venv/, requirements.txt and the
# assistant package it runs are all one level up, at the project root.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

warn() {
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$1"
    elif command -v zenity >/dev/null 2>&1; then
        zenity --error --text="$1"
    elif command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$1\" with title \"Life & Ministry Assistant\" buttons {\"OK\"} default button 1 with icon stop" >/dev/null 2>&1
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send -u critical "Life & Ministry Assistant" "$1"
    else
        echo "$1"
        read -p "Pulsa Intro para cerrar..." _
    fi
}

inform() {
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "$1"
    elif command -v zenity >/dev/null 2>&1; then
        zenity --info --text="$1"
    elif command -v osascript >/dev/null 2>&1; then
        osascript -e "display dialog \"$1\" with title \"Life & Ministry Assistant\" buttons {\"OK\"} default button 1" >/dev/null 2>&1
    else
        echo "$1"
    fi
}

has_system_chrome() {
    command -v google-chrome >/dev/null 2>&1 && return 0
    command -v google-chrome-stable >/dev/null 2>&1 && return 0
    command -v chromium >/dev/null 2>&1 && return 0
    command -v chromium-browser >/dev/null 2>&1 && return 0
    [ -d "/Applications/Google Chrome.app" ] && return 0
    return 1
}

if ! command -v python3 >/dev/null 2>&1; then
    warn "Falta Python 3, necesario para ejecutar esta aplicación.
Descárgalo de: https://www.python.org/downloads/
Luego vuelve a abrir Life & Ministry Assistant."
    exit 1
fi

first_run=0
if [ ! -d "venv" ]; then
    first_run=1
    inform "Primera vez que abres Life & Ministry Assistant: se va a instalar todo lo necesario. Puede tardar unos minutos y hace falta conexión a internet. No cierres esta ventana hasta que termine."

    log=$(mktemp)
    if ! python3 -m venv venv >"$log" 2>&1; then
        warn "No se pudo preparar la aplicación. Detalles:

$(tail -20 "$log")"
        rm -rf venv "$log"
        exit 1
    fi

    if ! venv/bin/python -m pip install --quiet --upgrade pip >"$log" 2>&1 \
        || ! venv/bin/python -m pip install --quiet -r requirements.txt >>"$log" 2>&1; then
        warn "No se pudieron instalar las dependencias (¿hay conexión a internet?). Detalles:

$(tail -20 "$log")"
        rm -rf venv "$log"
        exit 1
    fi
    rm -f "$log"
fi

# Sending over WhatsApp needs Chrome or Chromium. If none is installed on
# the system, Playwright's own browser is downloaded once (not needed if
# it was already downloaded in an earlier launch).
if ! has_system_chrome && [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
    inform "No se ha encontrado Google Chrome en este equipo: se va a descargar un navegador propio para el envío por WhatsApp (una sola vez, puede tardar un par de minutos)."
    log=$(mktemp)
    if ! venv/bin/python -m playwright install chromium >"$log" 2>&1; then
        warn "No se pudo descargar el navegador necesario para WhatsApp. Detalles:

$(tail -20 "$log")

Puedes instalar Google Chrome (google.com/chrome) y volver a abrir Life & Ministry Assistant."
    fi
    rm -f "$log"
fi

source venv/bin/activate
exec python3 -m assistant.gui.app
