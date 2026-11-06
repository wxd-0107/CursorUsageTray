"""Numeric tray icon: black background, green-to-red by usage."""

from __future__ import annotations

import colorsys

from PIL import Image, ImageDraw, ImageFont

# Taskbar buttons use a 32px slot. Draw larger so Windows can scale a sharp icon down.
ICON_SIZE = 64
# Semibold/regular — thicker than Semilight, lighter than Impact.
_FONT_FILES = ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "segoeui.ttf", "arial.ttf")


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_FILES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def usage_color(pct: float) -> tuple[int, int, int, int]:
    """0% green -> 50% yellow -> 100% red."""
    t = max(0.0, min(100.0, float(pct))) / 100.0
    hue = 120.0 * (1.0 - t)
    red, green, blue = colorsys.hsv_to_rgb(hue / 360.0, 0.92, 1.0)
    return int(red * 255), int(green * 255), int(blue * 255), 255


def icon_label(pct: float | None) -> str:
    """One decimal when below 100; 100 has no room for a fractional digit."""
    if pct is None:
        return "--"
    value = max(0.0, min(100.0, float(pct)))
    if value >= 99.95:
        return "100"
    return f"{value:.1f}"


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int, tuple[int, int, int, int]]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_w: int,
    max_h: int,
) -> tuple[ImageFont.ImageFont, tuple[int, int, tuple[int, int, int, int]]]:
    lo, hi = 6, max(6, max_h * 2)
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        font = _load_font(mid)
        tw, th, _bbox = _text_size(draw, text, font)
        if tw <= max_w and th <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    font = _load_font(best)
    return font, _text_size(draw, text, font)


def _blit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    bbox: tuple[int, int, int, int],
    x: float,
    y: float,
    color: tuple[int, int, int, int],
) -> None:
    draw.text((x - bbox[0], y - bbox[1]), text, fill=color, font=font)


def build_tray_icon(
    text: str,
    *,
    size: int = ICON_SIZE,
    pct: float | None = None,
    dim: bool = False,
) -> Image.Image:
    """Fill the tray slot. Integer digits stay large; the decimal sits at the lower right."""
    raw = (text or "--").strip()
    whole = raw
    frac = ""
    if "." in raw:
        whole, frac = raw.split(".", 1)
        frac = "".join(ch for ch in frac if ch.isdigit())[:1]
        whole = whole or "0"

    img = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    if dim or pct is None:
        color = (176, 176, 176, 255)
    else:
        color = usage_color(pct)

    if not frac:
        font, (tw, th, bbox) = _fit_font(draw, whole, size, size)
        _blit_text(draw, whole, font, bbox, (size - tw) / 2, (size - th) / 2, color)
        return img

    # Decimal digit ~75% of integer height; share one row so ".d" stays readable.
    pad = max(1, size // 32)
    max_w = size - pad * 2
    max_h = size - pad * 2
    frac_scale = 0.75
    lo, hi = 6, max_h
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        int_font = _load_font(mid)
        frac_font = _load_font(max(6, int(mid * frac_scale)))
        int_tw, int_th, _ = _text_size(draw, whole, int_font)
        frac_tw, frac_th, _ = _text_size(draw, frac, frac_font)
        dot = max(2, int(mid * 0.12))
        gap = max(1, mid // 18)
        total_w = int_tw + gap + dot + gap + frac_tw
        total_h = max(int_th, frac_th)
        if total_w <= max_w and total_h <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    int_font = _load_font(best)
    frac_font = _load_font(max(6, int(best * frac_scale)))
    int_tw, int_th, int_bbox = _text_size(draw, whole, int_font)
    frac_tw, frac_th, frac_bbox = _text_size(draw, frac, frac_font)
    dot = max(2, int(best * 0.12))
    gap = max(1, best // 18)
    total_w = int_tw + gap + dot + gap + frac_tw
    total_h = max(int_th, frac_th)
    x = (size - total_w) / 2
    y_base = (size - total_h) / 2

    _blit_text(draw, whole, int_font, int_bbox, x, y_base + (total_h - int_th) / 2, color)
    cursor = x + int_tw + gap
    dot_y = y_base + total_h - dot - max(1, int(total_h * 0.06))
    draw.rectangle((cursor, dot_y, cursor + dot, dot_y + dot), fill=color)
    cursor += dot + gap
    _blit_text(draw, frac, frac_font, frac_bbox, cursor, y_base + (total_h - frac_th) / 2, color)
    return img
