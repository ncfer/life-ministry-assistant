#!/usr/bin/env bash
# Generates a .zip ready to hand off to another person/congregation: a
# clean copy of the project, without personal data (real contacts, send
# history, config with your NAS paths, already-used VMCs, your own
# customized message templates, virtual environment...).
#
# Usage: ./package.sh   (run from this project, by you, not the recipient)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

NAME="life-ministry-assistant"
DATE=$(date +%Y%m%d)
DEST="dist"
FOLDER="$DEST/$NAME"
ZIP="$DEST/${NAME}-${DATE}.zip"

rm -rf "$FOLDER"
mkdir -p "$FOLDER"

rsync -a \
    --exclude "venv/" \
    --exclude "output/" \
    --exclude "__pycache__/" \
    --exclude "*.pyc" \
    --exclude ".whatsapp-session/" \
    --exclude "dist/" \
    --exclude "contacts.csv" \
    --exclude "config.json" \
    --exclude "history.csv" \
    --exclude "reminder_history.csv" \
    --exclude "message.txt" \
    --exclude "reminder_message.txt" \
    --exclude "VMC*.pdf" \
    --exclude "package.sh" \
    ./ "$FOLDER/"

# Ready-to-edit example contacts (instead of an empty CSV with no hint of
# the expected format); the user replaces them from the app itself.
cp contacts.example.csv "$FOLDER/contacts.csv"
mkdir -p "$FOLDER/output"

chmod +x "$FOLDER/launch_gui.sh" "$FOLDER/launch_gui.command" 2>/dev/null || true

(cd "$DEST" && rm -f "${NAME}-${DATE}.zip" && zip -rq "${NAME}-${DATE}.zip" "$NAME")

echo "Listo: $ZIP"
echo "Antes de repartirlo, recuerda que quien lo reciba tiene que poner su"
echo "propia plantilla PDF de asignación (PLANTILLA ASIGNACIONES.pdf) desde"
echo "la pantalla de Configuración general — no se incluye en el zip."
