"""Game feel layer: camera shake, time-warp slow-mo, edge flashes.

Owned by main, queried each frame. All effects are budgeted: shake amplitude
clamps so simultaneous events don't compound into nausea; slow-mo can't drop
below 30% real-time. Disabled cleanly when motion_scale=0 (reduced motion).
"""
import math
import random
import pygame

import theme
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class CameraShake:
    def __init__(self):
        self.amp = 0.0
        self.freq = 24.0
        self.time = 0.0
        self.duration = 0.0
        self.elapsed = 0.0

    def kick(self, amp=4.0, duration=0.25, freq=24.0):
        ms = theme.active().motion_scale
        amp = amp * ms
        if amp <= 0:
            return
        self.amp = max(self.amp, amp)
        self.duration = max(self.duration - self.elapsed, duration)
        self.elapsed = 0.0
        self.freq = freq

    def update(self, dt):
        self.time += dt
        if self.duration <= 0:
            self.amp = 0.0
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.amp = 0.0
            self.duration = 0.0
            self.elapsed = 0.0

    def offset(self):
        if self.amp <= 0 or self.duration <= 0:
            return (0, 0)
        falloff = max(0.0, 1.0 - self.elapsed / self.duration)
        a = self.amp * falloff
        ox = math.sin(self.time * self.freq * 2 * math.pi) * a
        oy = math.cos(self.time * (self.freq * 1.13) * 2 * math.pi) * a
        return (int(ox), int(oy))


class TimeWarp:
    """Lets gameplay-affecting systems get a scaled dt for cinematic moments."""
    def __init__(self):
        self.target = 1.0
        self.current = 1.0
        self.recovery = 1.5

    def slowmo(self, factor=0.35, duration=1.2):
        self.target = factor
        self._until = pygame.time.get_ticks() / 1000.0 + duration

    def update(self, dt_real):
        now = pygame.time.get_ticks() / 1000.0
        if hasattr(self, "_until") and now >= self._until:
            self.target = 1.0
        if self.current < self.target:
            self.current = min(self.target, self.current + dt_real * self.recovery)
        elif self.current > self.target:
            self.current = max(self.target, self.current - dt_real * self.recovery)
        return self.current


class EdgeFlash:
    """Glowing inner-frame outline drawn on top — used for reaction-window open
    and other 'something just happened' moments."""
    def __init__(self):
        self.life = 0.0
        self.max_life = 0.0
        self.color = (232, 195, 110)
        self.thickness = 24

    def fire(self, color=None, duration=0.5, thickness=28):
        ms = theme.active().motion_scale
        if ms <= 0.05:
            return
        self.life = duration * ms
        self.max_life = self.life
        self.color = color or theme.active().brass_300
        self.thickness = thickness

    def update(self, dt):
        if self.life > 0:
            self.life -= dt

    def draw(self, screen):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        alpha = int(140 * t)
        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(self.thickness):
            inset = i
            ring_alpha = int(alpha * (1.0 - i / self.thickness))
            if ring_alpha <= 0:
                continue
            pygame.draw.rect(
                flash, (*self.color, ring_alpha),
                pygame.Rect(inset, inset, SCREEN_WIDTH - 2 * inset, SCREEN_HEIGHT - 2 * inset),
                1,
            )
        screen.blit(flash, (0, 0))


class Vignette:
    """Subtle radial darkening at the edges of the screen.
    Drawn always; intensity bumps during declare-mode for theatrical push-in."""
    def __init__(self):
        self.intensity = 0.45
        self._cached = None
        self._cached_intensity = None

    def _build(self, intensity):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_d = math.hypot(cx, cy)
        steps = 30
        for i in range(steps):
            t = i / (steps - 1)
            r = int(max_d * (1.0 - t * 0.4))
            a = int(255 * intensity * (t ** 2.2))
            pygame.draw.circle(surf, (0, 0, 0, a), (cx, cy), r)
        return surf

    def get(self, intensity=None):
        intensity = intensity if intensity is not None else self.intensity
        if self._cached is None or abs((self._cached_intensity or 0) - intensity) > 0.02:
            self._cached = self._build(intensity)
            self._cached_intensity = intensity
        return self._cached


class LampGlow:
    """Slow moving warm-light ray across the felt for atmosphere.
    Very subtle — meant to add ambience, not obscure gameplay."""
    def __init__(self):
        self.t = 0.0
        self.speed = 1.0 / 60.0
        self._cached = None

    def update(self, dt):
        self.t = (self.t + dt * self.speed) % 1.0

    def draw(self, screen):
        if not theme.active().particles_enabled:
            return
        if theme.active().motion_scale <= 0.1:
            return
        col = theme.active().lamp_glow
        center_x = int(SCREEN_WIDTH * (0.25 + 0.5 * self.t))
        center_y = SCREEN_HEIGHT // 2
        radius = 220
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for i in range(12, 0, -1):
            t = i / 12
            r = int(radius * t)
            a = int(6 * (1.0 - t))
            if a <= 0:
                continue
            pygame.draw.circle(glow, (*col, a), (radius, radius), r)
        screen.blit(glow, (center_x - radius, center_y - radius))


class DealAnimation:
    """Choreographed deal: cards arc one-by-one from the deck to each seat."""
    def __init__(self):
        self.steps = []
        self.current = 0
        self.elapsed = 0.0
        self.running = False
        self.per_card = 0.16

    def start(self, slots):
        """slots: list of (seat_index, slot_index, target_pos)."""
        self.steps = list(slots)
        self.current = 0
        self.elapsed = 0.0
        self.running = bool(slots)

    def update(self, dt):
        if not self.running:
            return None
        self.elapsed += dt
        if self.elapsed >= self.per_card:
            self.elapsed = 0.0
            if self.current >= len(self.steps):
                self.running = False
                return None
            step = self.steps[self.current]
            self.current += 1
            return step
        return None
