from enum import Enum
import math

from game.card import Card


class AnimationType(Enum):
    CARD_FLIP = "card_flip"
    CARD_SWAP = "card_swap"
    CARD_DRAW = "card_draw"
    CARD_DISCARD = "card_discard"
    PEEK_REVEAL = "peek_reveal"
    DECLARE = "declare"


class Animation:
    def __init__(self, anim_type: AnimationType, start_pos: tuple, end_pos: tuple, card: Card = None, duration: float = 0.5, on_complete: callable = None):
        self.anim_type = anim_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.card = card
        self.duration = duration
        self.on_complete = on_complete
        self.progress = 0.0
        self.is_complete = False
        self.start_time = 0.0

    def update(self, dt: float):
        if self.is_complete:
            return
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = 1.0
            self.is_complete = True
            if self.on_complete is not None:
                self.on_complete()

    def interpolate_position(self) -> tuple:
        t = ease_out_cubic(self.progress)
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        return (x, y)


class AnimationManager:
    def __init__(self):
        self.animations: list[Animation] = []

    def add(self, animation: Animation):
        self.animations.append(animation)

    def update(self, dt: float):
        for anim in self.animations:
            anim.update(dt)
        self.animations = [a for a in self.animations if not a.is_complete]

    def get_active_count(self) -> int:
        return len(self.animations)

    def is_animating(self) -> bool:
        return len(self.animations) > 0


def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2