"""Generates assets/icon.png (the app icon) and assets/logo.png (the
"Life & Ministry Assistant" wordmark).

The icon is an open-book glyph (Lucide's "book-open", ISC license — see
assets/icons/LICENSE) on a rounded-square brand-color background,
rendered live via QSvgRenderer/QPainter (Qt) — not the actual jw.org/WOL
logo: this project deliberately stays legally separate from that
trademark (see project memory), so the look nods at the same "open
book" spirit of Bible study/ministry without copying any real emblem.

The wordmark reuses Fraunces (assets/fonts/, SIL Open Font License, the
app's own title typeface since the 24/08 visual refresh) instead of
Playfair Display, which this script used to depend on before those font
files were removed as apparently-unused — turned out they weren't,
whoops. One consistent display face across the UI and the wordmark now.

Run again whenever the brand color (assistant/gui/style.py's PRIMARY)
changes, to regenerate both images with the new color.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

from assistant.gui.style import PRIMARY, PRIMARY_HOVER

ICONS_DIR = Path(__file__).parent / "icons"
FONTS_DIR = Path(__file__).parent / "fonts"
FONT_TITLE = FONTS_DIR / "Fraunces-SemiBold.ttf"
FONT_SUBTITLE = FONTS_DIR / "Fraunces-Medium.ttf"

WHITE = (255, 255, 255)

# A QApplication instance is required before any Qt painting happens
# (QPixmap/QPainter/QSvgRenderer all need one) — offscreen is fine here,
# this script never shows a window.
_app = QApplication.instance() or QApplication([str(Path(__file__)), "-platform", "offscreen"])


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def make_icon(size: int = 512, out: Path = Path(__file__).parent / "icon.png") -> None:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = int(size * 0.04)
    radius = int(size * 0.22)
    painter.setBrush(QColor(PRIMARY))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(margin, margin, size - 2 * margin, size - 2 * margin, radius, radius)

    svg_text = (ICONS_DIR / "book-open.svg").read_text(encoding="utf-8").replace("currentColor", "#ffffff")
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    icon_size = size * 0.56
    x = (size - icon_size) / 2
    y = (size - icon_size) / 2
    renderer.render(painter, QRectF(x, y, icon_size, icon_size))
    painter.end()

    pix.save(str(out))
    print(f"Icono guardado en {out} ({size}x{size})")


def make_logo(width: int = 1200, height: int = 360, out: Path = Path(__file__).parent / "logo.png") -> None:
    color = _hex_to_rgb(PRIMARY)
    color_dark = _hex_to_rgb(PRIMARY_HOVER)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    title = "Life & Ministry"
    subtitle = "A S S I S T A N T"

    title_font = ImageFont.truetype(str(FONT_TITLE), int(height * 0.40))
    subtitle_font = ImageFont.truetype(str(FONT_SUBTITLE), int(height * 0.11))

    tb = draw.textbbox((0, 0), title, font=title_font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    sb = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]

    gap = int(height * 0.06)
    block_h = th + gap + sh
    top = (height - block_h) / 2

    tx = (width - tw) / 2 - tb[0]
    ty = top - tb[1]
    draw.text((tx, ty), title, font=title_font, fill=color)

    sx = (width - sw) / 2 - sb[0]
    sy = top + th + gap - sb[1]
    draw.text((sx, sy), subtitle, font=subtitle_font, fill=color_dark)

    img.save(out)
    print(f"Logo guardado en {out} ({width}x{height})")


if __name__ == "__main__":
    make_icon()
    make_logo()
