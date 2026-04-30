import math
import random
import pygame
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM,
    CARD_WHITE, CARD_BACK_BLUE, CARD_BACK_PATTERN, CARD_BACK_MEDALLION,
    CARD_BACK_MEDALLION_HI, CARD_BACK_MEDALLION_LO, CARD_SHADOW, BLACK, RED, GOLD,
    TEXT_WHITE, TEXT_BLACK, TEXT_DIM, HIGHLIGHT, DIM, PANEL_BG, PANEL_BORDER,
    POWER_GLOW, EMPTY_SLOT, KNOWN_TINT, DECLARE_RED, DECLARE_RED_HOVER,
    CANCEL_GRAY, CANCEL_GRAY_HOVER, PEEK_BLUE, PEEK_BLUE_HOVER, SWAP_GREEN,
    SWAP_GREEN_HOVER, DISCARD_ORANGE, DISCARD_ORANGE_HOVER, PAIR_TEAL, PAIR_TEAL_HOVER,
    STATUS_BAR_H, ACTION_BAR_Y, ACTION_BAR_H,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD,
    DECK_CENTER, DRAWN_CARD_POS, DISCARD_POS,
    PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    LOG_PANEL_X, LOG_PANEL_Y, LOG_PANEL_W, LOG_PANEL_H,
    CARD_FONT_SIZE, CARD_BIG_FONT_SIZE, TITLE_FONT_SIZE, SUBTITLE_FONT_SIZE,
    UI_FONT_SIZE, LOG_FONT_SIZE, SMALL_FONT_SIZE,
    POWER_LABELS, POWER_COLORS,
    CARD_GRID_SPACING_X, CARD_GRID_SPACING_Y, PLAYER_AREA_PADDING,
    ANIM_DRAW_DURATION, ANIM_SWAP_DURATION, ANIM_UNSEEN_SWAP_DURATION,
    ANIM_SEEN_SWAP_DURATION, ANIM_PEEK_LIFT_DURATION, ANIM_PAIR_FLY_DURATION,
    ANIM_DISCARD_DURATION, ANIM_NOTIFICATION_DURATION, ANIM_FLASH_DURATION,
    PLAYER_AREA_2, PLAYER_AREA_3, PLAYER_AREA_4,
    FELT_COLORS, FELT_COLORS_LIGHT, DEFAULT_FELT)
from game.card import Card
from game.player import Player
from game.game_manager import GameManager, GameState
from ui.animations import (VisualEvent, VisualEventType, AnimationQueue,
    ease_out_cubic, ease_out_back)

SEAT_POSITIONS_2 = {0: PLAYER_BOTTOM, 1: PLAYER_TOP}
SEAT_POSITIONS_3 = {0: PLAYER_BOTTOM, 1: (420, 200), 2: (1180, 200)}
SEAT_POSITIONS_4 = {0: PLAYER_BOTTOM, 1: PLAYER_LEFT, 2: PLAYER_TOP, 3: PLAYER_RIGHT}


def _player_area_bounds(seat_index, num_players):
    if num_players == 2:
        return PLAYER_AREA_2.get(seat_index, PLAYER_AREA_2[0])
    elif num_players == 3:
        return PLAYER_AREA_3.get(seat_index, PLAYER_AREA_3[0])
    else:
        return PLAYER_AREA_4.get(seat_index, PLAYER_AREA_4[0])


STATE_LABELS = {
    GameState.MENU: "Menu",
    GameState.SETUP: "Setup",
    GameState.PEEK_PHASE: "Peek Phase",
    GameState.TURN_START: "Turn Start",
    GameState.DRAW: "Draw",
    GameState.DECIDE: "Decide",
    GameState.POWER_RESOLVE: "Resolve Power",
    GameState.PAIR_CHECK: "Pair Check",
    GameState.TURN_END: "Turn End",
    GameState.RESOLVE_DECLARE: "Resolve Declare",
    GameState.GAME_OVER: "Game Over",
}

LAYOUT_ICONS = {'line': '\u2500\u2500\u2500', 'square': '\u2588\u2588', 'free': '\u2726'}
LAYOUT_NAMES = ['line', 'square', 'free']


