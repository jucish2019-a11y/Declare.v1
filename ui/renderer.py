import pygame
from enum import Enum

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    BG_GREEN,
    CARD_WHITE,
    CARD_BACK_BLUE,
    BLACK,
    RED,
    GOLD,
    TEXT_WHITE,
    TEXT_BLACK,
    HIGHLIGHT,
    DIM,
    CARD_WIDTH,
    CARD_HEIGHT,
    CORNER_RADIUS,
    CARD_SPREAD,
    DECK_POSITION,
    PLAYER_BOTTOM,
    PLAYER_TOP,
    PLAYER_LEFT,
    PLAYER_RIGHT,
    CARD_FONT_SIZE,
    TITLE_FONT_SIZE,
    UI_FONT_SIZE,
    LOG_FONT_SIZE,
    HAND_SIZE,
)
from game.card import Card
from game.player import Player
from game.game_manager import GameManager, GameState

SEAT_POSITIONS = {
    0: PLAYER_BOTTOM,
    1: PLAYER_LEFT,
    2: PLAYER_TOP,
    3: PLAYER_RIGHT,
}

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

ACTION_LABELS = {
    "draw": "Draw",
    "swap": "Swap",
    "discard": "Discard",
    "play_power": "Play Power",
    "pair_own": "Pair Own",
    "pair_opponent": "Pair Opponent",
    "declare": "Declare",
}

