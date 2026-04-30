import pygame
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM,
    CARD_WHITE, CARD_BACK_BLUE, CARD_BACK_PATTERN, CARD_BACK_MEDALLION,
    CARD_BACK_MEDALLION_HI, CARD_BACK_MEDALLION_LO, CARD_SHADOW, BLACK, RED, GOLD,
    GOLD_HOVER, TEXT_WHITE, TEXT_BLACK, TEXT_DIM, TEXT_DIMMER, HIGHLIGHT, DIM, PANEL_BG, PANEL_BORDER,
    POWER_GLOW, EMPTY_SLOT, DECLARE_RED, DECLARE_RED_HOVER, SWAP_GREEN, SWAP_GREEN_HOVER,
    PEEK_BLUE, PEEK_BLUE_HOVER,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD, HAND_SIZE, HAND_SIZE_OPTIONS,
    DECK_CENTER, DRAWN_CARD_POS, DISCARD_POS,
    PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    TITLE_FONT_SIZE, SUBTITLE_FONT_SIZE, UI_FONT_SIZE, LOG_FONT_SIZE,
    SMALL_FONT_SIZE, CARD_FONT_SIZE, CARD_BIG_FONT_SIZE,
)
from ui.widgets import Button


class MenuScreen:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("georgia", TITLE_FONT_SIZE, bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", SUBTITLE_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self._time = 0.0
        self.new_game_button = Button(SCREEN_WIDTH // 2, 460, 260, 54, "New Game", 'primary', font=self.button_font)
        self.quit_button = Button(SCREEN_WIDTH // 2, 530, 260, 54, "Quit", 'red', font=self.button_font)
        self.buttons = [self.new_game_button, self.quit_button]

    def _draw_card_back_medallion(self, surface, cx, cy, scale=1.0):
        w, h = int(44 * scale), int(30 * scale)
        hw, hh = w // 2, h // 2
        fill = CARD_BACK_MEDALLION
        hi = CARD_BACK_MEDALLION_HI
        lo = CARD_BACK_MEDALLION_LO
        oval_rect = pygame.Rect(cx - hw, cy - hh, w, h)
        pygame.draw.ellipse(surface, fill, oval_rect)
        pygame.draw.ellipse(surface, hi, oval_rect, 1)
        left_curl = [
            (cx - hw, cy),
            (cx - hw - int(8 * scale), cy - int(4 * scale)),
            (cx - hw - int(6 * scale), cy - int(10 * scale)),
            (cx - hw + int(2 * scale), cy - int(8 * scale)),
        ]
        right_curl = [
            (cx + hw, cy),
            (cx + hw + int(8 * scale), cy - int(4 * scale)),
            (cx + hw + int(6 * scale), cy - int(10 * scale)),
            (cx + hw - int(2 * scale), cy - int(8 * scale)),
        ]
        pygame.draw.lines(surface, fill, False, left_curl, 2)
        pygame.draw.lines(surface, hi, False, left_curl, 1)
        pygame.draw.lines(surface, fill, False, right_curl, 2)
        pygame.draw.lines(surface, hi, False, right_curl, 1)
        inner_diamond = [
            (cx, cy - int(10 * scale)), (cx + int(8 * scale), cy),
            (cx, cy + int(10 * scale)), (cx - int(8 * scale), cy)
        ]
        pygame.draw.polygon(surface, lo, inner_diamond)
        pygame.draw.polygon(surface, hi, inner_diamond, 1)
        dot = pygame.Rect(cx - 2, cy - 2, 4, 4)
        pygame.draw.rect(surface, hi, dot, border_radius=1)

    def _draw_menu_card_back(self, cx, cy, angle=0, alpha=255):
        surf = pygame.Surface((CARD_WIDTH + 20, CARD_HEIGHT + 20), pygame.SRCALPHA)
        rect = pygame.Rect(10, 10, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(surf, (*CARD_BACK_BLUE, alpha), rect, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(16, 16, CARD_WIDTH - 12, CARD_HEIGHT - 12)
        pygame.draw.rect(surf, (*CARD_BACK_PATTERN, alpha), inner, border_radius=CORNER_RADIUS - 2)
        line_color = (50, 90, 170, int(40 * alpha / 255))
        inner_w, inner_h = CARD_WIDTH - 20, CARD_HEIGHT - 20
        cross_surf = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
        for i in range(0, max(inner_w, inner_h), 12):
            if i < inner_w:
                pygame.draw.line(cross_surf, line_color, (i, 0), (i, inner_h))
            if i < inner_h:
                pygame.draw.line(cross_surf, line_color, (0, i), (inner_w, i))
        surf.blit(cross_surf, (10, 10))
        self._draw_card_back_medallion(surf, 10 + CARD_WIDTH // 2, 10 + CARD_HEIGHT // 2)
        pygame.draw.rect(surf, (*TEXT_WHITE, alpha), rect, 1, border_radius=CORNER_RADIUS)
        if angle != 0:
            surf = pygame.transform.rotate(surf, angle)
        self.screen.blit(surf, (cx - (CARD_WIDTH + 20) // 2, cy - (CARD_HEIGHT + 20) // 2))

    def draw(self):
        self.screen.fill(BG_DARK)
        gradient = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * t)
            g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * t)
            b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * t)
            for x in range(SCREEN_WIDTH):
                gradient.set_at((x, y), (r, g, b))
        self.screen.blit(gradient, (0, 0))

        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(0, 350, 8):
            alpha = int(50 * (1 - i / 350))
            pygame.draw.rect(vignette, (5, 5, 8, alpha),
                             (i, i, SCREEN_WIDTH - 2 * i, SCREEN_HEIGHT - 2 * i), border_radius=24)
        self.screen.blit(vignette, (0, 0))

        sway = math.sin(self._time * 1.5) * 3
        card_fan = [(-110, 295 + sway, -12), (-55, 290 + sway * 0.7, -4),
                     (0, 288, 0), (55, 290 - sway * 0.7, 4), (110, 295 - sway, 12)]
        for dx, cy, angle in card_fan:
            cx = SCREEN_WIDTH // 2 + dx
            self._draw_menu_card_back(cx, cy, angle)

        title_surf = self.title_font.render("DECLARE", True, GOLD)
        shadow_surf = self.title_font.render("DECLARE", True, (40, 25, 5))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2 + 2, 162))
        self.screen.blit(shadow_surf, title_rect)
        title_rect2 = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 160))
        self.screen.blit(title_surf, title_rect2)

        subtitle_surf = self.subtitle_font.render("A Card Game of Memory & Strategy", True, TEXT_DIM)
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 205)))

        for button in self.buttons:
            button.draw(self.screen)

    def update(self, dt):
        self._time += dt
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(dt, mouse_pos)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.contains(event.pos):
                    button.on_press()
                    return button.text.lower().replace(' ', '_')
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for button in self.buttons:
                button.on_release()
        return None


