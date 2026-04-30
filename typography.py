"""Centralized type system for Declare.

Three families:
  Cinzel  — display (titles, hero text, declare moments)
  Playfair Display — headers, section labels, large card numbers
  Inter   — UI body, buttons, log, captions

Falls back to system fonts if the bundled TTFs are missing.
All font sizes flow through `theme.text_scale` so the accessibility text-scale
control affects every label.
"""
import os
import pygame

import theme


_HERE = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_HERE, "assets", "fonts")

DISPLAY_TTF = os.path.join(_FONTS_DIR, "Cinzel-Regular.ttf")
HEADER_TTF = os.path.join(_FONTS_DIR, "PlayfairDisplay-Regular.ttf")
HEADER_ITALIC_TTF = os.path.join(_FONTS_DIR, "PlayfairDisplay-Italic.ttf")
BODY_TTF = os.path.join(_FONTS_DIR, "Inter-Regular.ttf")

_CACHE = {}


def _scaled(size):
    s = theme.active().text_scale
    return max(8, int(size * s))


def _load(path, size, sysfallback, bold=False, italic=False):
    key = (path, size, sysfallback, bold, italic)
    if key in _CACHE:
        return _CACHE[key]
    f = None
    if path and os.path.exists(path):
        try:
            f = pygame.font.Font(path, size)
            if bold:
                f.set_bold(True)
            if italic:
                f.set_italic(True)
        except (pygame.error, OSError):
            f = None
    if f is None:
        f = pygame.font.SysFont(sysfallback, size, bold=bold, italic=italic)
    _CACHE[key] = f
    return f


def display(size):
    return _load(DISPLAY_TTF, _scaled(size), "georgia,serif", bold=False)


def display_bold(size):
    return _load(DISPLAY_TTF, _scaled(size), "georgia,serif", bold=True)


def header(size):
    return _load(HEADER_TTF, _scaled(size), "georgia,serif", bold=False)


def header_bold(size):
    return _load(HEADER_TTF, _scaled(size), "georgia,serif", bold=True)


def header_italic(size):
    return _load(HEADER_ITALIC_TTF, _scaled(size), "georgia,serif", italic=True)


def body(size):
    return _load(BODY_TTF, _scaled(size), "segoeui,arial", bold=False)


def body_bold(size):
    return _load(BODY_TTF, _scaled(size), "segoeui,arial", bold=True)


def body_italic(size):
    return _load(BODY_TTF, _scaled(size), "segoeui,arial", italic=True)


def small(size):
    return _load(BODY_TTF, _scaled(size), "segoeui,arial", bold=False)


def small_bold(size):
    return _load(BODY_TTF, _scaled(size), "segoeui,arial", bold=True)


def render_with_letter_spacing(font, text, color, spacing_px=0):
    """Render text with extra horizontal space between glyphs.
    Useful for the deco display title where natural Cinzel spacing
    is already wide; spacing_px nudges further."""
    if spacing_px == 0:
        return font.render(text, True, color)
    surfs = [font.render(c, True, color) for c in text]
    h = max((s.get_height() for s in surfs), default=font.get_height())
    w = sum(s.get_width() for s in surfs) + spacing_px * (len(text) - 1)
    out = pygame.Surface((max(1, w), h), pygame.SRCALPHA)
    x = 0
    for s in surfs:
        out.blit(s, (x, 0))
        x += s.get_width() + spacing_px
    return out


def invalidate():
    _CACHE.clear()
