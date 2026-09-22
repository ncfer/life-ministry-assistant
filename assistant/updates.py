"""Checks GitHub for a newer release of the app.

Deliberately does NOT download or replace anything (decided with the
user): it only reports that a new version exists and hands over the
release page's URL, which the About dialog opens in the browser. On
Windows the running .exe is locked by the OS and can't overwrite itself
without an external helper script, and a half-applied update leaves the
user with no working app at all — not a trade worth making for a tool
that gets updated a couple of times a year.

Everything here fails silently: no network, GitHub down, rate limit or
a malformed answer all mean "no update info", never an error popup in
front of someone who just wanted to send their assignments.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

from . import __version__

REPO = "ncfer/life-ministry-assistant"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"
TIMEOUT_S = 5


@dataclass
class Release:
    version: str  # normalized, without the leading "v"
    url: str


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.3' -> (1, 2, 3). Anything unparseable becomes (0,), which
    compares lower than any real release, so a tag the app doesn't
    understand never gets announced as an update."""
    numbers = []
    for part in text.strip().lstrip("vV").split("."):
        digits = ""
        for char in part:
            if not char.isdigit():
                break  # stops at the suffix in "1.2.0-beta1"
            digits += char
        if not digits:
            break
        numbers.append(int(digits))
    return tuple(numbers) if numbers else (0,)


def is_newer(candidate: str, current: str = __version__) -> bool:
    return parse_version(candidate) > parse_version(current)


def latest_release() -> Release | None:
    """The newest published release, or None if it can't be checked."""
    try:
        response = requests.get(
            API_URL, timeout=TIMEOUT_S,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        data = response.json()
        tag = data["tag_name"]
    except Exception:
        return None
    return Release(version=tag.lstrip("vV"), url=data.get("html_url") or RELEASES_URL)