class SetupScreen:
    def __init__(self, screen, game_settings=None, num_players=2):
        self.screen = screen
        self.game_settings = game_settings
        self.title_font = pygame.font.SysFont("georgia", TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.input_font = pygame.font.SysFont("segoeui", SMALL_FONT_SIZE)
        self.num_players = num_players
        self.players_config = []
        for i in range(4):
            self.players_config.append({"name": f"Player {i + 1}", "is_human": i == 0})
        self.active_input = None
        self._all_buttons = []
        self._build_buttons()

    def _build_buttons(self):
        self._all_buttons = []
        self.player_count_btns = []
        for idx, count in enumerate([2, 3, 4]):
            bx = SCREEN_WIDTH // 2 - 100 + idx * 100
            btn = Button(bx, 180, 80, 44, str(count), 'primary', font=self.button_font)
            self.player_count_btns.append(btn)
            self._all_buttons.append(btn)
        self._build_game_settings_buttons()
        self.start_button = Button(SCREEN_WIDTH // 2, 700, 280, 54, "Start Game", 'primary', font=self.button_font)
        self.back_button = Button(100, 770, 160, 44, "Back", 'red', font=self.input_font)
        self._all_buttons.extend([self.start_button, self.back_button])

    def _build_game_settings_buttons(self):
        self.hand_size_buttons = []
        for idx, size in enumerate(HAND_SIZE_OPTIONS):
            bx = SCREEN_WIDTH // 2 - 180 + idx * 75
            btn = Button(bx, 0, 60, 36, str(size), 'primary', font=self.input_font)
            self.hand_size_buttons.append(btn)
            self._all_buttons.append(btn)
        self._rebuild_peek_count_buttons()

    def _rebuild_peek_count_buttons(self):
        self.peek_count_buttons = []
        if self.game_settings is None:
            return
        hand_size = self.game_settings.hand_size
        count = hand_size + 1
        start_x = SCREEN_WIDTH // 2 - (count * 55) // 2 + 25
        for i in range(count):
            bx = start_x + i * 55
            btn = Button(bx, 0, 48, 36, str(i), 'blue', font=self.input_font)
            self.peek_count_buttons.append(btn)
            self._all_buttons.append(btn)

    def _get_toggle_button(self, index, y):
        config = self.players_config[index]
        text = "Human" if config["is_human"] else "AI"
        variant = 'primary' if config["is_human"] else 'blue'
        btn = Button(820, y, 120, 36, text, variant, font=self.input_font)
        return btn

    def _settings_y(self):
        return 250 + self.num_players * 90 + 10

    def _get_active_buttons(self):
        btns = list(self.player_count_btns)
        btns.extend(self.hand_size_buttons)
        btns.extend(self.peek_count_buttons)
        btns.append(self.start_button)
        btns.append(self.back_button)
        for i in range(self.num_players):
            y = 250 + i * 90
            btns.append(self._get_toggle_button(i, y))
        return btns

    def draw(self):
        self.screen.fill(BG_DARK)
        gradient = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * t)
            g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * t)
            b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * t)
            for x in range(SCREEN_WIDTH):
                gradient.set_at((x, y), (r, g, b))
        self.screen.blit(gradient, (0, 0))

        title_surf = self.title_font.render("SETUP", True, GOLD)
        shadow = self.title_font.render("SETUP", True, (40, 25, 5))
        self.screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 82)))
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80)))

        label_surf = self.label_font.render("Number of Players:", True, TEXT_WHITE)
        self.screen.blit(label_surf, label_surf.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        for idx, btn in enumerate(self.player_count_btns):
            count_val = [2, 3, 4][idx]
            if self.num_players == count_val:
                btn.variant = 'gold'
                btn.base_color = GOLD
                btn.hover_color = GOLD_HOVER
                btn.text_color = BG_DARK
            else:
                btn.variant = 'primary'
                btn.base_color = SWAP_GREEN
                btn.hover_color = SWAP_GREEN_HOVER
                btn.text_color = TEXT_WHITE
            btn.draw(self.screen)

        for i in range(self.num_players):
            y = 250 + i * 90
            config = self.players_config[i]
            num_label = self.label_font.render(f"Player {i + 1}:", True, TEXT_DIM)
            self.screen.blit(num_label, (150, y - 12))
            name_rect = pygame.Rect(340, y - 18, 380, 36)
            border_color = GOLD if self.active_input == i else (50, 50, 55)
            pygame.draw.rect(self.screen, (30, 30, 35), name_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, name_rect, width=1, border_radius=8)
            name_surf = self.input_font.render(config["name"], True, TEXT_WHITE)
            self.screen.blit(name_surf, (name_rect.x + 10, name_rect.y + 9))
            toggle = self._get_toggle_button(i, y)
            if config["is_human"]:
                toggle.variant = 'primary'
                toggle.base_color = SWAP_GREEN
                toggle.hover_color = SWAP_GREEN_HOVER
            else:
                toggle.variant = 'blue'
                toggle.base_color = PEEK_BLUE
                toggle.hover_color = PEEK_BLUE_HOVER
            toggle.draw(self.screen)

        if self.game_settings is not None:
            settings_y = self._settings_y()
            section_surf = self.label_font.render("Game Settings", True, GOLD)
            self.screen.blit(section_surf, section_surf.get_rect(center=(SCREEN_WIDTH // 2, settings_y)))
            pygame.draw.line(self.screen, (60, 60, 65), (SCREEN_WIDTH // 2 - 200, settings_y + 18),
                             (SCREEN_WIDTH // 2 + 200, settings_y + 18), 1)

            hand_y = settings_y + 36
            hand_label = self.input_font.render("Cards per Hand:", True, TEXT_DIM)
            self.screen.blit(hand_label, (SCREEN_WIDTH // 2 - 240, hand_y - 8))
            for idx, btn in enumerate(self.hand_size_buttons):
                btn.rect.centery = hand_y
                if self.game_settings.hand_size == HAND_SIZE_OPTIONS[idx]:
                    btn.variant = 'gold'
                    btn.base_color = GOLD
                    btn.hover_color = GOLD_HOVER
                    btn.text_color = BG_DARK
                else:
                    btn.variant = 'primary'
                    btn.base_color = SWAP_GREEN
                    btn.hover_color = SWAP_GREEN_HOVER
                    btn.text_color = TEXT_WHITE
                btn.draw(self.screen)

            peek_y = hand_y + 50
            peek_label = self.input_font.render("Cards Visible:", True, TEXT_DIM)
            self.screen.blit(peek_label, (SCREEN_WIDTH // 2 - 240, peek_y - 8))
            for idx, btn in enumerate(self.peek_count_buttons):
                btn.rect.centery = peek_y
                if self.game_settings.peek_count == idx:
                    btn.variant = 'gold'
                    btn.base_color = GOLD
                    btn.hover_color = GOLD_HOVER
                    btn.text_color = BG_DARK
                else:
                    btn.variant = 'blue'
                    btn.base_color = PEEK_BLUE
                    btn.hover_color = PEEK_BLUE_HOVER
                    btn.text_color = TEXT_WHITE
                btn.draw(self.screen)

        self.start_button.draw(self.screen)
        self.back_button.draw(self.screen)

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._get_active_buttons():
            btn.update(dt, mouse_pos)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, btn in enumerate(self.player_count_btns):
                if btn.contains(event.pos):
                    self.num_players = [2, 3, 4][idx]
                    btn.on_press()
                    return None

            for i in range(self.num_players):
                y = 250 + i * 90
                toggle = self._get_toggle_button(i, y)
                if toggle.contains(event.pos):
                    self.players_config[i]["is_human"] = not self.players_config[i]["is_human"]
                    toggle.on_press()
                    return None
                name_rect = pygame.Rect(340, y - 18, 380, 36)
                if name_rect.collidepoint(event.pos):
                    self.active_input = i
                elif self.active_input == i:
                    self.active_input = None

            if self.game_settings is not None:
                for idx, btn in enumerate(self.hand_size_buttons):
                    if btn.contains(event.pos):
                        self.game_settings.hand_size = HAND_SIZE_OPTIONS[idx]
                        if self.game_settings.peek_count > self.game_settings.hand_size:
                            self.game_settings.peek_count = self.game_settings.hand_size
                        self._rebuild_peek_count_buttons()
                        btn.on_press()
                        return None
                for idx, btn in enumerate(self.peek_count_buttons):
                    if btn.contains(event.pos):
                        self.game_settings.peek_count = idx
                        btn.on_press()
                        return None

            if self.start_button.contains(event.pos):
                self.start_button.on_press()
                return 'start_game'
            if self.back_button.contains(event.pos):
                self.back_button.on_press()
                return 'back'

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self._get_active_buttons():
                btn.on_release()

        if event.type == pygame.KEYDOWN and self.active_input is not None:
            i = self.active_input
            if i < self.num_players:
                if event.key == pygame.K_BACKSPACE:
                    self.players_config[i]["name"] = self.players_config[i]["name"][:-1]
                elif event.key == pygame.K_RETURN:
                    self.active_input = None
                elif len(self.players_config[i]["name"]) < 20 and event.unicode.isprintable() and event.unicode != '':
                    self.players_config[i]["name"] += event.unicode
        return None


class PeekScreen:
    def __init__(self, screen, hand_size=4, peek_count=2, peek_seconds=5.0):
        self.screen = screen
        self.hand_size = hand_size
        self.peek_count = peek_count
        self.title_font = pygame.font.SysFont("georgia", TITLE_FONT_SIZE, bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", SUBTITLE_FONT_SIZE)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.card_font = pygame.font.SysFont("segoeui", CARD_FONT_SIZE, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", SMALL_FONT_SIZE)
        self.max_time = peek_seconds
        self.elapsed = 0.0
        self.revealed = True
        self.done_button = Button(SCREEN_WIDTH // 2, 500, 300, 54, "I've memorized them!", 'primary', font=self.button_font)
        self._all_buttons = [self.done_button]
        self._time = 0.0

    def _draw_card_face(self, x, y, card, glow=False):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        if glow:
            glow_rect = pygame.Rect(x - 5, y - 5, CARD_WIDTH + 10, CARD_HEIGHT + 10)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GOLD, 80), glow_surf.get_rect(), border_radius=CORNER_RADIUS + 4)
            self.screen.blit(glow_surf, (glow_rect.x, glow_rect.y))
        pygame.draw.rect(self.screen, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (40, 40, 45), rect, width=1, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        self.screen.blit(rank_surf, (x + 6, y + 4))
        sym_surf = self.card_font.render(card.suit_symbol, True, color)
        self.screen.blit(sym_surf, (x + 6, y + 22))
        center_surf = self.card_font.render(card.display_name, True, color)
        center_rect = center_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        self.screen.blit(center_surf, center_rect)

    def _draw_card_back(self, x, y, dimmed=False):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        base_color = tuple(c // 2 for c in CARD_BACK_BLUE) if dimmed else CARD_BACK_BLUE
        pygame.draw.rect(self.screen, base_color, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (40, 40, 45), rect, width=1, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(x + 8, y + 8, CARD_WIDTH - 16, CARD_HEIGHT - 16)
        inner_color = tuple(c // 2 for c in CARD_BACK_PATTERN) if dimmed else CARD_BACK_PATTERN
        pygame.draw.rect(self.screen, inner_color, inner, border_radius=4)

    def draw(self, game_manager):
        self.screen.fill(BG_DARK)
        gradient = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * t)
            g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * t)
            b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * t)
            for x in range(SCREEN_WIDTH):
                gradient.set_at((x, y), (r, g, b))
        self.screen.blit(gradient, (0, 0))

        title_surf = self.title_font.render("PEEK PHASE", True, GOLD)
        shadow = self.title_font.render("PEEK PHASE", True, (40, 25, 5))
        self.screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 82)))
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80)))

        if self.peek_count == 0:
            subtitle_text = "Blind start — no cards visible!"
        elif self.peek_count >= self.hand_size:
            subtitle_text = "All cards are face up!"
        else:
            subtitle_text = f"Memorize your bottom {self.peek_count} cards!"
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, TEXT_DIM)
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        bar_w = 400
        bar_h = 16
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 170
        remaining = max(0, 1.0 - self.elapsed / self.max_time)
        pygame.draw.rect(self.screen, (40, 40, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        fill_w = int(bar_w * remaining)
        if fill_w > 0:
            r = int(50 + 170 * remaining)
            g = int(180 * remaining)
            b = int(60 * remaining)
            pygame.draw.rect(self.screen, (r, g, b), (bar_x, bar_y, fill_w, bar_h), border_radius=8)
        pygame.draw.rect(self.screen, (60, 60, 65), (bar_x, bar_y, bar_w, bar_h), width=1, border_radius=8)

        if game_manager is None:
            self.done_button.draw(self.screen)
            return
        human = None
        for p in game_manager.players:
            if p.is_human:
                human = p
                break
        if human is None:
            self.done_button.draw(self.screen)
            return
        hand_size = len(human.hand)
        peek_slots = set(range(max(0, hand_size - self.peek_count), hand_size))
        total_spread = hand_size * CARD_WIDTH + (hand_size - 1) * CARD_SPREAD
        start_x = SCREEN_WIDTH // 2 - total_spread // 2
        card_y = 260
        for slot_idx in range(hand_size):
            cx = start_x + slot_idx * (CARD_WIDTH + CARD_SPREAD)
            card = human.hand[slot_idx]
            is_peek_slot = slot_idx in peek_slots and self.revealed
            if card is not None and is_peek_slot:
                self._draw_card_face(cx, card_y, card, glow=True)
            elif card is not None:
                self._draw_card_back(cx, card_y, dimmed=True)
            else:
                rect = pygame.Rect(cx, card_y, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, EMPTY_SLOT, rect, border_radius=CORNER_RADIUS)
            label = self.small_font.render(f"Slot {slot_idx + 1}", True, TEXT_DIMMER)
            self.screen.blit(label, label.get_rect(center=(cx + CARD_WIDTH // 2, card_y + CARD_HEIGHT + 20)))
        self.done_button.draw(self.screen)

    def update(self, dt):
        self._time += dt
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._all_buttons:
            btn.update(dt, mouse_pos)
        if self.revealed:
            self.elapsed += dt
            if self.elapsed >= self.max_time:
                self.revealed = False
                return 'peek_done'
        return None

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.done_button.contains(event.pos):
                self.done_button.on_press()
                self.revealed = False
                return 'peek_done'
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self._all_buttons:
                btn.on_release()
        return None


class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("georgia", TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.card_font = pygame.font.SysFont("segoeui", CARD_FONT_SIZE, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", SMALL_FONT_SIZE)
        self.play_again_button = Button(320, 680, 240, 50, "Play Again", 'primary', font=self.button_font)
        self.menu_button = Button(960, 680, 240, 50, "Main Menu", 'red', font=self.button_font)
        self.buttons = [self.play_again_button, self.menu_button]
        self._all_buttons = list(self.buttons)
        self._time = 0.0

    def _draw_card_face(self, x, y, card):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (40, 40, 45), rect, width=1, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        self.screen.blit(rank_surf, (x + 6, y + 4))
        sym_surf = self.card_font.render(card.suit_symbol, True, color)
        self.screen.blit(sym_surf, (x + 6, y + 22))
        center_surf = self.card_font.render(card.display_name, True, color)
        center_rect = center_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        self.screen.blit(center_surf, center_rect)

    def _draw_empty_slot(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, EMPTY_SLOT, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (40, 40, 45), rect, width=1, border_radius=CORNER_RADIUS)

    def draw(self, game_manager, result=None):
        self.screen.fill(BG_DARK)
        gradient = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * t)
            g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * t)
            b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * t)
            for x in range(SCREEN_WIDTH):
                gradient.set_at((x, y), (r, g, b))
        self.screen.blit(gradient, (0, 0))

        title_surf = self.title_font.render("GAME OVER", True, GOLD)
        shadow = self.title_font.render("GAME OVER", True, (40, 25, 5))
        self.screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 2, 62)))
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60)))

        if result:
            if result.get("auto_win"):
                announce_surf = self.label_font.render("Auto-win! A player has no cards!", True, TEXT_WHITE)
            elif result.get("winner"):
                winner = result["winner"]
                announce_text = f"{winner.name} wins!"
                announce_surf = self.label_font.render(announce_text, True, GOLD)
            elif result.get("declarer_won") is False:
                announce_surf = self.label_font.render("The declarer lost!", True, DECLARE_RED)
            else:
                announce_surf = self.label_font.render("It's a draw!", True, TEXT_WHITE)
            self.screen.blit(announce_surf, announce_surf.get_rect(center=(SCREEN_WIDTH // 2, 110)))

        if game_manager is None:
            for button in self.buttons:
                button.draw(self.screen)
            return

        num_players = len(game_manager.players)
        scores = result.get("scores", {}) if result else {}
        section_width = SCREEN_WIDTH // num_players
        for i, player in enumerate(game_manager.players):
            px = section_width * i + section_width // 2
            is_winner = result and result.get("winner") == player
            name_color = GOLD if is_winner else TEXT_WHITE
            name_surf = self.label_font.render(player.name, True, name_color)
            self.screen.blit(name_surf, name_surf.get_rect(center=(px, 160)))
            score_val = scores.get(player.seat_index, player.score if hasattr(player, 'score') else 0)
            score_surf = self.small_font.render(f"Score: {score_val}", True, GOLD)
            self.screen.blit(score_surf, score_surf.get_rect(center=(px, 190)))
            hand_size = len(player.hand)
            card_start_x = px - (hand_size * CARD_WIDTH + (hand_size - 1) * CARD_SPREAD) // 2
            for slot_idx in range(hand_size):
                card = player.hand[slot_idx]
                cx = card_start_x + slot_idx * (CARD_WIDTH + CARD_SPREAD)
                cy = 220
                if card is not None:
                    self._draw_card_face(cx, cy, card)
                else:
                    self._draw_empty_slot(cx, cy)

        for button in self.buttons:
            button.draw(self.screen)

    def update(self, dt):
        self._time += dt
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._all_buttons:
            btn.update(dt, mouse_pos)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_again_button.contains(event.pos):
                self.play_again_button.on_press()
                return 'play_again'
            if self.menu_button.contains(event.pos):
                self.menu_button.on_press()
                return 'menu'
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self._all_buttons:
                btn.on_release()
        return None