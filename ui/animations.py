import math
import pygame
from enum import Enum

from config import SCREEN_WIDTH, SCREEN_HEIGHT, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, DISCARD_POS

from game.card import Card


def _get_font(size, bold=False):
    import typography as typo
    return typo.body_bold(size) if bold else typo.body(size)


class VisualEventType(Enum):
    CARD_SLIDE = "card_slide"
    CARD_ARC = "card_arc"
    CARD_FLIP_ARC = "card_flip_arc"
    CARD_FADE_OUT = "card_fade_out"
    CARD_LIFT = "card_lift"
    NOTIFICATION_TEXT = "notification_text"
    SCREEN_FLASH = "screen_flash"


class VisualEvent:
    def __init__(self, event_type, start_pos, end_pos, card=None,
                 duration=0.4, arc_height=0, flip_at_peak=False,
                 face_up_at_end=False, on_complete=None, text="",
                 text_color=(255, 215, 0), start_face_up=False,
                 start_scale=1.0, end_scale=1.0):
        self.event_type = event_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.card = card
        self.duration = duration
        self.arc_height = arc_height
        self.flip_at_peak = flip_at_peak
        self.face_up_at_end = face_up_at_end
        self.on_complete = on_complete
        self.text = text
        self.text_color = text_color
        self.start_face_up = start_face_up
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.progress = 0.0
        self.is_complete = False

    def update(self, dt):
        if self.is_complete:
            return
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            self.is_complete = True
            if self.on_complete is not None:
                self.on_complete()

    def interpolate_position(self):
        t = ease_out_cubic(self.progress)
        if self.arc_height == 0:
            x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
            y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        else:
            mx = (self.start_pos[0] + self.end_pos[0]) / 2
            my = (self.start_pos[1] + self.end_pos[1]) / 2 - self.arc_height
            x = (1 - t) ** 2 * self.start_pos[0] + 2 * (1 - t) * t * mx + t ** 2 * self.end_pos[0]
            y = (1 - t) ** 2 * self.start_pos[1] + 2 * (1 - t) * t * my + t ** 2 * self.end_pos[1]
        return (x, y)

    def current_scale(self):
        t = ease_out_cubic(self.progress)
        return self.start_scale + (self.end_scale - self.start_scale) * t

    def current_alpha(self):
        if self.event_type == VisualEventType.CARD_FADE_OUT:
            return max(0, int(255 * (1.0 - self.progress)))
        return 255

    def should_show_face_up(self):
        if self.start_face_up:
            return True
        if self.flip_at_peak and self.progress >= 0.5:
            return True
        if self.face_up_at_end and self.progress >= 0.7:
            return True
        return False

    def horizontal_stretch(self):
        if self.flip_at_peak:
            if self.progress < 0.5:
                return abs(math.cos(self.progress * math.pi))
            else:
                flip_t = (self.progress - 0.5) * 2
                return abs(math.cos(flip_t * math.pi / 2))
        return 1.0


class AnimationQueue:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)

    def update(self, dt):
        for event in self.events:
            event.update(dt)
        self.events = [e for e in self.events if not e.is_complete]

    def is_animating(self):
        return len(self.events) > 0

    def draw(self, screen, renderer):
        for event in self.events:
            _draw_event(screen, renderer, event)


def _draw_event(screen, renderer, event):
    if event.event_type == VisualEventType.NOTIFICATION_TEXT:
        _draw_notification(screen, renderer, event)
        return

    if event.event_type == VisualEventType.SCREEN_FLASH:
        _draw_flash(screen, event)
        return

    pos = event.interpolate_position()
    x, y = pos
    scale = event.current_scale()
    alpha = event.current_alpha()
    stretch = event.horizontal_stretch()

    card_w = int(CARD_WIDTH * scale * stretch)
    card_h = int(CARD_HEIGHT * scale)
    if card_w <= 0 or card_h <= 0:
        return

    cx = int(x - card_w / 2)
    cy = int(y - card_h / 2)

    card_surface = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    rect = pygame.Surface((card_w, card_h), pygame.SRCALPHA).get_rect()

    show_face = event.should_show_face_up()

    if show_face and event.card is not None:
        _render_card_face_to_surface(renderer, card_surface, event.card, card_w, card_h, alpha)
    else:
        _render_card_back_to_surface(renderer, card_surface, card_w, card_h, alpha)

    if event.event_type == VisualEventType.CARD_LIFT:
        glow_alpha = int(120 * (1.0 - event.progress))
        glow_rect = pygame.Rect(0, 0, card_w + 12, card_h + 12)
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (80, 180, 255, glow_alpha), glow_surf.get_rect(), border_radius=CORNER_RADIUS + 2)
        screen.blit(glow_surf, (cx - 6, cy - 6))

    screen.blit(card_surface, (cx, cy))

    if event.event_type == VisualEventType.CARD_ARC or event.event_type == VisualEventType.CARD_FLIP_ARC:
        if event.progress < 0.9:
            _draw_trail(screen, event)


