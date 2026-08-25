"""Converts the filled-in assignment PDF to JPG.

PyMuPDF is used instead of poppler/pdf2image because poppler doesn't
render this template's checkbox check glyph (even though the AcroForm's
/V and /AS values are correct) — confirmed by comparing against a real
BulkPDF PDF, where the same problem happens with pdftoppm but not with
PyMuPDF.
"""
from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

DEFAULT_DPI = 200


def pdf_to_jpg(pdf_path: Path, destination: Path, dpi: int = DEFAULT_DPI) -> None:
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi)
        destination.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(destination))
    finally:
        doc.close()
