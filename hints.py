"""Hint engine: three tiers of progressive guidance.

Tier 1 — Affordance hints: dim suboptimal action buttons, gently pulse the
defensible one, label the drawn card's power.

Tier 2 — Memory aids: tinted gold known-card markers (rank-coded for 30s,
fading back to neutral), recently-discarded fan, opponent card-count chips.

Tier 3 — Coach mode (off by default, opt-in): post-turn replay text,
"you discarded the 9 — could have paired with slot 2".

Never shows: opponent unknown cards, declare-will-win predictions, deck top.
"""
import math
import time
import pygame

import theme
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DISCARD_POS, CARD_WIDTH, CARD_HEIGHT,
    POWER_LABELS, POWER_COLORS,
)


class HintEngine:
    def __init__(self, settings):
        self.settings = settings
        self._known_seen_at = {}
        self._coach_messages = []
        self._coach_until = 0.0

    def tier(self):
        return getattr(self.settings, "hint_tier", 1)

    def coach_on(self):
        return getattr(self.settings, "coach_mode", False)

    def evaluate_actions(self, gm, action_buttons, ai_decider=None):
        """Return (dim_keys, pulse_keys) sets for the action bar."""
        if self.tier() < 1 or not action_buttons:
            return set(), set()
        dim, pulse = set(), set()
        cp = gm.current_player()
        if not cp.is_human or ai_decider is None:
            return set(), set()

        drawn = gm.drawn_card
        legal = list(action_buttons.keys())

        recommended = None
        try:
            if drawn is None:
                pass
            else:
                decision = ai_decider.choose_action(drawn)
                action_key = decision.get("action")
                if action_key in legal:
                    recommended = action_key
        except Exception:
            recommended = None

        if recommended:
            pulse.add(recommended)
            for k in legal:
                if k != recommended and k not in ("declare", "draw"):
                    if k in ("discard", "swap") and recommended in ("pair_own", "play_power"):
                        dim.add(k)
        return dim, pulse

    def power_label_for_drawn(self, gm):
        if self.tier() < 1:
            return None, None
        if not gm.drawn_card or not gm.drawn_card.power:
            return None, None
        label = POWER_LABELS.get(gm.drawn_card.power, gm.drawn_card.power)
        color = POWER_COLORS.get(gm.drawn_card.power, (200, 200, 200))
        return label, color

    def known_marker_tint(self, slot_index, card):
        """Tier 2 memory aid: gold marker tinted by rank for 30s after seeing."""
        if self.tier() < 2:
            return None
        key = (id(card), slot_index, card.rank)
        now = time.monotonic()
        seen_at = self._known_seen_at.get(key)
        if seen_at is None:
            self._known_seen_at[key] = now
            seen_at = now
        age = now - seen_at
        if age > 30:
            return None
        fade = max(0.0, 1.0 - age / 30.0)
        if card.is_red:
            base = (220, 80, 80)
        else:
            base = (200, 200, 220)
        gold = (232, 195, 110)
        r = int(gold[0] * (1 - fade) + base[0] * fade)
        g = int(gold[1] * (1 - fade) + base[1] * fade)
        b = int(gold[2] * (1 - fade) + base[2] * fade)
        return (r, g, b)

    def draw_recent_discards(self, screen, discards):
        if self.tier() < 2:
            return
        if not discards:
            return
        last_three = discards[-3:]
        if len(last_three) < 2:
            return
        import card_render
        cx, cy = DISCARD_POS
        spacing = 18
        n = len(last_three)
        for i, card in enumerate(last_three[:-1]):
            offset = (i - (n - 1)) * spacing
            face = card_render.paint_face(card, int(CARD_WIDTH * 0.6),
                                           int(CARD_HEIGHT * 0.6))
            face = pygame.transform.rotate(face, -8 + i * 4)
            screen.blit(face, (cx - face.get_width() // 2 + offset,
                               cy + CARD_HEIGHT // 2 + 14))

    def draw_card_count_chip(self, screen, x, y, count, is_current):
        if self.tier() < 2:
            return
        th = theme.active()
        chip_w = 70
        chip_h = 22
        chip = pygame.Rect(x - chip_w // 2, y, chip_w, chip_h)
        pygame.draw.rect(screen, (*th.panel_bg, 220), chip, border_radius=11)
        outline_color = th.brass_300 if is_current else th.brass_700
        pygame.draw.rect(screen, outline_color, chip, 1, border_radius=11)

        import typography as typo
        font = typo.body_bold(12)
        for i in range(min(count, 4)):
            cx_dot = chip.x + 10 + i * 12
            cy_dot = chip.centery
            pygame.draw.circle(screen, th.brass_300, (cx_dot, cy_dot), 4)
            pygame.draw.circle(screen, th.brass_900, (cx_dot, cy_dot), 4, 1)
        count_label = font.render(f"x{count}", True, th.text_white)
        screen.blit(count_label, (chip.right - count_label.get_width() - 8,
                                   chip.centery - count_label.get_height() // 2))

    def coach_log(self, message, duration=5.0):
        if not self.coach_on():
            return
        self._coach_messages.append(message)
        self._coach_until = time.monotonic() + duration
        if len(self._coach_messages) > 4:
            self._coach_messages = self._coach_messages[-4:]

    def draw_coach(self, screen):
        if not self.coach_on():
            return
        if time.monotonic() > self._coach_until:
            return
        if not self._coach_messages:
            return
        th = theme.active()
        import typography as typo
        font = typo.body(16)
        small = typo.body_bold(13)
        msg = self._coach_messages[-1]
        text_surf = font.render(msg, True, th.text_white)
        w = text_surf.get_width() + 60
        h = 50
        x = SCREEN_WIDTH - w - 20
        y = 64
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*th.panel_bg, 230), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, th.signal_info, bg.get_rect(), 2, border_radius=8)
        screen.blit(bg, (x, y))
        tag = small.render("COACH", True, th.signal_info)
        screen.blit(tag, (x + 10, y + 6))
        screen.blit(text_surf, (x + 10, y + 26))

    def evaluate_post_turn(self, gm, last_action, drawn_card):
        """Tier 3: log post-turn analysis after a human action.
        last_action: dict with at least {'kind': str, 'detail': dict}
        """
        if not self.coach_on() or last_action is None or drawn_card is None:
            return
        kind = last_action.get("kind")
        cp = next((p for p in gm.players if p.is_human), None)
        if cp is None:
            return

        if kind == "discard":
            for slot, card in cp.known_cards.items():
                if card and card.rank == drawn_card.rank:
                    self.coach_log(
                        f"You discarded the {drawn_card.rank} — could have paired your "
                        f"{card.rank} of {card.suit} in slot {slot + 1}."
                    )
                    return
            for (p_idx, s_idx), card in cp.known_opponent_cards.items():
                if card and card.rank == drawn_card.rank:
                    self.coach_log(
                        f"You discarded the {drawn_card.rank} — could have paired the "
                        f"{card.rank} you saw in opponent {p_idx}'s slot {s_idx + 1}."
                    )
                    return

        if kind == "swap":
            slot = last_action.get("detail", {}).get("my_slot")
            if slot is not None and slot in cp.known_cards:
                old = cp.known_cards[slot]
                if old and old.value < (drawn_card.value if drawn_card.value is not None else 99):
                    self.coach_log(
                        f"You swapped a known {old.rank} (value {old.value}) for an unknown — "
                        f"may have raised your hand."
                    )
                    return
