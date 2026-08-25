"""Downloads a single PDF from a Google Drive share link, without any
Google API credentials — same "no login, just HTTP requests" spirit as
padlet.py, but simpler: Drive only exposes ONE file this way (no
title-based search across a folder), so the app just re-downloads
whatever file the configured link points to.

For a small file, Drive serves it directly. For a larger one, the first
response is an HTML "Google Drive can't scan this file for viruses"
warning page instead of the file — the real download needs a second
request with a confirmation token pulled either from that page's HTML or
from a `download_warning_*` cookie Drive sets alongside it.
"""
from __future__ import annotations

import re

import requests

from .i18n import t

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

_DOWNLOAD_URL = "https://drive.google.com/uc?export=download"

RE_FILE_ID_PATH = re.compile(r"/file/d/([a-zA-Z0-9_-]+)")
RE_FILE_ID_PARAM = re.compile(r"[?&]id=([a-zA-Z0-9_-]+)")
RE_CONFIRM_TOKEN = re.compile(r'confirm=([0-9A-Za-z_-]+)')


class DriveError(RuntimeError):
    pass


def extract_file_id(link: str) -> str:
    link = link.strip()
    m = RE_FILE_ID_PATH.search(link)
    if m:
        return m.group(1)
    m = RE_FILE_ID_PARAM.search(link)
    if m:
        return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{10,}", link):
        return link
    raise DriveError(t("errores.drive_link_invalido"))


def _confirm_token(response: requests.Response) -> str | None:
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    if "text/html" in response.headers.get("Content-Type", ""):
        m = RE_CONFIRM_TOKEN.search(response.text)
        if m:
            return m.group(1)
    return None


def download_pdf(link: str) -> bytes:
    """Returns the raw PDF bytes for the file at `link`. Raises
    DriveError if the link doesn't point to a valid public file (e.g.
    "Anyone with the link" sharing isn't enabled)."""
    file_id = extract_file_id(link)
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})

    try:
        response = session.get(_DOWNLOAD_URL, params={"id": file_id}, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DriveError(t("errores.drive_sin_acceso", error=e)) from e

    token = _confirm_token(response)
    if token:
        try:
            response = session.get(
                _DOWNLOAD_URL, params={"id": file_id, "confirm": token}, timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise DriveError(t("errores.drive_sin_acceso", error=e)) from e

    if "text/html" in response.headers.get("Content-Type", ""):
        raise DriveError(t("errores.drive_no_publico"))

    return response.content
