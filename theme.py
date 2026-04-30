"""Theme tokens for Declare.

Replaces flat literal RGB tuples scattered across config.py / renderer.py.
A single Theme instance is held by main.py and read by every rendering call.
Swapping themes (default / colorblind / high-contrast) reskins the whole game.
"""
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Theme:
    name: str = "Parlor"

    felt_deep: tuple = (26, 58, 46)
    felt_mid: tuple = (44, 92, 69)
    felt_rim: tuple = (14, 31, 24)
    lamp_glow: tuple = (255, 220, 140)

    paper_warm: tuple = (244, 236, 216)
    paper_edge: tuple = (190, 178, 150)
    ink_red: tuple = (178, 34, 34)
    ink_black: tuple = (26, 26, 26)
    card_back_a: tuple = (24, 36, 78)
    card_back_b: tuple = (54, 78, 140)
    card_back_motif: tuple = (220, 175, 90)

    brass_100: tuple = (255, 231, 168)
    brass_300: tuple = (232, 195, 110)
    brass_500: tuple = (188, 145, 64)
    brass_700: tuple = (124, 92, 38)
    brass_900: tuple = (60, 42, 18)

    signal_go: tuple = (79, 180, 119)
    signal_stop: tuple = (212, 72, 72)
    signal_warn: tuple = (224, 165, 38)
    signal_info: tuple = (111, 207, 227)
    you_cyan: tuple = (111, 207, 227)

    text_white: tuple = (244, 244, 240)
    text_dim: tuple = (170, 170, 170)
    text_muted: tuple = (130, 130, 130)
    panel_bg: tuple = (15, 15, 15)
    panel_bg_alpha: int = 220
    panel_border: tuple = (60, 60, 60)
    overlay: tuple = (0, 0, 0)

    declare_red: tuple = (212, 72, 72)
    declare_red_hi: tuple = (240, 102, 102)
    swap_green: tuple = (40, 130, 60)
    swap_green_hi: tuple = (60, 170, 80)
    peek_blue: tuple = (70, 140, 220)
    peek_blue_hi: tuple = (100, 170, 250)
    discard_orange: tuple = (200, 120, 30)
    discard_orange_hi: tuple = (230, 150, 50)
    pair_teal: tuple = (40, 140, 160)
    pair_teal_hi: tuple = (60, 170, 190)
    cancel_gray: tuple = (100, 100, 100)
    cancel_gray_hi: tuple = (140, 140, 140)

    text_scale: float = 1.0
    motion_scale: float = 1.0
    particles_enabled: bool = True
    high_contrast: bool = False

    @property
    def gold(self):
        return self.brass_300

    @property
    def empty_slot(self):
        return (60, 90, 60)

    @property
    def known_tint(self):
        return (*self.brass_300, 40)


THEME_DEFAULT = Theme()

THEME_DEUTAN = replace(
    THEME_DEFAULT,
    name="Color-blind (Deutan)",
    ink_red=(0, 90, 200),
    declare_red=(0, 90, 200),
    declare_red_hi=(40, 130, 240),
    signal_stop=(0, 90, 200),
    signal_go=(220, 165, 40),
    swap_green=(220, 165, 40),
    swap_green_hi=(245, 195, 70),
)

THEME_PROTAN = replace(
    THEME_DEFAULT,
    name="Color-blind (Protan)",
    ink_red=(70, 110, 220),
    declare_red=(70, 110, 220),
    declare_red_hi=(110, 150, 245),
    signal_stop=(70, 110, 220),
    signal_go=(220, 175, 60),
    swap_green=(220, 175, 60),
    swap_green_hi=(240, 200, 90),
)

THEME_TRITAN = replace(
    THEME_DEFAULT,
    name="Color-blind (Tritan)",
    ink_red=(220, 60, 80),
    declare_red=(220, 60, 80),
    signal_stop=(220, 60, 80),
    signal_go=(50, 170, 170),
    swap_green=(50, 170, 170),
    swap_green_hi=(80, 200, 200),
    peek_blue=(190, 130, 220),
    peek_blue_hi=(220, 160, 245),
)

THEME_HIGH_CONTRAST = replace(
    THEME_DEFAULT,
    name="High Contrast",
    felt_deep=(0, 0, 0),
    felt_mid=(20, 20, 20),
    felt_rim=(0, 0, 0),
    lamp_glow=(255, 255, 255),
    paper_warm=(255, 255, 255),
    paper_edge=(0, 0, 0),
    ink_red=(255, 0, 0),
    ink_black=(0, 0, 0),
    card_back_a=(0, 0, 80),
    card_back_b=(0, 0, 160),
    card_back_motif=(255, 255, 0),
    brass_300=(255, 255, 0),
    brass_500=(255, 230, 0),
    text_white=(255, 255, 255),
    text_dim=(220, 220, 220),
    panel_bg=(0, 0, 0),
    panel_border=(255, 255, 255),
    high_contrast=True,
)

THEMES = {
    "default": THEME_DEFAULT,
    "deutan": THEME_DEUTAN,
    "protan": THEME_PROTAN,
    "tritan": THEME_TRITAN,
    "high_contrast": THEME_HIGH_CONTRAST,
}

THEME_LABELS = {
    "default": "Parlor",
    "deutan": "CB - Deutan",
    "protan": "CB - Protan",
    "tritan": "CB - Tritan",
    "high_contrast": "High Contrast",
}


def get_theme(key: str) -> Theme:
    return THEMES.get(key, THEME_DEFAULT)


_active = THEME_DEFAULT


def set_active(theme_or_key):
    global _active
    if isinstance(theme_or_key, Theme):
        _active = theme_or_key
    else:
        _active = get_theme(theme_or_key)


def active() -> Theme:
    return _active


def with_text_scale(scale: float) -> Theme:
    return replace(_active, text_scale=scale)


def apply_text_scale(scale: float):
    global _active
    _active = replace(_active, text_scale=scale)


def apply_motion_scale(scale: float):
    global _active
    _active = replace(_active, motion_scale=scale)


def apply_particles(enabled: bool):
    global _active
    _active = replace(_active, particles_enabled=enabled)