def _render_card_face_to_surface(renderer, surface, card, w, h, alpha):
    import card_render
    face = card_render.paint_face(card, w, h)
    if alpha < 255:
        scratch = pygame.Surface((w, h), pygame.SRCALPHA)
        scratch.blit(face, (0, 0))
        scratch.set_alpha(alpha)
        surface.blit(scratch, (0, 0))
    else:
        surface.blit(face, (0, 0))


def _render_card_back_to_surface(renderer, surface, w, h, alpha):
    import card_render
    style = getattr(renderer, "_card_back_style", "classic") if renderer else "classic"
    back = card_render.paint_back(style=style, w=w, h=h)
    if alpha < 255:
        scratch = pygame.Surface((w, h), pygame.SRCALPHA)
        scratch.blit(back, (0, 0))
        scratch.set_alpha(alpha)
        surface.blit(scratch, (0, 0))
    else:
        surface.blit(back, (0, 0))


def _draw_trail(screen, event):
    num_dots = 5
    for i in range(num_dots):
        t = max(0.0, event.progress - (i + 1) * 0.06)
        t_ease = ease_out_cubic(t)
        if event.arc_height == 0:
            tx = event.start_pos[0] + (event.end_pos[0] - event.start_pos[0]) * t_ease
            ty = event.start_pos[1] + (event.end_pos[1] - event.start_pos[1]) * t_ease
        else:
            mx = (event.start_pos[0] + event.end_pos[0]) / 2
            my = (event.start_pos[1] + event.end_pos[1]) / 2 - event.arc_height
            tx = (1 - t_ease) ** 2 * event.start_pos[0] + 2 * (1 - t_ease) * t_ease * mx + t_ease ** 2 * event.end_pos[0]
            ty = (1 - t_ease) ** 2 * event.start_pos[1] + 2 * (1 - t_ease) * t_ease * my + t_ease ** 2 * event.end_pos[1]
        dot_alpha = max(0, int(60 * (1.0 - i / num_dots)))
        dot_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (255, 215, 0, dot_alpha), (3, 3), 3)
        screen.blit(dot_surf, (int(tx) - 3, int(ty) - 3))


def _draw_notification(screen, renderer, event):
    if not event.text:
        return
    fade_in = min(event.progress / 0.2, 1.0)
    fade_out = max(0.0, 1.0 - (event.progress - 0.7) / 0.3) if event.progress > 0.7 else 1.0
    alpha = min(fade_in, fade_out)
    font = _get_font(22, bold=True)
    text_surf = font.render(event.text, True, event.text_color)
    bg_surf = pygame.Surface((text_surf.get_width() + 24, text_surf.get_height() + 12), pygame.SRCALPHA)
    bg_surf.fill((0, 0, 0, int(180 * alpha)))
    screen.blit(bg_surf, (int(event.start_pos[0]) - bg_surf.get_width() // 2, int(event.start_pos[1]) - bg_surf.get_height() // 2))
    text_alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
    text_alpha_surf.blit(text_surf, (0, 0))
    text_alpha_surf.set_alpha(int(255 * alpha))
    screen.blit(text_alpha_surf, (int(event.start_pos[0]) - text_surf.get_width() // 2, int(event.start_pos[1]) - text_surf.get_height() // 2))


def _draw_flash(screen, event):
    alpha = max(0, int(80 * (1.0 - event.progress)))
    if alpha <= 0:
        return
    color = event.text_color
    flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    flash_surf.fill((*color, alpha))
    screen.blit(flash_surf, (0, 0))


def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_quad(t):
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2