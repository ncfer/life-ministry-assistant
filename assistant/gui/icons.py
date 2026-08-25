"""Loads the SVG icons in assets/icons/ (Lucide, ISC license — see
assets/icons/LICENSE — plus one hand-drawn to match, "message.svg", since
Lucide doesn't have an exact "editable message" icon) and recolors them
for the current theme.

Qt's own SVG renderer resolves `currentColor` to black when there's no
surrounding CSS context (there never is here, these are loaded as
standalone files) — so instead of relying on that, the SVG source text is
read once and `currentColor` is textually replaced with the real hex
color before rendering. This is simpler and more reliable than
compositing tricks, and safe because these are our own bundled files, not
arbitrary/untrusted SVG.

Two earlier versions of this module pre-baked the icon into a fixed-size
QPixmap (first with a hand-computed devicePixelRatio, then without one at
all) — both looked fine in this dev environment's QT_QPA_PLATFORM=offscreen
renders, and both were genuinely broken (icons clipped/misaligned) on the
user's real HiDPI screen (devicePixelRatio=2.0), because a pre-baked
pixmap's correctness depends on correctly guessing the real screen's DPR
ahead of time. `svg_renderer()` below sidesteps that entirely: it hands
back the live QSvgRenderer, and callers render it fresh inside their own
paintEvent (see widgets.IconBadge) — Qt gives every paintEvent a QPainter
already tied to the real target's actual device pixel ratio, so there is
no DPR to guess. This is also what makes the icon genuinely vector end to
end: it's re-rasterized at whatever exact resolution the screen needs,
never scaled from a fixed-size bitmap.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QByteArray
from PyQt6.QtSvg import QSvgRenderer

_ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

# Same (name, color) combination gets requested many times (every time a
# page/dialog is rebuilt) — no point re-reading/re-parsing the SVG each
# time. A QSvgRenderer has no notion of "size" baked in, so the cache key
# is just (name, color) instead of also a pixel size.
_cache: dict[tuple[str, str], QSvgRenderer] = {}


def svg_renderer(name: str, color: str) -> QSvgRenderer:
    """The recolored SVG for `name` (a file stem in assets/icons/), ready
    to `.render(painter, target_rect)` at whatever size the caller needs,
    as many times as needed — a QSvgRenderer is reusable, it doesn't get
    consumed by rendering."""
    key = (name, color)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    svg_path = _ICONS_DIR / f"{name}.svg"
    svg_text = svg_path.read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    _cache[key] = renderer
    return renderer
