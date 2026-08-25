"""Access to a password-protected Padlet board, without a browser: plain
HTTP requests only (GET the page → extract CSRF token + session cookie
from the HTML itself → POST the password → GET the Markdown export that
Padlet generates natively, with title + text + attachment links for each
post).

Deliberately generic: the board URL and password are parameters, there's
nothing about a specific congregation here — so it works the same for
anyone else who wants to use this, just changing those two values.

Same code as `app/padlet.py` in `~/Proyectos/asignaciones-service`
(n8n microservice) — duplicated on purpose so the desktop app doesn't
depend on that service running. If a bug is fixed here, check whether it
applies there too, and vice versa.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

import requests

from .i18n import t

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

RE_CSRF = re.compile(r'<meta name="csrf-token" content="([^"]+)"')
RE_REQUIRES_PASSWORD = re.compile(r'"showPasswordInput":true')
RE_PASSWORD_SUBMIT_URL = re.compile(r'"passwordSubmitUrl":"([^"]+)"')
RE_PUBLIC_KEY = re.compile(r'"public_key":"([^"]+)"')
RE_PASSWORD_ERROR = re.compile(r'"passwordErrorText":"([^"]+)"')

# In the export Markdown, each post starts with "### N. Title" and its
# attachments are "[Attachment N](url)" lines up to the next "### " or the
# end of the document.
RE_POST = re.compile(r"^### \d+\.\s*(.+?)\s*$", re.MULTILINE)
RE_ATTACHMENT = re.compile(r"\[Attachment \d+\]\((https?://[^)]+)\)")


class PadletError(RuntimeError):
    pass


def _extract_public_key(html: str, password_submit_url: str | None, board_url: str) -> str:
    m = RE_PUBLIC_KEY.search(html)
    if m:
        return m.group(1)
    if password_submit_url:
        candidate = password_submit_url.rstrip("/").rsplit("/", 1)[-1]
        if candidate:
            return candidate
    candidate = board_url.rstrip("/").rsplit("/", 1)[-1].rsplit("-", 1)[-1]
    if candidate:
        return candidate
    raise PadletError(t("errores.padlet_sin_clave_publica"))


def _get(session: requests.Session, url: str, **kwargs) -> requests.Response:
    """GET with the given session, turning any network failure (timeout,
    DNS, connection refused, 4xx/5xx) into PadletError — without this, a
    network failure leaks through as an uncaught exception and prints an
    ugly traceback instead of a clear message (seen in practice: Padlet
    can return 403 if hit with too many requests in a short time)."""
    try:
        response = session.get(url, timeout=kwargs.pop("timeout", 15), **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        raise PadletError(t("errores.padlet_sin_acceso", url=url, error=e)) from e


def _authenticated_session(board_url: str, password: str | None) -> tuple[requests.Session, str, str]:
    """Returns (session with the needed cookies, page HTML, public_key)."""
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})

    response = _get(session, board_url)
    html = response.text

    password_submit_url = None
    m_submit = RE_PASSWORD_SUBMIT_URL.search(html)
    if m_submit:
        password_submit_url = m_submit.group(1)

    if RE_REQUIRES_PASSWORD.search(html):
        if not password:
            raise PadletError(t("errores.padlet_falta_password"))
        if not password_submit_url:
            raise PadletError(t("errores.padlet_sin_url_password"))
        m_csrf = RE_CSRF.search(html)
        if not m_csrf:
            raise PadletError(t("errores.padlet_sin_csrf"))
        csrf_token = m_csrf.group(1)

        try:
            password_response = session.post(
                urljoin(board_url, password_submit_url),
                json={"password": password},
                headers={
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Referer": board_url,
                },
                timeout=15,
                allow_redirects=True,
            )
        except requests.exceptions.RequestException as e:
            raise PadletError(t("errores.padlet_envio_password_fallo", error=e)) from e

        m_error = RE_PASSWORD_ERROR.search(password_response.text)
        if m_error and m_error.group(1) != "null":
            raise PadletError(t("errores.padlet_password_rechazada", detalle=m_error.group(1)))
        if password_response.status_code >= 400:
            raise PadletError(t("errores.padlet_password_error_http", codigo=password_response.status_code))

        # Re-read the page now authenticated — the previous html is the
        # password screen's, no good for getting the public_key unless it
        # was already in the passwordSubmitUrl.
        html = _get(session, board_url).text

    public_key = _extract_public_key(html, password_submit_url, board_url)
    return session, html, public_key


def list_posts(board_url: str, password: str | None = None) -> list[dict]:
    """Returns [{"title": ..., "attachments": [url, ...]}] for every post
    on the board, in the order they appear."""
    session, _html, public_key = _authenticated_session(board_url, password)
    md = _get(session, f"https://padlet.com/padlets/{public_key}/exports/markdown.md", timeout=20).text

    headers = list(RE_POST.finditer(md))
    if not headers:
        raise PadletError(t("errores.padlet_export_vacio"))

    posts = []
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(md)
        block = md[start:end]
        posts.append({
            "title": m.group(1),
            "attachments": RE_ATTACHMENT.findall(block),
        })
    return posts


def list_pdfs_by_title(board_url: str, title_contains: str, password: str | None = None) -> list[tuple[str, bytes]]:
    """Like `download_pdf_by_title`, but downloads ALL matching posts,
    not just the first. Important: the board can have both the current
    bimester's VMC and the next one's published at the same time (seen in
    real production, e.g. "VIDA Y MINISTERIO JULIO AGOSTO" and "VIDA Y
    MINISTERIO SEP OCT" coexisting) — just keeping the first match risks
    picking the wrong document. The caller decides what to do with several
    documents (e.g. merge everyone's weeks)."""
    posts = list_posts(board_url, password)
    target = title_contains.strip().lower()
    found = [p for p in posts if target in p["title"].lower()]

    if not found:
        titles = [p["title"] for p in posts]
        raise PadletError(t("errores.padlet_titulo_no_encontrado", titulo=title_contains, titulos=titles))

    result = []
    for p in found:
        if not p["attachments"]:
            raise PadletError(t("errores.padlet_sin_adjunto", titulo=p["title"]))
        try:
            response = requests.get(p["attachments"][0], timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise PadletError(t("errores.padlet_descarga_fallo", titulo=p["title"], error=e)) from e
        result.append((p["title"], response.content))
    return result


def download_pdf_by_title(board_url: str, title_contains: str, password: str | None = None) -> tuple[str, bytes]:
    """Finds (case/accent-insensitive) the first post whose title contains
    `title_contains` and downloads its first attachment. Returns
    (real_title, pdf_content)."""
    posts = list_posts(board_url, password)
    target = title_contains.strip().lower()

    found = next((p for p in posts if target in p["title"].lower()), None)
    if found is None:
        titles = [p["title"] for p in posts]
        raise PadletError(t("errores.padlet_titulo_no_encontrado", titulo=title_contains, titulos=titles))
    if not found["attachments"]:
        raise PadletError(t("errores.padlet_sin_adjunto", titulo=found["title"]))

    try:
        response = requests.get(found["attachments"][0], timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise PadletError(t("errores.padlet_descarga_fallo", titulo=found["title"], error=e)) from e
    return found["title"], response.content
