"""TutorialDirector — interactive 8-chapter onboarding.

Sits parallel to the live game state. Each chapter drives a scripted scenario
with a goal predicate ("the player must perform action X"). The director
displays a captioned highlight ring around the relevant UI element and
advances when the predicate is satisfied.

Runs against a normal GameManager + scripted-deck. Doesn't change game rules.
"""
import math
import pygame
from dataclasses import dataclass, field

import theme
import audio
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DECK_CENTER, DRAWN_CARD_POS, DISCARD_POS,
    ACTION_BAR_Y, ACTION_BAR_H,
)


@dataclass
class TutorialStep:
    title: str
    body: str
    target: str = ""
    advance_on: str = "continue"
    advance_predicate: callable = None
    sfx: str = ""
    auto_advance_after: float = 0.0


CHAPTERS = [
    TutorialStep(
        title="Welcome to Declare.",
        body="A casino-style card game of memory, bluffing, and "
             "lightning-fast reactions. Press SPACE or click "
             "Continue to begin.",
        target="center",
        advance_on="continue",
    ),
    TutorialStep(
        title="Your Hand",
        body="Each round you hold a small hand of cards face down. "
             "You can only see cards you have peeked at. The player "
             "with the lowest hand-total wins.",
        target="player_hand",
        advance_on="continue",
    ),
    TutorialStep(
        title="The Draw",
        body="On your turn, draw a card from the deck. You can play it, "
             "swap it into your hand, discard it, or use its power. "
             "Try clicking the deck or pressing 1.",
        target="deck",
        advance_on="draw",
        sfx="draw",
    ),
    TutorialStep(
        title="Suits & Values",
        body="Aces = 1. Number cards = face value. J/Q = 11/12. "
             "Red Kings = 13 (high). Black Kings = 0 — keep these. "
             "Lowest sum wins.",
        target="center",
        advance_on="continue",
    ),
    TutorialStep(
        title="Powers",
        body="Cards 7-K carry powers. Peek at your own card, peek at "
             "opponents, swap cards, or skip a turn. The drawn card's "
             "power lights up below the card.",
        target="drawn_card",
        advance_on="continue",
    ),
    TutorialStep(
        title="Pairing",
        body="If you draw a rank that matches a card you've seen, "
             "you can pair them — both go to the discard pile. Pairing "
             "an opponent's card forces them to take one of yours.",
        target="discard",
        advance_on="continue",
    ),
    TutorialStep(
        title="Reactive Pairing",
        body="When ANY player plays a card, others have a brief window "
             "to drop a matching rank. Wrong card = penalty draw. "
             "Watch the gold banner.",
        target="center",
        advance_on="continue",
    ),
    TutorialStep(
        title="Declare to Win",
        body="When your hand-total is 10 or less, click Declare to "
             "end the round. If you have the lowest score, you win. "
             "If not, your score is doubled. Bold but risky.",
        target="declare_button",
        advance_on="continue",
    ),
    TutorialStep(
        title="You're Ready.",
        body="That's the basics. Press Continue to return to the menu "
             "and start a real match. Good luck at the table.",
        target="center",
        advance_on="continue",
        sfx="achievement",
    ),
]