def _get_seat_position(seat_index, num_players):
    if num_players == 2:
        return SEAT_POSITIONS_2.get(seat_index, PLAYER_BOTTOM)
    elif num_players == 3:
        return SEAT_POSITIONS_3.get(seat_index, PLAYER_BOTTOM)
    else:
        return SEAT_POSITIONS_4.get(seat_index, PLAYER_BOTTOM)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.card_font = pygame.font.SysFont("arial", CARD_FONT_SIZE, bold=True)
        self.card_big_font = pygame.font.SysFont("arial", CARD_BIG_FONT_SIZE, bold=True)
        self.title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
        self.subtitle_font = pygame.font.SysFont("arial", SUBTITLE_FONT_SIZE)
        self.ui_font = pygame.font.SysFont("arial", UI_FONT_SIZE)
        self.log_font = pygame.font.SysFont("arial", LOG_FONT_SIZE)
        self.small_font = pygame.font.SysFont("arial", SMALL_FONT_SIZE)
        self.hovered_card = None
        self.hovered_button = None
        self.hovered_slot = None
        self.peek_reveal = None
        self._pulse_time = 0.0
        self.animation_queue = AnimationQueue()
        self.dragging_card = None
        self.drag_pos = None
        self.game_settings = None
        self._felt_cache = {}
        self._felt_noise = None
        self._generate_noise()

    def _generate_noise(self):
        random.seed(42)
        self._felt_noise = pygame.Surface((256, 256), pygame.SRCALPHA)
        for _ in range(800):
            px = random.randint(0, 255)
            py = random.randint(0, 255)
            alpha = random.randint(5, 20)
            size = random.randint(1, 2)
            pygame.draw.circle(self._felt_noise, (255, 255, 255, alpha), (px, py), size)

    def _get_felt_surface(self, felt_key):
        if felt_key in self._felt_cache:
            return self._felt_cache[felt_key]
        base_color = FELT_COLORS.get(felt_key, FELT_COLORS[DEFAULT_FELT])
        light_color = FELT_COLORS_LIGHT.get(felt_key, FELT_COLORS_LIGHT[DEFAULT_FELT])
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                t = min(dist / max_dist, 1.0)
                r = int(base_color[0] + (light_color[0] - base_color[0]) * (1.0 - t * t))
                g = int(base_color[1] + (light_color[1] - base_color[1]) * (1.0 - t * t))
                b = int(base_color[2] + (light_color[2] - base_color[2]) * (1.0 - t * t))
                surf.set_at((x, y), (r, g, b))
        if self._felt_noise:
            noise_area = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for y in range(0, SCREEN_HEIGHT, 256):
                for x in range(0, SCREEN_WIDTH, 256):
                    noise_area.blit(self._felt_noise, (x, y))
            surf.blit(noise_area, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self._felt_cache[felt_key] = surf
        return surf

    def draw_background(self):
        self.screen.fill(BG_DARK)

    def draw(self, game_manager, mouse_pos=(0, 0), action_buttons=None,
             cancel_button=None, status_message="", awaiting_target=None):
        felt_key = self.game_settings.felt_style if self.game_settings else DEFAULT_FELT
        felt_surf = self._get_felt_surface(felt_key)
        self.screen.blit(felt_surf, (0, 0))
        self._draw_table_rail()
        self._draw_table_felt()
        self._draw_status_bar(game_manager)
        self.draw_discard(game_manager.discard_pile)
        self.draw_deck(game_manager.deck.remaining if game_manager.deck else 0)
        cp = game_manager.current_player()
        if game_manager.drawn_card and cp.is_human:
            self.draw_drawn_card(game_manager.drawn_card)
        num_players = len(game_manager.players)
        current_player_index = game_manager.current_player_index
        for player in game_manager.players:
            pos = _get_seat_position(player.seat_index, num_players)
            is_current = player.seat_index == current_player_index
            is_human = player.is_human
            self.draw_player_area(player, pos, is_current, is_human, game_manager, mouse_pos)
        self.draw_peek_reveal()
        if game_settings := self.game_settings:
            if game_settings.show_game_log:
                self.draw_game_log(game_manager.game_log)
        if action_buttons:
            self._draw_action_bar_container()
            self.draw_action_buttons(action_buttons)
        if cancel_button:
            self._draw_cancel_button(cancel_button, mouse_pos)
        if status_message:
            self.draw_status_message(status_message)
        self.animation_queue.draw(self.screen, self)

    def _draw_action_bar_container(self):
        container_rect = pygame.Rect(0, ACTION_BAR_Y - 8, SCREEN_WIDTH, ACTION_BAR_H + 16)
        container_surf = pygame.Surface((container_rect.width, container_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(container_surf, (*BG_DARK, 220), container_surf.get_rect(), border_radius=12)
        pygame.draw.rect(container_surf, (*PANEL_BORDER, 100), container_surf.get_rect(), 1, border_radius=12)
        self.screen.blit(container_surf, container_rect.topleft)
        pygame.draw.line(self.screen, (*GOLD_DIM, 60), (container_rect.left + 20, container_rect.top),
                         (container_rect.right - 20, container_rect.top), 1)

    def _draw_table_rail(self):
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        rx, ry = 620, 340
        rail_w = 28
        outer_rx = rx + rail_w
        outer_ry = ry + rail_w
        rail_surf = pygame.Surface((outer_rx * 2, outer_ry * 2), pygame.SRCALPHA)
        for i in range(rail_w, 0, -1):
            t = i / rail_w
            r = int(55 + 20 * t)
            g = int(35 + 15 * t)
            b = int(18 + 10 * t)
            a = int(180 + 60 * t)
            inner_ellipse = pygame.Rect(i, i, (outer_rx - i) * 2, (outer_ry - i) * 2)
            pygame.draw.ellipse(rail_surf, (r, g, b, a), inner_ellipse)
        self.screen.blit(rail_surf, (center[0] - outer_rx, center[1] - outer_ry))
        gold_pts = []
        steps = 120
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            x = center[0] + outer_rx * math.cos(angle)
            y = center[1] + outer_ry * math.sin(angle)
            gold_pts.append((x, y))
        if len(gold_pts) > 2:
            pygame.draw.lines(self.screen, (*GOLD, 120), True, gold_pts, 2)
        pygame.draw.ellipse(self.screen, (35, 22, 12, 200),
                            (center[0] - outer_rx, center[1] - outer_ry,
                             outer_rx * 2, outer_ry * 2), 2)

    def _draw_table_felt(self):
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        rx, ry = 620, 340
        felt_surf = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
        felt_base = FELT_COLORS.get(DEFAULT_FELT, FELT_COLORS['forest'])
        felt_light = FELT_COLORS_LIGHT.get(DEFAULT_FELT, FELT_COLORS_LIGHT['forest'])
        cx_f, cy_f = rx, ry
        max_dist = math.sqrt(cx_f * cx_f + cy_f * cy_f)
        for y in range(ry * 2):
            for x in range(rx * 2):
                dist = math.sqrt((x - cx_f) ** 2 + (y - cy_f) ** 2)
                t = min(dist / max_dist, 1.0)
                r = int(felt_base[0] + (felt_light[0] - felt_base[0]) * (1.0 - t * t))
                g = int(felt_base[1] + (felt_light[1] - felt_base[1]) * (1.0 - t * t))
                b = int(felt_base[2] + (felt_light[2] - felt_base[2]) * (1.0 - t * t))
                felt_surf.set_at((x, y), (r, g, b, 200))
        self.screen.blit(felt_surf, (center[0] - rx, center[1] - ry))
        pygame.draw.ellipse(self.screen, (*GOLD_DIM, 80),
                            (center[0] - rx, center[1] - ry, rx * 2, ry * 2), 1)

    def _draw_status_bar(self, game_manager):
        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, STATUS_BAR_H)
        gradient_surf = pygame.Surface((SCREEN_WIDTH, STATUS_BAR_H))
        for i in range(STATUS_BAR_H):
            t = i / STATUS_BAR_H
            r = int(18 + 8 * t)
            g = int(22 + 12 * t)
            b = int(28 + 10 * t)
            for j in range(SCREEN_WIDTH):
                gradient_surf.set_at((j, i), (r, g, b))
        self.screen.blit(gradient_surf, (0, 0))
        pygame.draw.line(self.screen, (*GOLD_DIM, 100), (0, STATUS_BAR_H - 1), (SCREEN_WIDTH, STATUS_BAR_H - 1), 1)
        state_label = STATE_LABELS.get(game_manager.state, str(game_manager.state.value))
        current_player = game_manager.current_player()
        avatar_rect = pygame.Rect(14, (STATUS_BAR_H - 28) // 2, 28, 28)
        pygame.draw.circle(self.screen, (30, 30, 35), avatar_rect.center, 14)
        pygame.draw.circle(self.screen, GOLD, avatar_rect.center, 14, 2)
        initial_surf = self.small_font.render(current_player.name[0].upper(), True, GOLD)
        initial_rect = initial_surf.get_rect(center=avatar_rect.center)
        self.screen.blit(initial_surf, initial_rect)
        round_surf = self.ui_font.render(f"Round {game_manager.round_number}", True, TEXT_DIM)
        text_x = avatar_rect.right + 16
        self.screen.blit(round_surf, (text_x, (STATUS_BAR_H - round_surf.get_height()) // 2))
        name_surf = self.ui_font.render(current_player.name, True, GOLD)
        name_x = text_x + round_surf.get_width() + 20
        self.screen.blit(name_surf, (name_x, (STATUS_BAR_H - name_surf.get_height()) // 2))
        state_surf = self.small_font.render(state_label, True, TEXT_DIM)
        state_x = name_x + name_surf.get_width() + 16
        self.screen.blit(state_surf, (state_x, (STATUS_BAR_H - state_surf.get_height()) // 2 + 2))

    def draw_card_face(self, x, y, card, selected=False, hovered=False, show_power_label=False, show_pips=True):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._draw_shadow(x, y)
        bg_color = CARD_WHITE
        if hovered:
            bg_color = (252, 252, 248)
        self._draw_rounded_rect(self.screen, bg_color, rect, CORNER_RADIUS)
        color = RED if card.is_red else BLACK

        inner_rect = pygame.Rect(x + 3, y + 3, CARD_WIDTH - 6, CARD_HEIGHT - 6)
        pygame.draw.rect(self.screen, (230, 230, 228), inner_rect, 1, border_radius=CORNER_RADIUS - 2)

        corner_text = f"{card.rank}{card.suit_symbol}"
        badge_rect = pygame.Rect(x + 2, y + 1, 34, 20)
        pygame.draw.rect(self.screen, (242, 242, 248), badge_rect, border_radius=4)
        tl_surf = self.small_font.render(corner_text, True, color)
        self.screen.blit(tl_surf, (x + 5, y + 3))
        br_surf = self.small_font.render(corner_text, True, color)
        br_surf = pygame.transform.rotate(br_surf, 180)
        br_rect = br_surf.get_rect(bottomright=(x + CARD_WIDTH - 5, y + CARD_HEIGHT - 3))
        self.screen.blit(br_surf, br_rect)

        big_surf = self.card_big_font.render(card.rank, True, color)
        big_rect = big_surf.get_rect(center=(x + CARD_WIDTH // 2 + 6, y + CARD_HEIGHT // 2 - 6))
        self.screen.blit(big_surf, big_rect)
        suit_surf = self.card_font.render(card.suit_symbol, True, color)
        suit_rect = suit_surf.get_rect(center=(x + CARD_WIDTH // 2 + 6, y + CARD_HEIGHT // 2 + 18))
        self.screen.blit(suit_surf, suit_rect)

        if card.rank in ('J', 'Q', 'K'):
            self._draw_crown(x, y, card)

        if show_pips:
            self._draw_suit_pips(x, y, card)

        if show_power_label and card.power is not None:
            power_color = POWER_COLORS.get(card.power, TEXT_WHITE)
            power_label = POWER_LABELS.get(card.power, card.power)
            p_surf = self.small_font.render(power_label, True, power_color)
            p_rect = p_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT + 12))
            self.screen.blit(p_surf, p_rect)
        if selected:
            sel_rect = rect.inflate(4, 4)
            pygame.draw.rect(self.screen, GOLD, sel_rect, 2, border_radius=CORNER_RADIUS + 2)
        pygame.draw.rect(self.screen, (170, 170, 170), rect, 1, border_radius=CORNER_RADIUS)
        return rect

    def _draw_suit_pips(self, x, y, card):
        color = RED if card.is_red else BLACK
        cx = x + CARD_WIDTH // 2
        cy = y + CARD_HEIGHT // 2
        w, h = CARD_WIDTH, CARD_HEIGHT

        def pip(px, py, size=8):
            pts = [(px, py - size), (px + size * 0.65, py + size * 0.5),
                   (px - size * 0.65, py + size * 0.5)]
            pygame.draw.polygon(self.screen, color, pts)

        def diam(px, py, size=8):
            pts = [(px, py - size), (px + size, py), (px, py + size), (px - size, py)]
            pygame.draw.polygon(self.screen, color, pts)

        rank = card.rank
        if rank == 'A':
            pip(cx, cy)
        elif rank == '2':
            pip(cx, cy - 26)
            pip(cx, cy + 26)
        elif rank == '3':
            pip(cx, cy - 26)
            pip(cx, cy + 26)
            pip(cx, cy)
        elif rank == '4':
            pip(cx - 20, cy - 18)
            pip(cx + 20, cy - 18)
            pip(cx - 20, cy + 18)
            pip(cx + 20, cy + 18)
        elif rank == '5':
            pip(cx - 20, cy - 18)
            pip(cx + 20, cy - 18)
            pip(cx - 20, cy + 18)
            pip(cx + 20, cy + 18)
            pip(cx, cy)
        elif rank == '6':
            pip(cx - 20, cy - 22)
            pip(cx + 20, cy - 22)
            pip(cx - 20, cy)
            pip(cx + 20, cy)
            pip(cx - 20, cy + 22)
            pip(cx + 20, cy + 22)
        elif rank == '7':
            pip(cx - 20, cy - 22)
            pip(cx + 20, cy - 22)
            pip(cx - 20, cy)
            pip(cx + 20, cy)
            pip(cx - 20, cy + 22)
            pip(cx + 20, cy + 22)
            pip(cx, cy - 32)
        elif rank == '8':
            pip(cx - 20, cy - 22)
            pip(cx + 20, cy - 22)
            pip(cx - 20, cy)
            pip(cx + 20, cy)
            pip(cx - 20, cy + 22)
            pip(cx + 20, cy + 22)
            pip(cx, cy - 32)
            pip(cx, cy + 32)
        elif rank == '9':
            pip(cx - 22, cy - 26)
            pip(cx + 22, cy - 26)
            pip(cx - 22, cy)
            pip(cx + 22, cy)
            pip(cx - 22, cy + 26)
            pip(cx + 22, cy + 26)
            pip(cx, cy)
        elif rank == '10':
            pip(cx - 22, cy - 30)
            pip(cx + 22, cy - 30)
            pip(cx - 22, cy - 4)
            pip(cx + 22, cy - 4)
            pip(cx - 22, cy + 22)
            pip(cx + 22, cy + 22)
            pip(cx, cy - 30)
            pip(cx, cy - 4)
            pip(cx, cy + 22)
        elif rank in ('J', 'Q', 'K'):
            pass
        else:
            pass

    def _draw_crown(self, x, y, card):
        color = RED if card.is_red else BLACK
        cx = x + CARD_WIDTH // 2 + 8
        cy = y + CARD_HEIGHT // 2 + 6
        base_w = 22
        base_h = 10
        crown_pts = [
            (cx - base_w // 2, cy + base_h // 2),
            (cx - base_w // 2, cy - base_h // 4),
            (cx - base_w // 4, cy - base_h // 2),
            (cx, cy - base_h // 4),
            (cx + base_w // 4, cy - base_h // 2),
            (cx + base_w // 2, cy - base_h // 4),
            (cx + base_w // 2, cy + base_h // 2),
        ]
        crown_fill = (220, 170, 30) if card.is_red else (80, 80, 80)
        pygame.draw.polygon(self.screen, crown_fill, crown_pts)
        pygame.draw.polygon(self.screen, (255, 220, 80), crown_pts, 1)
        if card.rank == 'K':
            if not card.is_red:
                k_surf = self.small_font.render("0", True, (180, 180, 180))
                k_rect = k_surf.get_rect(center=(cx, cy + base_h + 5))
                self.screen.blit(k_surf, k_rect)
            else:
                k_surf = self.small_font.render("13", True, (150, 20, 20))
                k_rect = k_surf.get_rect(center=(cx, cy + base_h + 5))
                self.screen.blit(k_surf, k_rect)

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

    def draw_card_back(self, x, y, has_known_marker=False, hovered=False):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        lift_y = -4 if hovered else 0
        self._draw_shadow(x, y + lift_y)

        self._draw_rounded_rect(self.screen, CARD_BACK_BLUE, rect, CORNER_RADIUS)

        inner = pygame.Rect(x + 6, y + 6, CARD_WIDTH - 12, CARD_HEIGHT - 12)
        pygame.draw.rect(self.screen, CARD_BACK_PATTERN, inner, border_radius=CORNER_RADIUS - 2)

        self._draw_card_back_crosshatch(x, y + lift_y)

        dcx = x + CARD_WIDTH // 2
        dcy = y + CARD_HEIGHT // 2 + lift_y
        self._draw_card_back_medallion(self.screen, dcx, dcy)

        pygame.draw.rect(self.screen, TEXT_WHITE, rect, 1, border_radius=CORNER_RADIUS)

        if has_known_marker:
            badge_x = x + CARD_WIDTH - 14
            badge_y = y + 6 + lift_y
            pygame.draw.circle(self.screen, GOLD, (badge_x, badge_y + 4), 5)
            pygame.draw.circle(self.screen, (201, 168, 76, 100), (badge_x, badge_y + 4), 5, 1)
        return rect

    def _draw_card_back_crosshatch(self, x, y):
        inner_x = x + 10
        inner_y = y + 10
        inner_w = CARD_WIDTH - 20
        inner_h = CARD_HEIGHT - 20
        line_color = (50, 90, 170, 40)
        spacing = 12
        surface = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
        for i in range(-inner_h, inner_w, spacing):
            pts = []
            for j in range(0, inner_w + inner_h, 4):
                px = i + j
                py = j
                if 0 <= px < inner_w and 0 <= py < inner_h:
                    pass
                px2 = i + j
                py2 = -j + inner_h if (i + j) >= inner_h else inner_h
                if 0 <= px2 < inner_w and 0 <= py2 < inner_h:
                    pass
        cross_surf = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
        step = spacing
        for i in range(0, max(inner_w, inner_h), step):
            if i < inner_w:
                pygame.draw.line(cross_surf, line_color, (i, 0), (i, inner_h))
            if i < inner_h:
                pygame.draw.line(cross_surf, line_color, (0, i), (inner_w, i))
        self.screen.blit(cross_surf, (inner_x, inner_y))

    def draw_empty_slot(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._draw_dashed_rect(self.screen, EMPTY_SLOT, rect, CORNER_RADIUS)
        return rect

    def draw_deck(self, remaining):
        cx, cy = DECK_CENTER
        dx = cx - CARD_WIDTH // 2
        dy = cy - CARD_HEIGHT // 2
        if remaining > 0:
            stack_count = min(remaining, 5)
            for i in range(stack_count - 1, -1, -1):
                offset = i * 2
                shadow_rect = pygame.Rect(dx - offset, dy - offset, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, (15, 30, 60), shadow_rect, border_radius=CORNER_RADIUS)
            top_rect = pygame.Rect(dx, dy, CARD_WIDTH, CARD_HEIGHT)
            self._draw_rounded_rect(self.screen, CARD_BACK_BLUE, top_rect, CORNER_RADIUS)
            inner = pygame.Rect(dx + 6, dy + 6, CARD_WIDTH - 12, CARD_HEIGHT - 12)
            pygame.draw.rect(self.screen, CARD_BACK_PATTERN, inner, border_radius=CORNER_RADIUS - 2)
            inner_x, inner_y = dx + 10, dy + 10
            inner_w, inner_h = CARD_WIDTH - 20, CARD_HEIGHT - 20
            line_color = (40, 70, 140, 35)
            cross_surf = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
            for i in range(0, max(inner_w, inner_h), 12):
                if i < inner_w:
                    pygame.draw.line(cross_surf, line_color, (i, 0), (i, inner_h))
                if i < inner_h:
                    pygame.draw.line(cross_surf, line_color, (0, i), (inner_w, i))
            self.screen.blit(cross_surf, (inner_x, inner_y))
            self._draw_card_back_medallion(self.screen, cx, cy)
            pygame.draw.rect(self.screen, TEXT_WHITE, top_rect, 1, border_radius=CORNER_RADIUS)
            count_surf = self.small_font.render(str(remaining), True, TEXT_WHITE)
            count_rect = count_surf.get_rect(center=(cx, cy + CARD_HEIGHT // 2 + 14))
            self.screen.blit(count_surf, count_rect)
        else:
            self.draw_empty_slot(dx, dy)
            empty_surf = self.small_font.render("Empty", True, DIM)
            empty_rect = empty_surf.get_rect(center=(cx, cy))
            self.screen.blit(empty_surf, empty_rect)

    def draw_discard(self, discard_pile):
        if not discard_pile:
            return
        cx, cy = DISCARD_POS
        dx = cx - CARD_WIDTH // 2
        dy = cy - CARD_HEIGHT // 2
        top_card = discard_pile[-1]
        top_card.face_up = True
        self.draw_card_face(dx, dy, top_card)
        label_surf = self.small_font.render("Discard", True, TEXT_DIM)
        label_rect = label_surf.get_rect(center=(cx, cy + CARD_HEIGHT // 2 + 14))
        self.screen.blit(label_surf, label_rect)

    def draw_player_area(self, player, position, is_current, is_human, game_manager, mouse_pos):
        px, py = position
        layout = getattr(player, 'layout_mode', 'line')
        num_players = len(game_manager.players)
        card_positions = self._compute_card_positions(player, position, game_manager)
        self.hovered_slot = None
        if is_human:
            for slot_index in range(len(player.hand)):
                if slot_index < len(card_positions):
                    cx, cy = card_positions[slot_index]
                    card_rect = pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT)
                    if card_rect.collidepoint(mouse_pos) and player.hand[slot_index] is not None:
                        self.hovered_slot = slot_index
                        break

        bounds = _player_area_bounds(player.seat_index, num_players)
        if layout == 'free':
            self._draw_area_outline(bounds)

        name_color = GOLD if is_current else TEXT_WHITE
        raw_name_y = card_positions[0][1] - CARD_HEIGHT // 2 - 50 if card_positions else py - 70
        _, y_min, _, y_max = bounds
        name_y = max(y_min + 20, min(raw_name_y, y_max - CARD_HEIGHT - 60))
        name_surf = self.ui_font.render(player.name, True, name_color)
        name_rect = name_surf.get_rect(center=(px, name_y))
        if is_current:
            alpha = int(80 + 40 * math.sin(self._pulse_time * 3))
            glow_rect = name_rect.inflate(24, 12)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GOLD, alpha), glow_surf.get_rect(), border_radius=8)
            self.screen.blit(glow_surf, glow_rect.topleft)
        pill_surf = pygame.Surface((name_rect.width + 32, name_rect.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (*BG_DARK, 180), pill_surf.get_rect(), border_radius=8)
        self.screen.blit(pill_surf, (name_rect.centerx - name_rect.width // 2 - 16, name_rect.centery - name_rect.height // 2 - 8))
        self.screen.blit(name_surf, name_rect)
        info_y = name_y + name_surf.get_height() + 4
        if is_human:
            info_text = f"Cards: {player.card_count}"
        else:
            info_text = f"Cards: {player.card_count}"
        info_surf = self.small_font.render(info_text, True, TEXT_DIM)
        info_rect = info_surf.get_rect(center=(px, info_y))
        self.screen.blit(info_surf, info_rect)

        for slot_index in range(len(player.hand)):
            card = player.hand[slot_index]
            if slot_index < len(card_positions):
                cx, cy = card_positions[slot_index]
            else:
                cx, cy = 0, 0

            if self.dragging_card is not None and self.dragging_card == slot_index and is_human:
                continue

            hovered = is_human and self.hovered_slot == slot_index
            if card is None:
                self.draw_empty_slot(cx, cy)
            elif is_human:
                has_marker = slot_index in player.known_cards
                self.draw_card_back(cx, cy, has_known_marker=has_marker, hovered=hovered)
            else:
                self.draw_card_back(cx, cy, has_known_marker=False)

        if self.dragging_card is not None and is_human and self.drag_pos is not None:
            slot_index = self.dragging_card
            card = player.hand[slot_index]
            if card is not None:
                dx, dy = self.drag_pos
                drag_surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
                if slot_index in player.known_cards:
                    self._render_card_face_on_surface(drag_surf, card, show_pips=False)
                else:
                    self._render_card_back_on_surface(drag_surf)
                drag_surf.set_alpha(200)
                self.screen.blit(drag_surf, (dx - CARD_WIDTH // 2, dy - CARD_HEIGHT // 2))

    def _draw_area_outline(self, bounds):
        x_min, y_min, x_max, y_max = bounds
        outline_rect = pygame.Rect(x_min, y_min, x_max - x_min, y_max - y_min)
        outline_surf = pygame.Surface((outline_rect.width, outline_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(outline_surf, (255, 255, 255, 25), outline_surf.get_rect(), 2, border_radius=8)
        self.screen.blit(outline_surf, outline_rect.topleft)

    def _compute_card_positions(self, player, position, game_manager):
        px, py = position
        layout = getattr(player, 'layout_mode', 'line')
        num_players = len(game_manager.players)
        positions = []

        hand_size = len(player.hand)

        if layout == 'line':
            total_width = hand_size * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
            start_x = px - total_width // 2
            start_y = py - CARD_HEIGHT // 2 + 4
            for i in range(hand_size):
                positions.append((start_x + i * CARD_SPREAD, start_y))

        elif layout == 'square':
            if hand_size == 4:
                grid_w = 2 * CARD_GRID_SPACING_X
                grid_h = 2 * CARD_GRID_SPACING_Y
                start_x = px - grid_w // 2
                start_y = py - grid_h // 2 + 4
                grid_positions = [
                    (start_x, start_y),
                    (start_x + CARD_GRID_SPACING_X, start_y),
                    (start_x, start_y + CARD_GRID_SPACING_Y),
                    (start_x + CARD_GRID_SPACING_X, start_y + CARD_GRID_SPACING_Y),
                ]
                for i in range(hand_size):
                    positions.append(grid_positions[i])
            else:
                total_width = hand_size * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
                start_x = px - total_width // 2
                start_y = py - CARD_HEIGHT // 2 + 4
                for i in range(hand_size):
                    positions.append((start_x + i * CARD_SPREAD, start_y))

        elif layout == 'free':
            default_positions = self._default_line_positions(px, py, hand_size)
            stored = getattr(player, 'card_positions', {})
            for i in range(hand_size):
                if i in stored and stored[i] is not None:
                    positions.append(stored[i])
                elif i < len(default_positions):
                    positions.append(default_positions[i])
                    if i not in stored:
                        stored[i] = default_positions[i]
                else:
                    positions.append((px, py))
            player.card_positions = stored

        return positions

    def _default_line_positions(self, px, py, hand_size=4):
        total_width = hand_size * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
        start_x = px - total_width // 2
        start_y = py - CARD_HEIGHT // 2 + 4
        positions = []
        for i in range(hand_size):
            positions.append((start_x + i * CARD_SPREAD, start_y))
        return positions

    def _draw_layout_buttons(self, player, cx, y, mouse_pos):
        layout = getattr(player, 'layout_mode', 'line')
        btn_w = 36
        btn_h = 22
        spacing = 4
        total_w = len(LAYOUT_NAMES) * btn_w + (len(LAYOUT_NAMES) - 1) * spacing
        start_x = cx - total_w // 2

        for i, mode in enumerate(LAYOUT_NAMES):
            bx = start_x + i * (btn_w + spacing)
            rect = pygame.Rect(bx, y, btn_w, btn_h)
            is_active = (layout == mode)
            is_hovered = rect.collidepoint(mouse_pos) and not is_active
            if is_active:
                color = GOLD
                text_color = BG_DARK
            elif is_hovered:
                color = (100, 100, 100)
                text_color = TEXT_WHITE
            else:
                color = (60, 60, 60)
                text_color = TEXT_DIM
            self._draw_rounded_rect(self.screen, color, rect, 4)
            icon = LAYOUT_ICONS[mode]
            icon_surf = self.small_font.render(icon, True, text_color)
            icon_rect = icon_surf.get_rect(center=rect.center)
            self.screen.blit(icon_surf, icon_rect)

    def get_layout_button_rects(self, player, cx, y):
        btn_w = 36
        btn_h = 22
        spacing = 4
        total_w = len(LAYOUT_NAMES) * btn_w + (len(LAYOUT_NAMES) - 1) * spacing
        start_x = cx - total_w // 2
        rects = {}
        for i, mode in enumerate(LAYOUT_NAMES):
            bx = start_x + i * (btn_w + spacing)
            rects[mode] = pygame.Rect(bx, y, btn_w, btn_h)
        return rects

    def get_layout_button_y(self, player, game_manager):
        pos = _get_seat_position(player.seat_index, len(game_manager.players))
        card_positions = self._compute_card_positions(player, pos, game_manager)
        if card_positions:
            return int(card_positions[0][1]) - 28 - 18
        return pos[1] - 50

    def init_free_positions(self, player, game_manager):
        pos = _get_seat_position(player.seat_index, len(game_manager.players))
        defaults = self._default_line_positions(pos[0], pos[1])
        for i, p in enumerate(defaults):
            if i not in player.card_positions:
                player.card_positions[i] = p

    def _render_card_face_on_surface(self, surface, card, show_pips=True):
        rect = surface.get_rect()
        pygame.draw.rect(surface, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK

        inner_rect = pygame.Rect(4, 4, rect.width - 8, rect.height - 8)
        pygame.draw.rect(surface, (225, 225, 230), inner_rect, 1, border_radius=CORNER_RADIUS - 2)

        if show_pips:
            self._draw_suit_pips(0, 0, card)

        big_surf = self.card_big_font.render(card.rank, True, color)
        big_rect = big_surf.get_rect(center=(rect.width // 2 + 8, rect.height // 2 - 8))
        surface.blit(big_surf, big_rect)
        suit_surf = self.card_font.render(card.suit_symbol, True, color)
        suit_rect = suit_surf.get_rect(center=(rect.width // 2 + 8, rect.height // 2 + 16))
        surface.blit(suit_surf, suit_rect)

        if card.rank in ('J', 'Q', 'K'):
            self._draw_crown(0, 0, card)

        corner_text = f"{card.rank}{card.suit_symbol}"
        badge_rect = pygame.Rect(2, 1, 32, 18)
        pygame.draw.rect(surface, (240, 240, 245), badge_rect, border_radius=3)
        tl_surf = self.small_font.render(corner_text, True, color)
        surface.blit(tl_surf, (5, 4))
        br_surf = self.small_font.render(corner_text, True, color)
        br_rect = br_surf.get_rect(bottomright=(rect.width - 5, rect.height - 4))
        surface.blit(br_surf, br_rect)

        pygame.draw.rect(surface, (180, 180, 180), rect, 1, border_radius=CORNER_RADIUS)

    def _render_card_back_on_surface(self, surface):
        rect = surface.get_rect()
        gradient_surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
        for i in range(CARD_WIDTH):
            t = i / CARD_WIDTH
            alpha = int(20 + 25 * t)
            pygame.draw.line(gradient_surf, (20, 45, 95, alpha), (i, 0), (i, CARD_HEIGHT))
        surface.blit(gradient_surf, (0, 0))
        pygame.draw.rect(surface, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(6, 6, rect.width - 12, rect.height - 12)
        pygame.draw.rect(surface, CARD_BACK_PATTERN, inner, border_radius=CORNER_RADIUS - 2)
        inner_x, inner_y = 10, 10
        inner_w, inner_h = CARD_WIDTH - 20, CARD_HEIGHT - 20
        line_color = (50, 90, 170, 40)
        cross_surf = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
        for i in range(0, max(inner_w, inner_h), 12):
            if i < inner_w:
                pygame.draw.line(cross_surf, line_color, (i, 0), (i, inner_h))
            if i < inner_h:
                pygame.draw.line(cross_surf, line_color, (0, i), (inner_w, i))
        surface.blit(cross_surf, (inner_x, inner_y))
        dcx = rect.width // 2
        dcy = rect.height // 2
        self._draw_card_back_medallion(surface, dcx, dcy)
        pygame.draw.rect(surface, TEXT_WHITE, rect, 1, border_radius=CORNER_RADIUS)

    def draw_drawn_card(self, card):
        cx, cy = DRAWN_CARD_POS
        dx = cx - CARD_WIDTH // 2
        dy = cy - CARD_HEIGHT // 2
        label_surf = self.small_font.render("DREW", True, GOLD)
        label_rect = label_surf.get_rect(center=(cx, dy - 12))
        self.screen.blit(label_surf, label_rect)
        rect = self.draw_card_face(dx, dy, card, show_power_label=True, show_pips=False)
        return rect

    def draw_peek_reveal(self):
        if self.peek_reveal is None or self.peek_reveal['timer'] <= 0:
            return
        card = self.peek_reveal['card']
        rx = self.peek_reveal['x']
        ry = self.peek_reveal['y']
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        label_surf = self.ui_font.render("You saw:", True, GOLD)
        label_rect = label_surf.get_rect(center=(rx + CARD_WIDTH // 2, ry - 24))
        self.screen.blit(label_surf, label_rect)
        self.draw_card_face(rx, ry, card)
        fade_pct = min(self.peek_reveal['timer'] / 0.5, 1.0)
        border_alpha = int(255 * fade_pct)
        border_surf = pygame.Surface((CARD_WIDTH + 8, CARD_HEIGHT + 8), pygame.SRCALPHA)
        pygame.draw.rect(border_surf, (*POWER_GLOW, border_alpha), border_surf.get_rect(), 3, border_radius=CORNER_RADIUS + 2)
        self.screen.blit(border_surf, (rx - 4, ry - 4))

    def draw_game_log(self, log_entries):
        panel_rect = pygame.Rect(LOG_PANEL_X, LOG_PANEL_Y, LOG_PANEL_W, LOG_PANEL_H)
        panel_surf = pygame.Surface((LOG_PANEL_W, LOG_PANEL_H), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*PANEL_BG, 230), panel_surf.get_rect(), border_radius=8)
        pygame.draw.rect(panel_surf, (*PANEL_BORDER, 120), panel_surf.get_rect(), 1, border_radius=8)
        self.screen.blit(panel_surf, (LOG_PANEL_X, LOG_PANEL_Y))
        header_surf = self.ui_font.render("Game Log", True, GOLD)
        self.screen.blit(header_surf, (LOG_PANEL_X + 10, LOG_PANEL_Y + 8))
        pygame.draw.line(self.screen, PANEL_BORDER, (LOG_PANEL_X + 8, LOG_PANEL_Y + 32),
                         (LOG_PANEL_X + LOG_PANEL_W - 8, LOG_PANEL_Y + 32), 1)
        if not log_entries:
            return
        visible = log_entries[-10:]
        for i, entry in enumerate(visible):
            text = str(entry)
            if len(text) > 35:
                text = text[:32] + "..."
            if isinstance(entry, dict):
                text = str(entry.get('text', entry))[:35]
            entry_surf = self.log_font.render(text, True, TEXT_WHITE)
            self.screen.blit(entry_surf, (LOG_PANEL_X + 10, LOG_PANEL_Y + 38 + i * 22))

    def draw_action_buttons(self, action_buttons):
        for name, btn in action_buttons.items():
            rect = btn['rect']
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            color = btn.get('hover_color', btn['color']) if hovered else btn['color']

            shadow_surf = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (3, 4, rect.width, rect.height), border_radius=8)
            self.screen.blit(shadow_surf, (rect.x - 3, rect.y + 2))

            self._draw_rounded_rect(self.screen, color, rect, 8)

            c_r = max(color[0] - 30, 0)
            c_g = max(color[1] - 30, 0)
            c_b = max(color[2] - 30, 0)
            pygame.draw.line(self.screen, (c_r, c_g, c_b),
                            (rect.left + 3, rect.bottom - 3), (rect.right - 3, rect.bottom - 3), 2)
            pygame.draw.line(self.screen, (c_r, c_g, c_b),
                            (rect.right - 3, rect.top + 3), (rect.right - 3, rect.bottom - 3), 2)

            l_r = min(color[0] + 40, 255)
            l_g = min(color[1] + 40, 255)
            l_b = min(color[2] + 40, 255)
            pygame.draw.line(self.screen, (l_r, l_g, l_b),
                            (rect.left + 3, rect.top + 3), (rect.right - 3, rect.top + 3), 2)
            pygame.draw.line(self.screen, (l_r, l_g, l_b),
                            (rect.left + 3, rect.top + 3), (rect.left + 3, rect.bottom - 3), 2)

            pygame.draw.rect(self.screen, (20, 20, 25), rect, 1, border_radius=8)
            text_surf = self.ui_font.render(btn['text'], True, TEXT_WHITE)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def _draw_cancel_button(self, cancel_button, mouse_pos):
        rect = cancel_button['rect']
        hovered = rect.collidepoint(mouse_pos)
        color = CANCEL_GRAY_HOVER if hovered else CANCEL_GRAY

        shadow_surf = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 70), (3, 4, rect.width, rect.height), border_radius=8)
        self.screen.blit(shadow_surf, (rect.x - 3, rect.y + 2))

        self._draw_rounded_rect(self.screen, color, rect, 8)

        c_r = max(color[0] - 30, 0)
        c_g = max(color[1] - 30, 0)
        c_b = max(color[2] - 30, 0)
        pygame.draw.line(self.screen, (c_r, c_g, c_b),
                        (rect.left + 3, rect.bottom - 3), (rect.right - 3, rect.bottom - 3), 2)
        pygame.draw.line(self.screen, (c_r, c_g, c_b),
                        (rect.right - 3, rect.top + 3), (rect.right - 3, rect.bottom - 3), 2)

        l_r = min(color[0] + 40, 255)
        l_g = min(color[1] + 40, 255)
        l_b = min(color[2] + 40, 255)
        pygame.draw.line(self.screen, (l_r, l_g, l_b),
                        (rect.left + 3, rect.top + 3), (rect.right - 3, rect.top + 3), 2)
        pygame.draw.line(self.screen, (l_r, l_g, l_b),
                        (rect.left + 3, rect.top + 3), (rect.left + 3, rect.bottom - 3), 2)
        pygame.draw.rect(self.screen, (20, 20, 25), rect, 1, border_radius=8)
        text_surf = self.ui_font.render(cancel_button.get('text', 'Cancel'), True, TEXT_WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_status_message(self, message):
        if not message:
            return
        msg_surf = self.ui_font.render(message, True, GOLD)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, ACTION_BAR_Y - 20))
        bg_rect = msg_rect.inflate(32, 16)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), border_radius=8)
        pygame.draw.rect(bg_surf, (*GOLD_DIM, 80), bg_surf.get_rect(), 1, border_radius=8)
        self.screen.blit(bg_surf, bg_rect.topleft)
        self.screen.blit(msg_surf, msg_rect)

    def get_card_rects(self, player_index, game_manager):
        player = game_manager.players[player_index]
        num_players = len(game_manager.players)
        pos = _get_seat_position(player.seat_index, num_players)
        card_positions = self._compute_card_positions(player, pos, game_manager)
        rects = []
        for slot_index in range(len(player.hand)):
            if slot_index < len(card_positions):
                cx, cy = card_positions[slot_index]
                rects.append(pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT))
            else:
                rects.append(pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT))
        return rects

    def get_card_center(self, player_index, slot_index, game_manager):
        rects = self.get_card_rects(player_index, game_manager)
        if slot_index < len(rects):
            r = rects[slot_index]
            return (r.centerx, r.centery)
        return (0, 0)

    def get_deck_rect(self):
        cx, cy = DECK_CENTER
        return pygame.Rect(cx - CARD_WIDTH // 2, cy - CARD_HEIGHT // 2, CARD_WIDTH, CARD_HEIGHT)

    def update(self, dt):
        self._pulse_time += dt
        if self.peek_reveal is not None:
            self.peek_reveal['timer'] -= dt
            if self.peek_reveal['timer'] <= 0:
                self.peek_reveal = None
        self.animation_queue.update(dt)

    def set_peek_reveal(self, card, x, y, duration):
        self.peek_reveal = {'card': card, 'x': x, 'y': y, 'timer': duration}

    def is_animating(self):
        return self.animation_queue.is_animating()

    def set_game_settings(self, settings):
        self.game_settings = settings

    def effective_anim_duration(self, base_duration):
        if self.game_settings and not self.game_settings.animations_enabled:
            return 0.01
        return base_duration

    def push_draw_animation(self, game_manager):
        deck_cx, deck_cy = DECK_CENTER
        drawn_cx, drawn_cy = DRAWN_CARD_POS
        event = VisualEvent(
            VisualEventType.CARD_SLIDE,
            start_pos=(deck_cx, deck_cy),
            end_pos=(drawn_cx, drawn_cy),
            card=game_manager.drawn_card,
            duration=self.effective_anim_duration(ANIM_DRAW_DURATION),
            start_face_up=True,
        )
        self.animation_queue.add(event)

    def push_swap_animation(self, game_manager, slot_index, swapped_card):
        drawn_cx, drawn_cy = DRAWN_CARD_POS
        human_idx = None
        for i, p in enumerate(game_manager.players):
            if p.is_human:
                human_idx = i
                break
        if human_idx is None:
            return
        slot_center = self.get_card_center(human_idx, slot_index, game_manager)
        discard_cx, discard_cy = DISCARD_POS
        slide_to_slot = VisualEvent(
            VisualEventType.CARD_SLIDE,
            start_pos=(drawn_cx, drawn_cy),
            end_pos=slot_center,
            card=game_manager.drawn_card,
            duration=self.effective_anim_duration(ANIM_SWAP_DURATION),
            start_face_up=True,
        )
        fade_to_discard = VisualEvent(
            VisualEventType.CARD_FADE_OUT,
            start_pos=slot_center,
            end_pos=(discard_cx, discard_cy),
            card=swapped_card,
            duration=self.effective_anim_duration(ANIM_SWAP_DURATION),
            start_face_up=True,
            start_scale=1.0,
            end_scale=0.6,
        )
        self.animation_queue.add(slide_to_slot)
        self.animation_queue.add(fade_to_discard)

    def push_unseen_swap_animation(self, game_manager, my_slot, target_player_idx, their_slot):
        human_idx = None
        for i, p in enumerate(game_manager.players):
            if p.is_human:
                human_idx = i
                break
        if human_idx is None:
            return
        my_center = self.get_card_center(human_idx, my_slot, game_manager)
        their_center = self.get_card_center(target_player_idx, their_slot, game_manager)
        my_card = game_manager.players[human_idx].hand[my_slot]
        their_card = game_manager.players[target_player_idx].hand[their_slot]
        arc_my = VisualEvent(
            VisualEventType.CARD_ARC,
            start_pos=my_center,
            end_pos=their_center,
            card=my_card,
            duration=self.effective_anim_duration(ANIM_UNSEEN_SWAP_DURATION),
            arc_height=80,
            start_face_up=False,
        )
        arc_their = VisualEvent(
            VisualEventType.CARD_ARC,
            start_pos=their_center,
            end_pos=my_center,
            card=their_card,
            duration=self.effective_anim_duration(ANIM_UNSEEN_SWAP_DURATION),
            arc_height=80,
            start_face_up=False,
        )
        flash = VisualEvent(
            VisualEventType.SCREEN_FLASH,
            start_pos=(0, 0),
            end_pos=(0, 0),
            duration=self.effective_anim_duration(ANIM_FLASH_DURATION),
            text_color=SWAP_GREEN,
        )
        self.animation_queue.add(flash)
        self.animation_queue.add(arc_my)
        self.animation_queue.add(arc_their)

    def push_seen_swap_animation(self, game_manager, my_slot, target_player_idx, their_slot, card_received):
        human_idx = None
        for i, p in enumerate(game_manager.players):
            if p.is_human:
                human_idx = i
                break
        if human_idx is None:
            return
        my_center = self.get_card_center(human_idx, my_slot, game_manager)
        their_center = self.get_card_center(target_player_idx, their_slot, game_manager)
        my_card = game_manager.players[human_idx].hand[my_slot]
        arc_my = VisualEvent(
            VisualEventType.CARD_ARC,
            start_pos=my_center,
            end_pos=their_center,
            card=my_card,
            duration=self.effective_anim_duration(ANIM_SEEN_SWAP_DURATION),
            arc_height=80,
            start_face_up=False,
        )
        arc_their = VisualEvent(
            VisualEventType.CARD_FLIP_ARC,
            start_pos=their_center,
            end_pos=my_center,
            card=card_received,
            duration=self.effective_anim_duration(ANIM_SEEN_SWAP_DURATION),
            arc_height=80,
            flip_at_peak=True,
            start_face_up=False,
            face_up_at_end=False,
        )
        flash = VisualEvent(
            VisualEventType.SCREEN_FLASH,
            start_pos=(0, 0),
            end_pos=(0, 0),
            duration=self.effective_anim_duration(ANIM_FLASH_DURATION),
            text_color=SWAP_GREEN,
        )
        self.animation_queue.add(flash)
        self.animation_queue.add(arc_my)
        self.animation_queue.add(arc_their)
        note_y = (my_center[1] + their_center[1]) / 2 - 60
        note_x = (my_center[0] + their_center[0]) / 2
        notif = VisualEvent(
            VisualEventType.NOTIFICATION_TEXT,
            start_pos=(note_x, note_y),
            end_pos=(note_x, note_y),
            duration=self.effective_anim_duration(ANIM_NOTIFICATION_DURATION),
            text=f"Received: {card_received.display_name}",
            text_color=GOLD,
        )
        self.animation_queue.add(notif)

    def push_discard_animation(self, game_manager):
        drawn_cx, drawn_cy = DRAWN_CARD_POS
        discard_cx, discard_cy = DISCARD_POS
        event = VisualEvent(
            VisualEventType.CARD_SLIDE,
            start_pos=(drawn_cx, drawn_cy),
            end_pos=(discard_cx, discard_cy),
            card=game_manager.drawn_card,
            duration=self.effective_anim_duration(ANIM_DISCARD_DURATION),
            start_face_up=True,
        )
        self.animation_queue.add(event)

    def push_peek_lift_animation(self, game_manager, target_pos):
        event = VisualEvent(
            VisualEventType.CARD_LIFT,
            start_pos=target_pos,
            end_pos=(target_pos[0], target_pos[1] - 15),
            duration=self.effective_anim_duration(ANIM_PEEK_LIFT_DURATION),
            start_face_up=False,
        )
        self.animation_queue.add(event)

    def push_pair_fly_animation(self, game_manager, pos1, card1, pos2=None, card2=None):
        discard_cx, discard_cy = DISCARD_POS
        fly1 = VisualEvent(
            VisualEventType.CARD_FADE_OUT,
            start_pos=pos1,
            end_pos=(discard_cx, discard_cy),
            card=card1,
            duration=self.effective_anim_duration(ANIM_PAIR_FLY_DURATION),
            start_face_up=True,
            start_scale=1.0,
            end_scale=0.5,
        )
        self.animation_queue.add(fly1)
        if pos2 is not None and card2 is not None:
            fly2 = VisualEvent(
                VisualEventType.CARD_FADE_OUT,
                start_pos=pos2,
                end_pos=(discard_cx + 30, discard_cy),
                card=card2,
                duration=self.effective_anim_duration(ANIM_PAIR_FLY_DURATION),
                start_face_up=True,
                start_scale=1.0,
                end_scale=0.5,
            )
            self.animation_queue.add(fly2)
        flash = VisualEvent(
            VisualEventType.SCREEN_FLASH,
            start_pos=(0, 0),
            end_pos=(0, 0),
            duration=self.effective_anim_duration(ANIM_FLASH_DURATION),
            text_color=PAIR_TEAL,
        )
        self.animation_queue.add(flash)

    def push_ai_peek_animation(self, player_idx, slot_idx, game_manager):
        center = self.get_card_center(player_idx, slot_idx, game_manager)
        lift = VisualEvent(
            VisualEventType.CARD_LIFT,
            start_pos=center,
            end_pos=(center[0], center[1] - 15),
            duration=self.effective_anim_duration(ANIM_PEEK_LIFT_DURATION),
            start_face_up=False,
        )
        pos = _get_seat_position(game_manager.players[player_idx].seat_index, len(game_manager.players))
        notif = VisualEvent(
            VisualEventType.NOTIFICATION_TEXT,
            start_pos=(pos[0], pos[1] - 60),
            end_pos=(pos[0], pos[1] - 60),
            duration=self.effective_anim_duration(ANIM_NOTIFICATION_DURATION),
            text=f"{game_manager.players[player_idx].name} peeked!",
            text_color=PEEK_BLUE,
        )
        self.animation_queue.add(lift)
        self.animation_queue.add(notif)

    def push_ai_swap_animation(self, game_manager, target_player_idx, their_slot):
        their_center = self.get_card_center(target_player_idx, their_slot, game_manager)
        discard_cx, discard_cy = DISCARD_POS
        fade_to_discard = VisualEvent(
            VisualEventType.CARD_FADE_OUT,
            start_pos=their_center,
            end_pos=(discard_cx, discard_cy),
            duration=self.effective_anim_duration(ANIM_SWAP_DURATION),
            start_face_up=False,
            start_scale=1.0,
            end_scale=0.6,
        )
        self.animation_queue.add(fade_to_discard)

    def push_ai_skip_animation(self, game_manager, player_idx):
        pos = _get_seat_position(game_manager.players[player_idx].seat_index, len(game_manager.players))
        notif = VisualEvent(
            VisualEventType.NOTIFICATION_TEXT,
            start_pos=(pos[0], pos[1] - 60),
            end_pos=(pos[0], pos[1] - 60),
            duration=self.effective_anim_duration(ANIM_NOTIFICATION_DURATION),
            text="Skip next player!",
            text_color=DECLARE_RED,
        )
        flash = VisualEvent(
            VisualEventType.SCREEN_FLASH,
            start_pos=(0, 0),
            end_pos=(0, 0),
            duration=self.effective_anim_duration(ANIM_FLASH_DURATION),
            text_color=GOLD,
        )
        self.animation_queue.add(flash)
        self.animation_queue.add(notif)

    def push_ai_pair_animation(self, game_manager, pos1, pos2=None):
        discard_cx, discard_cy = DISCARD_POS
        fly1 = VisualEvent(
            VisualEventType.CARD_FADE_OUT,
            start_pos=pos1,
            end_pos=(discard_cx, discard_cy),
            duration=self.effective_anim_duration(ANIM_PAIR_FLY_DURATION),
            start_face_up=False,
            start_scale=1.0,
            end_scale=0.5,
        )
        self.animation_queue.add(fly1)
        if pos2 is not None:
            fly2 = VisualEvent(
                VisualEventType.CARD_FADE_OUT,
                start_pos=pos2,
                end_pos=(discard_cx + 30, discard_cy),
                duration=self.effective_anim_duration(ANIM_PAIR_FLY_DURATION),
                start_face_up=False,
                start_scale=1.0,
                end_scale=0.5,
            )
            self.animation_queue.add(fly2)
        flash = VisualEvent(
            VisualEventType.SCREEN_FLASH,
            start_pos=(0, 0),
            end_pos=(0, 0),
            duration=self.effective_anim_duration(ANIM_FLASH_DURATION),
            text_color=PAIR_TEAL,
        )
        self.animation_queue.add(flash)

    def _draw_rounded_rect(self, surface, color, rect, radius):
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def _draw_dashed_rect(self, surface, color, rect, radius=0):
        dash_len = 8
        gap_len = 6
        points = [
            (rect.left, rect.top), (rect.right, rect.top),
            (rect.right, rect.bottom), (rect.left, rect.bottom)
        ]
        for i in range(4):
            start = points[i]
            end = points[(i + 1) % 4]
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length == 0:
                continue
            ux = dx / length
            uy = dy / length
            pos = 0
            drawing = True
            while pos < length:
                seg = dash_len if drawing else gap_len
                seg = min(seg, length - pos)
                if drawing:
                    sx = int(start[0] + ux * pos)
                    sy = int(start[1] + uy * pos)
                    ex = int(start[0] + ux * (pos + seg))
                    ey = int(start[1] + uy * (pos + seg))
                    pygame.draw.line(surface, color, (sx, sy), (ex, ey), 1)
                pos += seg
                drawing = not drawing

    def _draw_shadow(self, x, y):
        shadow_surf = pygame.Surface((CARD_WIDTH + 12, CARD_HEIGHT + 12), pygame.SRCALPHA)
        for i in range(4, 0, -1):
            alpha = 15 + i * 15
            offset = i * 2
            pygame.draw.rect(shadow_surf, (0, 0, 0, alpha),
                             (offset, offset + 2, CARD_WIDTH, CARD_HEIGHT),
                             border_radius=CORNER_RADIUS)
        self.screen.blit(shadow_surf, (x - 6, y - 4))

    def draw_gear_icon(self, mouse_pos, settings_open=False):
        rect = self.get_gear_rect()
        cx, cy = rect.centerx, rect.centery
        hovered = rect.collidepoint(mouse_pos)
        color = GOLD if hovered or settings_open else TEXT_DIM
        radius = 10
        teeth = 8
        tooth_len = 5
        tooth_width = 3
        pts = []
        for i in range(teeth * 2):
            angle = math.pi * 2 * i / (teeth * 2) - math.pi / 2
            if i % 2 == 0:
                r = radius + tooth_len
            else:
                r = radius
                angle += tooth_width / radius
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if len(pts) > 2:
            pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.circle(self.screen, BG_DARK, (cx, cy), 4)
        pygame.draw.circle(self.screen, color, (cx, cy), 4, 1)

    def get_gear_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 52, 8, 40, 34)