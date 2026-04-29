import math
import pygame
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, BG_GREEN, BG_DARK, CARD_WHITE, CARD_BACK_BLUE,
    CARD_BACK_PATTERN, CARD_SHADOW, BLACK, RED, GOLD, TEXT_WHITE, TEXT_BLACK, TEXT_DIM,
    HIGHLIGHT, DIM, PANEL_BG, PANEL_BORDER, POWER_GLOW, EMPTY_SLOT, KNOWN_TINT,
    DECLARE_RED, DECLARE_RED_HOVER, CANCEL_GRAY, CANCEL_GRAY_HOVER,
    PEEK_BLUE, PEEK_BLUE_HOVER, SWAP_GREEN, SWAP_GREEN_HOVER,
    DISCARD_ORANGE, DISCARD_ORANGE_HOVER, PAIR_TEAL, PAIR_TEAL_HOVER,
    STATUS_BAR_H, ACTION_BAR_Y, ACTION_BAR_H,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD,
    DECK_CENTER, DRAWN_CARD_POS, DISCARD_POS,
    PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    LOG_PANEL_X, LOG_PANEL_Y, LOG_PANEL_W, LOG_PANEL_H,
    CARD_FONT_SIZE, CARD_BIG_FONT_SIZE, TITLE_FONT_SIZE, SUBTITLE_FONT_SIZE,
    UI_FONT_SIZE, LOG_FONT_SIZE, SMALL_FONT_SIZE,
    POWER_LABELS, POWER_COLORS, HAND_SIZE)
from game.card import Card
from game.player import Player
from game.game_manager import GameManager, GameState