class TutorialDirector:
    def __init__(self):
        self.active = False
        self.chapter = 0
        self._fade = 0.0
        self._title_font = None
        self._body_font = None
        self._small_font = None
        self._button_rect = pygame.Rect(0, 0, 220, 50)
        self._step_just_advanced = False
        self._satisfied = False
        self._continue_rect = None
        self._skip_rect = None

    def _ensure_fonts(self):
        if self._title_font is None:
            import typography as typo
            self._title_font = typo.display_bold(30)
            self._body_font = typo.body(20)
            self._small_font = typo.body(14)

    def start(self):
        self.active = True
        self.chapter = 0
        self._fade = 0.0
        self._satisfied = False
        audio.play("ui_open")

    def stop(self):
        self.active = False

    def update(self, dt):
        if not self.active:
            return
        self._fade = min(1.0, self._fade + dt * 3.0)

    def current(self):
        if 0 <= self.chapter < len(CHAPTERS):
            return CHAPTERS[self.chapter]
        return None

    def advance(self):
        if not self.active:
            return False
        step = self.current()
        if step and step.sfx:
            audio.play(step.sfx)
        self.chapter += 1
        self._fade = 0.0
        self._satisfied = False
        if self.chapter >= len(CHAPTERS):
            self.active = False
            return True
        return False

    def notify_action(self, action_name):
        step = self.current()
        if not step:
            return
        if step.advance_on == action_name:
            self._satisfied = True

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.stop()
                return "skip"
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return "advance"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._continue_rect and self._continue_rect.collidepoint(event.pos):
                return "advance"
            if self._skip_rect and self._skip_rect.collidepoint(event.pos):
                self.stop()
                return "skip"
        return None

    def draw(self, screen):
        if not self.active:
            return
        self._ensure_fonts()
        step = self.current()
        if not step:
            return
        th = theme.active()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(140 * self._fade)))
        screen.blit(overlay, (0, 0))

        target = step.target
        ring_rect = self._target_rect(target)
        if ring_rect is not None:
            self._draw_highlight(screen, ring_rect)

        panel_w, panel_h = 720, 220
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        panel_y = SCREEN_HEIGHT - panel_h - 60
        if target == "deck" or target == "discard" or target == "drawn_card":
            panel_y = SCREEN_HEIGHT - panel_h - 60
        if target == "declare_button":
            panel_y = 100
        if target == "player_hand":
            panel_y = 80

        slide = int((1 - self._fade) * 30)
        panel_y -= slide

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*th.panel_bg, 235), panel.get_rect(), border_radius=14)
        pygame.draw.rect(panel, th.brass_500, panel.get_rect(), 2, border_radius=14)
        screen.blit(panel, (panel_x, panel_y))

        chapter_label = f"Chapter {self.chapter + 1} / {len(CHAPTERS)}"
        cl_surf = self._small_font.render(chapter_label, True, th.brass_300)
        screen.blit(cl_surf, (panel_x + 20, panel_y + 14))

        title_surf = self._title_font.render(step.title, True, th.brass_300)
        screen.blit(title_surf, (panel_x + 20, panel_y + 40))

        body_lines = self._wrap(step.body, panel_w - 40)
        for i, line in enumerate(body_lines):
            surf = self._body_font.render(line, True, th.text_white)
            screen.blit(surf, (panel_x + 20, panel_y + 90 + i * 28))

        cont_label = "Continue" if step.advance_on != "continue" else "Continue"
        if step.advance_on != "continue" and not self._satisfied:
            cont_label = "Try the highlighted action"
        bw, bh = 200, 38
        self._continue_rect = pygame.Rect(panel_x + panel_w - bw - 20,
                                          panel_y + panel_h - bh - 18, bw, bh)
        c_color = th.signal_go if (self._satisfied or step.advance_on == "continue") else th.cancel_gray
        pygame.draw.rect(screen, c_color, self._continue_rect, border_radius=8)
        pygame.draw.rect(screen, th.brass_500, self._continue_rect, 2, border_radius=8)
        cs = self._body_font.render(cont_label, True, th.text_white)
        screen.blit(cs, cs.get_rect(center=self._continue_rect.center))

        sw, sh = 100, 34
        self._skip_rect = pygame.Rect(panel_x + 20, panel_y + panel_h - sh - 20, sw, sh)
        pygame.draw.rect(screen, (60, 60, 60), self._skip_rect, border_radius=6)
        pygame.draw.rect(screen, th.brass_700, self._skip_rect, 1, border_radius=6)
        sk = self._small_font.render("Skip", True, th.text_dim)
        screen.blit(sk, sk.get_rect(center=self._skip_rect.center))

        keys_hint = self._small_font.render("Space / Enter to continue, Esc to skip",
                                             True, th.text_muted)
        screen.blit(keys_hint, (panel_x + 130, panel_y + panel_h - 30))

    def _target_rect(self, target):
        if target == "deck":
            cx, cy = DECK_CENTER
            return pygame.Rect(cx - 60, cy - 80, 120, 160)
        if target == "discard":
            cx, cy = DISCARD_POS
            return pygame.Rect(cx - 60, cy - 80, 120, 160)
        if target == "drawn_card":
            cx, cy = DRAWN_CARD_POS
            return pygame.Rect(cx - 60, cy - 80, 120, 160)
        if target == "declare_button":
            return pygame.Rect(SCREEN_WIDTH // 2 - 200, ACTION_BAR_Y - 4, 400, ACTION_BAR_H + 8)
        if target == "player_hand":
            return pygame.Rect(280, 620, 1040, 180)
        return None

    def _draw_highlight(self, screen, rect):
        th = theme.active()
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.6 + 0.4 * math.sin(t * 3.5)
        glow_surf = pygame.Surface((rect.width + 60, rect.height + 60), pygame.SRCALPHA)
        for i in range(20, 0, -1):
            a = int(15 * pulse * (i / 20))
            pygame.draw.rect(glow_surf, (*th.brass_300, a),
                             pygame.Rect(30 - i, 30 - i, rect.width + i * 2, rect.height + i * 2),
                             border_radius=12 + i)
        screen.blit(glow_surf, (rect.x - 30, rect.y - 30), special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(screen, th.brass_300, rect, 3, border_radius=10)

    def _wrap(self, text, max_w):
        words = text.split()
        lines = []
        current = ""
        for w in words:
            test = current + (" " if current else "") + w
            if self._body_font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines


class FirstLaunchSplash:
    """One-time splash on first run, offering tutorial."""
    def __init__(self):
        self._fade = 0.0
        self.active = False
        self._title_font = None
        self._body_font = None
        self._btn_font = None
        self._tutorial_rect = None
        self._skip_rect = None

    def show(self):
        self.active = True
        self._fade = 0.0

    def update(self, dt):
        if self.active:
            self._fade = min(1.0, self._fade + dt * 2.5)

    def _ensure(self):
        if self._title_font is None:
            import typography as typo
            self._title_font = typo.display_bold(56)
            self._body_font = typo.header_italic(22)
            self._btn_font = typo.body_bold(22)

    def draw(self, screen):
        if not self.active:
            return
        self._ensure()
        th = theme.active()
        screen.fill(th.felt_rim)

        # lamp glow removed

        title = self._title_font.render("Welcome to Declare", True, th.brass_300)
        title.set_alpha(int(255 * self._fade))
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 280)))

        body = "First time at the table?"
        body_surf = self._body_font.render(body, True, th.text_white)
        body_surf.set_alpha(int(255 * self._fade))
        screen.blit(body_surf, body_surf.get_rect(center=(SCREEN_WIDTH // 2, 360)))

        body2 = "We can walk you through the rules in five minutes."
        body2_surf = self._body_font.render(body2, True, th.text_dim)
        body2_surf.set_alpha(int(255 * self._fade))
        screen.blit(body2_surf, body2_surf.get_rect(center=(SCREEN_WIDTH // 2, 396)))

        bw, bh = 280, 56
        cx = SCREEN_WIDTH // 2
        self._tutorial_rect = pygame.Rect(cx - bw - 20, 500, bw, bh)
        self._skip_rect = pygame.Rect(cx + 20, 500, bw, bh)

        pygame.draw.rect(screen, th.signal_go, self._tutorial_rect, border_radius=10)
        pygame.draw.rect(screen, th.brass_500, self._tutorial_rect, 2, border_radius=10)
        ts = self._btn_font.render("Start Tutorial", True, th.text_white)
        screen.blit(ts, ts.get_rect(center=self._tutorial_rect.center))

        pygame.draw.rect(screen, (60, 60, 60), self._skip_rect, border_radius=10)
        pygame.draw.rect(screen, th.brass_700, self._skip_rect, 2, border_radius=10)
        ss = self._btn_font.render("Skip — I know how to play", True, th.text_white)
        screen.blit(ss, ss.get_rect(center=self._skip_rect.center))

    def handle_event(self, event):
        if not self.active:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._tutorial_rect and self._tutorial_rect.collidepoint(event.pos):
                self.active = False
                return "tutorial"
            if self._skip_rect and self._skip_rect.collidepoint(event.pos):
                self.active = False
                return "skip"
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.active = False
                return "tutorial"
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return "skip"
        return None