LOG_PANEL_WIDTH = 280
LOG_PANEL_HEIGHT = 180
LOG_PANEL_MARGIN = 10
LOG_LINE_SPACING = 20


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.card_font = pygame.font.SysFont("arial", CARD_FONT_SIZE, bold=True)
        self.title_font = pygame.font.SysFont("arial", TITLE_FONT_SIZE, bold=True)
        self.ui_font = pygame.font.SysFont("arial", UI_FONT_SIZE)
        self.log_font = pygame.font.SysFont("arial", LOG_FONT_SIZE)
        self._card_cache: dict = {}

    def draw(self, game_manager: GameManager, selected_slot=None, hovered_slot=None, animation_state=None):
        self.screen.fill(BG_GREEN)
        self._draw_table_background()
        self._draw_deck_and_discard(game_manager)
        for player in game_manager.players:
            pos = SEAT_POSITIONS[player.seat_index]
            is_current = player.seat_index == game_manager.current_player_index
            is_human_viewing = player.is_human
            self.draw_player_area(player, pos, is_current, is_human_viewing)
        if game_manager.drawn_card:
            self.draw_drawn_card(game_manager.drawn_card)
        if selected_slot is not None:
            pass
        if hovered_slot is not None:
            pass
        self.draw_status_bar(game_manager)
        self.draw_game_log(game_manager.game_log)
        info = game_manager.get_game_state_info()
        self.draw_action_buttons(info.get("valid_actions", []))

    def _draw_table_background(self):
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        rx, ry = 500, 280
        darker_green = (30, 95, 50)
        pygame.draw.ellipse(self.screen, darker_green, (center[0] - rx, center[1] - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(self.screen, (50, 130, 70), (center[0] - rx, center[1] - ry, rx * 2, ry * 2), 3)

    def _draw_deck_and_discard(self, game_manager: GameManager):
        remaining = game_manager.deck.remaining if game_manager.deck else 0
        self.draw_deck(remaining)
        if game_manager.discard_pile:
            self.draw_discard_pile(game_manager.discard_pile)

    def draw_card(self, x, y, card: Card = None, face_up=False, selected=False, highlighted=False) -> pygame.Rect:
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        if not face_up or card is None:
            self.draw_card_back(x, y)
            if selected:
                pygame.draw.rect(self.screen, GOLD, rect, 3, border_radius=CORNER_RADIUS)
            return rect

        bg_color = CARD_WHITE
        if highlighted:
            bg_color = HIGHLIGHT
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=CORNER_RADIUS)

        rank_surf, suit_surf = self._render_card_text(card)
        rank_rect = rank_surf.get_rect(topleft=(x + 5, y + 5))
        suit_rect = suit_surf.get_rect(topleft=(x + 5, y + 5 + CARD_FONT_SIZE))
        self.screen.blit(rank_surf, rank_rect)
        self.screen.blit(suit_surf, suit_rect)

        center_rank = pygame.transform.scale(rank_surf, (int(rank_surf.get_width() * 1.5), int(rank_surf.get_height() * 1.5)))
        center_suit = pygame.transform.scale(suit_surf, (int(suit_surf.get_width() * 1.5), int(suit_surf.get_height() * 1.5)))
        cx = x + CARD_WIDTH // 2
        cy = y + CARD_HEIGHT // 2
        cr_rect = center_rank.get_rect(center=(cx, cy - 10))
        cs_rect = center_suit.get_rect(center=(cx, cy + 14))
        self.screen.blit(center_rank, cr_rect)
        self.screen.blit(center_suit, cs_rect)

        if selected:
            pygame.draw.rect(self.screen, GOLD, rect, 3, border_radius=CORNER_RADIUS)

        return rect

    def draw_card_back(self, x, y) -> pygame.Rect:
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, TEXT_WHITE, rect, 2, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(x + 6, y + 6, CARD_WIDTH - 12, CARD_HEIGHT - 12)
        pygame.draw.rect(self.screen, (40, 80, 150), inner, border_radius=CORNER_RADIUS - 2)
        pygame.draw.rect(self.screen, (60, 100, 170), inner, 1, border_radius=CORNER_RADIUS - 2)
        diamond_cx = x + CARD_WIDTH // 2
        diamond_cy = y + CARD_HEIGHT // 2
        diamond_pts = [
            (diamond_cx, diamond_cy - 18),
            (diamond_cx + 12, diamond_cy),
            (diamond_cx, diamond_cy + 18),
            (diamond_cx - 12, diamond_cy),
        ]
        pygame.draw.polygon(self.screen, (80, 120, 190), diamond_pts)
        pygame.draw.polygon(self.screen, TEXT_WHITE, diamond_pts, 1)
        return rect

    def draw_deck(self, deck_remaining: int):
        dx, dy = DECK_POSITION
        dx -= CARD_WIDTH // 2
        dy -= CARD_HEIGHT // 2
        if deck_remaining > 0:
            stack_offset = min(deck_remaining, 3)
            for i in range(stack_offset):
                offset_rect = pygame.Rect(dx - i * 2, dy - i * 2, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, CARD_BACK_BLUE, offset_rect, border_radius=CORNER_RADIUS)
            pygame.draw.rect(self.screen, TEXT_WHITE, pygame.Rect(dx, dy, CARD_WIDTH, CARD_HEIGHT), 2, border_radius=CORNER_RADIUS)
            count_surf = self.log_font.render(str(deck_remaining), True, TEXT_WHITE)
            count_rect = count_surf.get_rect(center=(dx + CARD_WIDTH // 2, dy + CARD_HEIGHT + 14))
            self.screen.blit(count_surf, count_rect)
        else:
            empty_rect = pygame.Rect(dx, dy, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(self.screen, DIM, empty_rect, 2, border_radius=CORNER_RADIUS)
            empty_surf = self.log_font.render("Empty", True, DIM)
            empty_text_rect = empty_surf.get_rect(center=empty_rect.center)
            self.screen.blit(empty_surf, empty_text_rect)

    def draw_discard_pile(self, discard_pile: list):
        if not discard_pile:
            return
        top_card = discard_pile[-1]
        dx = DECK_POSITION[0] + 100
        dy = DECK_POSITION[1] - CARD_HEIGHT // 2
        top_card.face_up = True
        self.draw_card(dx, dy, top_card, face_up=True)

    def draw_player_area(self, player: Player, position: tuple, is_current: bool, is_human_viewing: bool):
        px, py = position
        name_color = GOLD if is_current else TEXT_WHITE
        name_surf = self.ui_font.render(player.name, True, name_color)
        name_rect = name_surf.get_rect(center=(px, py - CARD_HEIGHT // 2 - 20))

        if is_current:
            glow_rect = name_rect.inflate(16, 8)
            pygame.draw.rect(self.screen, (80, 80, 0), glow_rect, border_radius=4)
            pygame.draw.rect(self.screen, GOLD, glow_rect, 2, border_radius=4)
        self.screen.blit(name_surf, name_rect)

        score_surf = self.log_font.render(f"Score: {player.score}", True, TEXT_WHITE)
        score_rect = score_surf.get_rect(center=(px, py - CARD_HEIGHT // 2 - 4))
        self.screen.blit(score_surf, score_rect)

        total_width = HAND_SIZE * CARD_SPREAD + (CARD_WIDTH - CARD_SPREAD)
        start_x = px - total_width // 2
        start_y = py - CARD_HEIGHT // 2 + 4

        for i in range(HAND_SIZE):
            cx = start_x + i * CARD_SPREAD
            cy = start_y
            card = player.hand[i]
            if card is None:
                empty_rect = pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, (60, 100, 60), empty_rect, 1, border_radius=CORNER_RADIUS)
                continue

            show_face = False
            if is_human_viewing and i in player.known_cards:
                show_face = True

            self.draw_card(cx, cy, card, face_up=show_face)

        if player.card_count < HAND_SIZE:
            badge_x = px + total_width // 2 + 10
            badge_y = py - CARD_HEIGHT // 2 + 4
            count_text = str(player.card_count)
            count_surf = self.log_font.render(count_text, True, TEXT_WHITE)
            badge_radius = 10
            pygame.draw.circle(self.screen, (180, 50, 50), (badge_x, badge_y + badge_radius), badge_radius)
            text_rect = count_surf.get_rect(center=(badge_x, badge_y + badge_radius))
            self.screen.blit(count_surf, text_rect)

    def draw_drawn_card(self, card: Card):
        dx = DECK_POSITION[0] + 100 + CARD_WIDTH + 30
        dy = DECK_POSITION[1] - CARD_HEIGHT // 2
        label_surf = self.log_font.render("Drawn:", True, TEXT_WHITE)
        label_rect = label_surf.get_rect(center=(dx + CARD_WIDTH // 2, dy - 12))
        self.screen.blit(label_surf, label_rect)
        card.face_up = True
        self.draw_card(dx, dy, card, face_up=True, highlighted=True)

    def draw_game_log(self, log_entries: list):
        if not log_entries:
            return
        panel_x = SCREEN_WIDTH - LOG_PANEL_WIDTH - LOG_PANEL_MARGIN
        panel_y = SCREEN_HEIGHT - LOG_PANEL_HEIGHT - LOG_PANEL_MARGIN
        panel_rect = pygame.Rect(panel_x, panel_y, LOG_PANEL_WIDTH, LOG_PANEL_HEIGHT)
        panel_surface = pygame.Surface((LOG_PANEL_WIDTH, LOG_PANEL_HEIGHT), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 160))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (80, 80, 80), panel_rect, 1, border_radius=4)

        header_surf = self.log_font.render("Game Log", True, GOLD)
        self.screen.blit(header_surf, (panel_x + 6, panel_y + 4))
        pygame.draw.line(self.screen, GOLD, (panel_x + 4, panel_y + 22), (panel_x + LOG_PANEL_WIDTH - 4, panel_y + 22))

        visible = log_entries[-8:]
        for i, entry in enumerate(visible):
            text = str(entry)
            if len(text) > 38:
                text = text[:35] + "..."
            entry_surf = self.log_font.render(text, True, TEXT_WHITE)
            self.screen.blit(entry_surf, (panel_x + 6, panel_y + 26 + i * LOG_LINE_SPACING))

    def draw_action_buttons(self, valid_actions: list):
        if not valid_actions:
            return
        btn_width = 120
        btn_height = 36
        btn_spacing = 8
        total_width = len(valid_actions) * btn_width + (len(valid_actions) - 1) * btn_spacing
        start_x = SCREEN_WIDTH // 2 - total_width // 2
        start_y = SCREEN_HEIGHT - 50

        for i, action in enumerate(valid_actions):
            x = start_x + i * (btn_width + btn_spacing)
            y = start_y
            btn_rect = pygame.Rect(x, y, btn_width, btn_height)
            pygame.draw.rect(self.screen, (40, 80, 140), btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, TEXT_WHITE, btn_rect, 2, border_radius=6)
            label = ACTION_LABELS.get(action, action)
            label_surf = self.log_font.render(label, True, TEXT_WHITE)
            label_rect = label_surf.get_rect(center=btn_rect.center)
            self.screen.blit(label_surf, label_rect)

    def draw_status_bar(self, game_manager: GameManager):
        bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 36)
        pygame.draw.rect(self.screen, (20, 20, 20), bar_rect)
        state_label = STATE_LABELS.get(game_manager.state, game_manager.state.value)
        current_name = game_manager.current_player().name
        left_text = f"Round {game_manager.round_number}  |  {current_name}'s Turn  |  {state_label}"
        left_surf = self.log_font.render(left_text, True, TEXT_WHITE)
        self.screen.blit(left_surf, (10, 10))

    def get_player_positions(self, num_players: int) -> list:
        if num_players == 2:
            return [PLAYER_BOTTOM, PLAYER_TOP]
        elif num_players == 3:
            return [PLAYER_BOTTOM, (400, 100), (880, 100)]
        elif num_players == 4:
            return [PLAYER_BOTTOM, PLAYER_LEFT, PLAYER_TOP, PLAYER_RIGHT]
        return [PLAYER_BOTTOM]

    def _draw_rounded_rect(self, surface, color, rect, radius):
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def _render_card_text(self, card: Card) -> tuple:
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        suit_surf = self.card_font.render(card.suit_symbol, True, color)
        return (rank_surf, suit_surf)