SEAT_POSITIONS_2 = {0: PLAYER_BOTTOM, 1: PLAYER_TOP}
SEAT_POSITIONS_3 = {0: PLAYER_BOTTOM, 1: (380, 170), 2: (900, 170)}
SEAT_POSITIONS_4 = {0: PLAYER_BOTTOM, 1: PLAYER_LEFT, 2: PLAYER_TOP, 3: PLAYER_RIGHT}

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
        self.peek_reveal = None
        self._pulse_time = 0.0

    def draw(self, game_manager, mouse_pos=(0, 0), action_buttons=None, cancel_button=None, status_message="", awaiting_target=None):
        self.screen.fill(BG_GREEN)
        self._draw_table_felt()
        self._draw_status_bar(game_manager)
        self.draw_discard(game_manager.discard_pile)
        self.draw_deck(game_manager.deck.remaining if game_manager.deck else 0)
        if game_manager.drawn_card:
            self.draw_drawn_card(game_manager.drawn_card)
        num_players = len(game_manager.players)
        for player in game_manager.players:
            pos = _get_seat_position(player.seat_index, num_players)
            is_current = player.seat_index == game_manager.current_player_index
            is_human = player.is_human
            self.draw_player_area(player, pos, is_current, is_human, game_manager, mouse_pos)
        self.draw_peek_reveal()
        self.draw_game_log(game_manager.game_log)
        if action_buttons:
            self.draw_action_buttons(action_buttons)
        if cancel_button:
            self._draw_cancel_button(cancel_button, mouse_pos)
        if status_message:
            self.draw_status_message(status_message)

    def _draw_table_felt(self):
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        rx, ry = 480, 260
        felt_surf = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(felt_surf, (30, 95, 50, 80), (0, 0, rx * 2, ry * 2))
        self.screen.blit(felt_surf, (center[0] - rx, center[1] - ry))
        pygame.draw.ellipse(self.screen, (50, 130, 70), (center[0] - rx, center[1] - ry, rx * 2, ry * 2), 2)

    def _draw_status_bar(self, game_manager):
        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, STATUS_BAR_H)
        pygame.draw.rect(self.screen, BG_DARK, bar_rect)
        pygame.draw.line(self.screen, PANEL_BORDER, (0, STATUS_BAR_H), (SCREEN_WIDTH, STATUS_BAR_H))
        state_label = STATE_LABELS.get(game_manager.state, str(game_manager.state.value))
        current_player = game_manager.current_player()
        round_surf = self.ui_font.render(f"Round {game_manager.round_number}", True, TEXT_DIM)
        self.screen.blit(round_surf, (12, (STATUS_BAR_H - round_surf.get_height()) // 2))
        name_surf = self.ui_font.render(current_player.name, True, GOLD)
        self.screen.blit(name_surf, (120, (STATUS_BAR_H - name_surf.get_height()) // 2))
        state_surf = self.small_font.render(state_label, True, TEXT_DIM)
        self.screen.blit(state_surf, (120 + name_surf.get_width() + 12, (STATUS_BAR_H - state_surf.get_height()) // 2 + 1))

    def draw_card_face(self, x, y, card, selected=False, hovered=False, show_power_label=False):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._draw_shadow(x, y)
        bg_color = CARD_WHITE
        if hovered:
            bg_color = (255, 255, 230)
        self._draw_rounded_rect(self.screen, bg_color, rect, CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        big_surf = self.card_big_font.render(card.rank, True, color)
        big_rect = big_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2 - 8))
        self.screen.blit(big_surf, big_rect)
        suit_surf = self.card_font.render(card.suit_symbol, True, color)
        suit_rect = suit_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2 + 16))
        self.screen.blit(suit_surf, suit_rect)
        corner_text = f"{card.rank}{card.suit_symbol}"
        tl_surf = self.small_font.render(corner_text, True, color)
        self.screen.blit(tl_surf, (x + 5, y + 4))
        br_surf = self.small_font.render(corner_text, True, color)
        br_rect = br_surf.get_rect(bottomright=(x + CARD_WIDTH - 5, y + CARD_HEIGHT - 4))
        self.screen.blit(br_surf, br_rect)
        if show_power_label and card.power is not None:
            power_color = POWER_COLORS.get(card.power, TEXT_WHITE)
            power_label = POWER_LABELS.get(card.power, card.power)
            p_surf = self.small_font.render(power_label, True, power_color)
            p_rect = p_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT + 12))
            self.screen.blit(p_surf, p_rect)
        if selected:
            pygame.draw.rect(self.screen, GOLD, rect, 3, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (180, 180, 180), rect, 1, border_radius=CORNER_RADIUS)
        return rect

    def draw_card_back(self, x, y, has_known_marker=False):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._draw_shadow(x, y)
        self._draw_rounded_rect(self.screen, CARD_BACK_BLUE, rect, CORNER_RADIUS)
        inner = pygame.Rect(x + 6, y + 6, CARD_WIDTH - 12, CARD_HEIGHT - 12)
        pygame.draw.rect(self.screen, CARD_BACK_PATTERN, inner, border_radius=CORNER_RADIUS - 2)
        dcx = x + CARD_WIDTH // 2
        dcy = y + CARD_HEIGHT // 2
        pts = [(dcx, dcy - 18), (dcx + 12, dcy), (dcx, dcy + 18), (dcx - 12, dcy)]
        pygame.draw.polygon(self.screen, (80, 120, 190), pts)
        pygame.draw.polygon(self.screen, TEXT_WHITE, pts, 1)
        pygame.draw.rect(self.screen, TEXT_WHITE, rect, 1, border_radius=CORNER_RADIUS)
        if has_known_marker:
            tri_size = 10
            tri_pts = [
                (x + CARD_WIDTH - 2, y + 2),
                (x + CARD_WIDTH - 2, y + 2 + tri_size),
                (x + CARD_WIDTH - 2 - tri_size, y + 2),
            ]
            pygame.draw.polygon(self.screen, GOLD, tri_pts)
        return rect

    def draw_empty_slot(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self._draw_dashed_rect(self.screen, EMPTY_SLOT, rect, CORNER_RADIUS)
        return rect

    def draw_deck(self, remaining):
        cx, cy = DECK_CENTER
        dx = cx - CARD_WIDTH // 2
        dy = cy - CARD_HEIGHT // 2
        if remaining > 0:
            stack_count = min(remaining, 4)
            for i in range(stack_count):
                shadow_rect = pygame.Rect(dx - i * 2, dy - i * 2, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, (20, 45, 95), shadow_rect, border_radius=CORNER_RADIUS)
            top_rect = pygame.Rect(dx, dy, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(self.screen, CARD_BACK_BLUE, top_rect, border_radius=CORNER_RADIUS)
            inner = pygame.Rect(dx + 6, dy + 6, CARD_WIDTH - 12, CARD_HEIGHT - 12)
            pygame.draw.rect(self.screen, CARD_BACK_PATTERN, inner, border_radius=CORNER_RADIUS - 2)
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
        num_players = len(game_manager.players)
        total_width = HAND_SIZE * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
        start_x = px - total_width // 2
        start_y = py - CARD_HEIGHT // 2 + 4
        name_color = GOLD if is_current else TEXT_WHITE
        name_y = start_y - 28
        name_surf = self.ui_font.render(player.name, True, name_color)
        name_rect = name_surf.get_rect(center=(px, name_y + name_surf.get_height() // 2))
        self.screen.blit(name_surf, name_rect)
        if is_current:
            alpha = int(80 + 40 * math.sin(self._pulse_time * 3))
            glow_rect = name_rect.inflate(20, 10)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*GOLD, alpha), glow_surf.get_rect(), border_radius=6)
            self.screen.blit(glow_surf, glow_rect.topleft)
            self.screen.blit(name_surf, name_rect)
        info_y = name_y + name_surf.get_height() + 2
        if is_human:
            info_text = f"Cards: {player.card_count} | Score: ???"
        else:
            info_text = f"Cards: {player.card_count}"
        info_surf = self.small_font.render(info_text, True, TEXT_DIM)
        info_rect = info_surf.get_rect(center=(px, info_y + info_surf.get_height() // 2))
        self.screen.blit(info_surf, info_rect)
        if is_current and is_human:
            arrow_surf = self.small_font.render("\u25b6 YOUR TURN", True, GOLD)
            arrow_rect = arrow_surf.get_rect(center=(px, info_y + info_surf.get_height() + 12))
            self.screen.blit(arrow_surf, arrow_rect)
        card_rects = []
        for slot_index in range(HAND_SIZE):
            card = player.hand[slot_index]
            cx = start_x + slot_index * CARD_SPREAD
            cy = start_y
            slot_rect = pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT)
            hovered = (mouse_pos[0] >= slot_rect.left and mouse_pos[0] <= slot_rect.right
                       and mouse_pos[1] >= slot_rect.top and mouse_pos[1] <= slot_rect.bottom)
            if card is None:
                self.draw_empty_slot(cx, cy)
            elif is_human:
                has_marker = slot_index in player.known_cards
                self.draw_card_back(cx, cy, has_known_marker=has_marker)
            else:
                self.draw_card_back(cx, cy, has_known_marker=False)
            card_rects.append((slot_rect, slot_index))
        return card_rects

    def draw_drawn_card(self, card):
        cx, cy = DRAWN_CARD_POS
        dx = cx - CARD_WIDTH // 2
        dy = cy - CARD_HEIGHT // 2
        label_surf = self.small_font.render("DREW", True, GOLD)
        label_rect = label_surf.get_rect(center=(cx, dy - 12))
        self.screen.blit(label_surf, label_rect)
        rect = self.draw_card_face(dx, dy, card, show_power_label=True)
        if card.power is not None:
            power_color = POWER_COLORS.get(card.power, TEXT_WHITE)
            power_label = POWER_LABELS.get(card.power, card.power)
            p_surf = self.small_font.render(power_label, True, power_color)
            p_rect = p_surf.get_rect(center=(cx, dy + CARD_HEIGHT + 12))
            self.screen.blit(p_surf, p_rect)
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
        panel_surf.fill((*PANEL_BG, 220))
        self.screen.blit(panel_surf, (LOG_PANEL_X, LOG_PANEL_Y))
        pygame.draw.rect(self.screen, PANEL_BORDER, panel_rect, 1, border_radius=4)
        header_surf = self.ui_font.render("Game Log", True, GOLD)
        self.screen.blit(header_surf, (LOG_PANEL_X + 8, LOG_PANEL_Y + 6))
        pygame.draw.line(self.screen, PANEL_BORDER, (LOG_PANEL_X + 4, LOG_PANEL_Y + 30), (LOG_PANEL_X + LOG_PANEL_W - 4, LOG_PANEL_Y + 30))
        if not log_entries:
            return
        visible = log_entries[-8:]
        for i, entry in enumerate(visible):
            text = str(entry)
            if len(text) > 35:
                text = text[:32] + "..."
            if isinstance(entry, dict):
                text = str(entry.get('text', entry))[:35]
            entry_surf = self.log_font.render(text, True, TEXT_WHITE)
            self.screen.blit(entry_surf, (LOG_PANEL_X + 8, LOG_PANEL_Y + 36 + i * 22))

    def draw_action_buttons(self, action_buttons):
        for name, btn in action_buttons.items():
            rect = btn['rect']
            color = btn.get('hover_color', btn['color']) if rect.collidepoint(pygame.mouse.get_pos()) else btn['color']
            self._draw_rounded_rect(self.screen, color, rect, 8)
            pygame.draw.rect(self.screen, TEXT_WHITE, rect, 1, border_radius=8)
            text_surf = self.ui_font.render(btn['text'], True, TEXT_WHITE)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

    def _draw_cancel_button(self, cancel_button, mouse_pos):
        rect = cancel_button['rect']
        hovered = rect.collidepoint(mouse_pos)
        color = CANCEL_GRAY_HOVER if hovered else CANCEL_GRAY
        self._draw_rounded_rect(self.screen, color, rect, 8)
        pygame.draw.rect(self.screen, TEXT_WHITE, rect, 1, border_radius=8)
        text_surf = self.ui_font.render(cancel_button.get('text', 'Cancel'), True, TEXT_WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw_status_message(self, message):
        if not message:
            return
        msg_surf = self.ui_font.render(message, True, GOLD)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, ACTION_BAR_Y - 20))
        bg_rect = msg_rect.inflate(24, 12)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 160), bg_surf.get_rect(), border_radius=6)
        self.screen.blit(bg_surf, bg_rect.topleft)
        self.screen.blit(msg_surf, msg_rect)

    def get_card_rects(self, player_index, game_manager):
        player = game_manager.players[player_index]
        num_players = len(game_manager.players)
        pos = _get_seat_position(player.seat_index, num_players)
        px, py = pos
        total_width = HAND_SIZE * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
        start_x = px - total_width // 2
        start_y = py - CARD_HEIGHT // 2 + 4
        rects = []
        for slot_index in range(HAND_SIZE):
            cx = start_x + slot_index * CARD_SPREAD
            cy = start_y
            rects.append(pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT))
        return rects

    def get_deck_rect(self):
        cx, cy = DECK_CENTER
        return pygame.Rect(cx - CARD_WIDTH // 2, cy - CARD_HEIGHT // 2, CARD_WIDTH, CARD_HEIGHT)

    def update(self, dt):
        self._pulse_time += dt
        if self.peek_reveal is not None:
            self.peek_reveal['timer'] -= dt
            if self.peek_reveal['timer'] <= 0:
                self.peek_reveal = None

    def set_peek_reveal(self, card, x, y, duration):
        self.peek_reveal = {'card': card, 'x': x, 'y': y, 'timer': duration}

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
        shadow_rect = pygame.Rect(x + 2, y + 2, CARD_WIDTH, CARD_HEIGHT)
        shadow_surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
        shadow_surf.fill((*CARD_SHADOW, 80))
        self.screen.blit(shadow_surf, (x + 2, y + 2))