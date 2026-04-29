import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BG_GREEN, CARD_WHITE, CARD_BACK_BLUE,
    BLACK, RED, GOLD, TEXT_WHITE, TEXT_BLACK, HIGHLIGHT, DIM,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD,
    DECK_POSITION, PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    HAND_SIZE,
)
from game.card import Deck
from game.player import HumanPlayer, AIPlayer
from game.game_manager import GameManager, GameState
from game.ai import AIDecider
from ui.screens import MenuScreen, SetupScreen, PeekScreen, GameOverScreen


class ActionButton:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=TEXT_WHITE, font_size=20):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.is_hovered = False
        self.visible = True
        self.enabled = True

    def draw(self, screen, font):
        if not self.visible:
            return
        color = self.hover_color if self.is_hovered and self.enabled else self.color
        if not self.enabled:
            color = DIM
        pygame.draw.rect(screen, color, self.rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(screen, BLACK, self.rect, width=2, border_radius=CORNER_RADIUS)
        text_surf = font.render(self.text, True, self.text_color if self.enabled else (150, 150, 150))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click) -> bool:
        if not self.visible or not self.enabled:
            return False
        return mouse_click and self.rect.collidepoint(mouse_pos)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.card_font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", 16)
        self.label_font = pygame.font.SysFont("segoeui", 22)
        self.log_font = pygame.font.SysFont("segoeui", 16)
        self.selected_slot = None
        self.target_player = None
        self.target_slot = None
        self.awaiting_target = None

    def draw(self, game_manager):
        gm = game_manager
        self._draw_deck(gm)
        positions = self._get_player_positions(gm)
        for i, player in enumerate(gm.players):
            self._draw_player_hand(gm, player, positions[i], i)
        self._draw_current_player_indicator(gm, positions)
        self._draw_drawn_card(gm)
        self._draw_game_log(gm)
        self._draw_action_buttons(gm)

    def _get_player_positions(self, game_manager):
        positions = [PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT]
        return positions[:len(game_manager.players)]

    def _draw_deck(self, game_manager):
        dx, dy = DECK_POSITION
        remaining = game_manager.deck.remaining if game_manager.deck else 0
        stack_count = min(remaining, 5)
        for i in range(stack_count):
            rect = pygame.Rect(dx - CARD_WIDTH // 2 - i, dy - CARD_HEIGHT // 2 - i, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(self.screen, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
            pygame.draw.rect(self.screen, (20, 40, 80), rect, width=2, border_radius=CORNER_RADIUS)
        if remaining == 0:
            rect = pygame.Rect(dx - CARD_WIDTH // 2, dy - CARD_HEIGHT // 2, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(self.screen, DIM, rect, border_radius=CORNER_RADIUS)
        deck_text = self.small_font.render(f"Deck: {remaining}", True, TEXT_WHITE)
        self.screen.blit(deck_text, deck_text.get_rect(center=(dx, dy + CARD_HEIGHT // 2 + 16)))

    def _draw_player_hand(self, game_manager, player, position, player_index):
        px, py = position
        is_current = player_index == game_manager.current_player_index
        is_human = player.is_human

        name_color = GOLD if is_current else TEXT_WHITE
        name_surf = self.label_font.render(player.name, True, name_color)
        name_rect = name_surf.get_rect(center=(px, py - CARD_HEIGHT // 2 - 30))
        self.screen.blit(name_surf, name_rect)

        score_text = f"Cards: {player.card_count}"
        score_surf = self.small_font.render(score_text, True, TEXT_WHITE)
        self.screen.blit(score_surf, score_surf.get_rect(center=(px, py - CARD_HEIGHT // 2 - 12)))

        start_x = px - (HAND_SIZE * (CARD_WIDTH + CARD_SPREAD)) // 2 + CARD_SPREAD
        for slot_idx in range(HAND_SIZE):
            card = player.hand[slot_idx]
            cx = start_x + slot_idx * (CARD_WIDTH + CARD_SPREAD)
            cy = py

            if card is None:
                empty_rect = pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, (30, 70, 35), empty_rect, border_radius=CORNER_RADIUS)
                pygame.draw.rect(self.screen, DIM, empty_rect, width=1, border_radius=CORNER_RADIUS)
                continue

            show_face = is_human and slot_idx in player.known_cards

            if self.selected_slot is not None and is_human and is_current and slot_idx == self.selected_slot:
                highlight_rect = pygame.Rect(cx - 3, cy - 3, CARD_WIDTH + 6, CARD_HEIGHT + 6)
                pygame.draw.rect(self.screen, HIGHLIGHT, highlight_rect, border_radius=CORNER_RADIUS + 2)

            if show_face:
                self._draw_card_face(cx, cy, card)
            else:
                self._draw_card_back(cx, cy)

    def _draw_card_face(self, x, y, card):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        self.screen.blit(rank_surf, (x + 6, y + 4))
        sym_surf = self.card_font.render(card.suit_symbol, True, color)
        self.screen.blit(sym_surf, (x + 6, y + 22))
        center_surf = self.card_font.render(card.display_name, True, color)
        center_rect = center_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2 + 10))
        self.screen.blit(center_surf, center_rect)

    def _draw_card_back(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (20, 40, 80), rect, width=2, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(x + 8, y + 8, CARD_WIDTH - 16, CARD_HEIGHT - 16)
        pygame.draw.rect(self.screen, (40, 80, 160), inner, border_radius=4)

    def _draw_current_player_indicator(self, game_manager, positions):
        idx = game_manager.current_player_index
        px, py = positions[idx]
        indicator_rect = pygame.Rect(px - 60, py - CARD_HEIGHT // 2 - 48, 120, 20)
        pygame.draw.rect(self.screen, GOLD, indicator_rect, border_radius=10)

    def _draw_drawn_card(self, game_manager):
        if game_manager.drawn_card is None:
            return
        card = game_manager.drawn_card
        dx, dy = DECK_POSITION
        cx = dx + CARD_WIDTH + 20
        cy = dy - CARD_HEIGHT // 2
        label = self.small_font.render("Drawn:", True, TEXT_WHITE)
        self.screen.blit(label, label.get_rect(center=(cx + CARD_WIDTH // 2, cy - 14)))
        self._draw_card_face(cx, cy, card)

    def _draw_game_log(self, game_manager):
        log = game_manager.game_log[-5:]
        y = SCREEN_HEIGHT - 10 - len(log) * 18
        for i, entry in enumerate(log):
            surf = self.log_font.render(entry, True, TEXT_WHITE)
            self.screen.blit(surf, (10, y + i * 18))

    def _draw_action_buttons(self, game_manager):
        pass

    def get_card_rect(self, player_index, slot_index, game_manager):
        positions = self._get_player_positions(game_manager)
        px, py = positions[player_index]
        start_x = px - (HAND_SIZE * (CARD_WIDTH + CARD_SPREAD)) // 2 + CARD_SPREAD
        cx = start_x + slot_index * (CARD_WIDTH + CARD_SPREAD)
        return pygame.Rect(cx, py, CARD_WIDTH, CARD_HEIGHT)

    def get_deck_rect(self):
        dx, dy = DECK_POSITION
        return pygame.Rect(dx - CARD_WIDTH // 2, dy - CARD_HEIGHT // 2, CARD_WIDTH, CARD_HEIGHT)

    def get_drawn_card_rect(self, game_manager):
        if game_manager.drawn_card is None:
            return None
        dx, dy = DECK_POSITION
        cx = dx + CARD_WIDTH + 20
        cy = dy - CARD_HEIGHT // 2
        return pygame.Rect(cx, cy, CARD_WIDTH, CARD_HEIGHT)


def _create_action_buttons(game_manager, renderer):
    from game.rules import get_valid_actions
    buttons = {}
    gm = game_manager
    cp = gm.current_player()

    valid = get_valid_actions(cp, gm.drawn_card, gm.has_drawn_this_turn)
    if not valid:
        return buttons

    base_y = SCREEN_HEIGHT - 50
    if gm.state == GameState.TURN_START:
        if 'declare' in valid:
            buttons['declare'] = ActionButton(SCREEN_WIDTH // 2 - 200, base_y, 160, 40, "Declare", (180, 160, 30), (220, 200, 50), TEXT_BLACK)
        if 'draw' in valid:
            buttons['draw'] = ActionButton(SCREEN_WIDTH // 2 - 20, base_y, 120, 40, "Draw", (40, 100, 50), (60, 140, 70))
    elif gm.state == GameState.DECIDE:
        if 'play_power' in valid:
            buttons['play_power'] = ActionButton(SCREEN_WIDTH // 2 - 350, base_y, 140, 40, "Use Power", (120, 60, 160), (160, 90, 200))
        if 'swap' in valid:
            buttons['swap'] = ActionButton(SCREEN_WIDTH // 2 - 190, base_y, 120, 40, "Swap", (40, 100, 50), (60, 140, 70))
        if 'discard' in valid:
            buttons['discard'] = ActionButton(SCREEN_WIDTH // 2 - 50, base_y, 120, 40, "Discard", (140, 40, 40), (180, 60, 60))
        if 'pair_own' in valid:
            buttons['pair_own'] = ActionButton(SCREEN_WIDTH // 2 + 90, base_y, 150, 40, "Pair Own", (40, 100, 160), (60, 130, 200))
        if 'pair_opponent' in valid:
            buttons['pair_opponent'] = ActionButton(SCREEN_WIDTH // 2 + 270, base_y, 170, 40, "Pair Opponent", (160, 100, 40), (200, 140, 60))

    elif gm.state in (GameState.PAIR_CHECK, GameState.POWER_RESOLVE):
        buttons['end_turn'] = ActionButton(SCREEN_WIDTH // 2, base_y, 160, 40, "End Turn", (100, 100, 100), (140, 140, 140))

    return buttons


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Declare")
    clock = pygame.time.Clock()
    renderer = Renderer(screen)

    game_manager = None
    current_screen = "menu"
    menu_screen = MenuScreen(screen)
    setup_screen = SetupScreen(screen)
    peek_screen = PeekScreen(screen)
    game_over_screen = GameOverScreen(screen)

    selected_slot = None
    target_player = None
    target_slot = None
    awaiting_action = None
    awaiting_power_target = False
    awaiting_swap_slot = False
    awaiting_pair_own_slot = False
    awaiting_pair_opponent_target = False
    pair_opponent_give_slot = None
    ai_action_delay = 0.0
    AI_DELAY = 1.0
    action_buttons = {}
    status_message = ""
    status_timer = 0.0

    game_over_result = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        if status_timer > 0:
            status_timer -= dt
            if status_timer <= 0:
                status_message = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_screen == "menu":
                action = menu_screen.handle_event(event)
                if action == "new_game":
                    current_screen = "setup"
                    setup_screen = SetupScreen(screen)
                elif action == "quit":
                    running = False

            elif current_screen == "setup":
                action = setup_screen.handle_event(event)
                if action == "start_game":
                    game_over_result = None
                    configs = setup_screen.players_config[:setup_screen.num_players]
                    game_manager = GameManager(configs)
                    game_manager.setup_game()
                    peek_screen = PeekScreen(screen)
                    current_screen = "peek"
                elif action == "back":
                    current_screen = "menu"

            elif current_screen == "peek":
                action = peek_screen.handle_event(event)
                if action == "peek_done":
                    game_manager.start_peek_phase()
                    current_screen = "game"

            elif current_screen == "game":
                if game_manager is None:
                    current_screen = "menu"
                    continue

                if game_manager.state == GameState.GAME_OVER:
                    current_screen = "game_over"
                    continue

                cp = game_manager.current_player()

                if event.type == pygame.MOUSEMOTION:
                    for btn in action_buttons.values():
                        btn.update_hover(event.pos)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cp.is_human:
                    mouse_pos = event.pos
                    clicked_button = None
                    for name, btn in action_buttons.items():
                        if btn.is_clicked(mouse_pos, True):
                            clicked_button = name
                            break

                    if clicked_button:
                        if clicked_button == 'draw' and game_manager.state == GameState.TURN_START:
                            drawn = game_manager.draw_card()
                            status_message = f"Drew: {drawn.display_name}" if drawn else "Drew a card"
                            status_timer = 2.0
                            selected_slot = None

                        elif clicked_button == 'declare' and game_manager.state == GameState.TURN_START:
                            result = game_manager.execute_player_action("declare", {})
                            if result.get("success", True):
                                game_manager.resolve_declaration()
                                current_screen = "game_over"

                        elif clicked_button == 'swap' and game_manager.state == GameState.DECIDE:
                            awaiting_swap_slot = True
                            status_message = "Click one of your cards to swap"
                            status_timer = 5.0

                        elif clicked_button == 'discard' and game_manager.state == GameState.DECIDE:
                            result = game_manager.execute_player_action("discard", {"drawn_card": game_manager.drawn_card})
                            game_manager.end_turn()

                        elif clicked_button == 'play_power' and game_manager.state == GameState.DECIDE:
                            card = game_manager.drawn_card
                            if card and card.power:
                                if card.power in ('peek_self',):
                                    awaiting_power_target = True
                                    awaiting_action = 'peek_self'
                                    status_message = "Click one of your unknown cards to peek"
                                    status_timer = 5.0
                                elif card.power in ('peek_opponent',):
                                    awaiting_power_target = True
                                    awaiting_action = 'peek_opponent'
                                    status_message = "Click an opponent's card to peek"
                                    status_timer = 5.0
                                elif card.power in ('unseen_swap', 'seen_swap'):
                                    awaiting_power_target = True
                                    awaiting_action = card.power
                                    status_message = "Click one of your cards, then an opponent's card to swap"
                                    status_timer = 5.0
                                elif card.power == 'skip':
                                    target_info = {}
                                    game_manager.execute_player_action("play_power", {
                                        "card": card,
                                        "target_info": target_info,
                                    })
                                    game_manager.skip_next = True
                                    game_manager.end_turn()

                        elif clicked_button == 'pair_own' and game_manager.state == GameState.DECIDE:
                            awaiting_pair_own_slot = True
                            status_message = "Click your matching card to pair"
                            status_timer = 5.0

                        elif clicked_button == 'pair_opponent' and game_manager.state == GameState.DECIDE:
                            awaiting_pair_opponent_target = True
                            status_message = "Click opponent's matching card, then yours to give"
                            status_timer = 5.0

                        elif clicked_button == 'end_turn':
                            game_manager.end_turn()

                    else:
                        if awaiting_swap_slot and game_manager.state == GameState.DECIDE:
                            human_idx = None
                            for i, p in enumerate(game_manager.players):
                                if p.is_human:
                                    human_idx = i
                                    break
                            if human_idx is not None:
                                for slot_idx in range(HAND_SIZE):
                                    rect = renderer.get_card_rect(human_idx, slot_idx, game_manager)
                                    if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                        result = game_manager.execute_player_action("swap", {
                                            "my_slot": slot_idx,
                                            "drawn_card": game_manager.drawn_card,
                                        })
                                        awaiting_swap_slot = False
                                        game_manager.end_turn()
                                        break

                        elif awaiting_power_target:
                            human_idx = None
                            for i, p in enumerate(game_manager.players):
                                if p.is_human:
                                    human_idx = i
                                    break

                            if awaiting_action == 'peek_self' and human_idx is not None:
                                for slot_idx in range(HAND_SIZE):
                                    rect = renderer.get_card_rect(human_idx, slot_idx, game_manager)
                                    if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                        card = game_manager.drawn_card
                                        game_manager.execute_player_action("play_power", {
                                            "card": card,
                                            "target_info": {"slot": slot_idx},
                                        })
                                        game_manager.players[human_idx].known_cards[slot_idx] = game_manager.players[human_idx].hand[slot_idx]
                                        status_message = f"Peeked: {game_manager.players[human_idx].hand[slot_idx].display_name}"
                                        status_timer = 2.0
                                        awaiting_power_target = False
                                        awaiting_action = None
                                        game_manager.end_turn()
                                        break

                            elif awaiting_action == 'peek_opponent':
                                for p_idx, player in enumerate(game_manager.players):
                                    if player.is_human:
                                        continue
                                    for slot_idx in range(HAND_SIZE):
                                        rect = renderer.get_card_rect(p_idx, slot_idx, game_manager)
                                        if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                            card = game_manager.drawn_card
                                            human = game_manager.players[human_idx]
                                            game_manager.execute_player_action("play_power", {
                                                "card": card,
                                                "target_info": {"player_index": player.seat_index, "slot": slot_idx},
                                            })
                                            human.known_opponent_cards[(player.seat_index, slot_idx)] = player.hand[slot_idx]
                                            status_message = f"Peeked opponent card!"
                                            status_timer = 2.0
                                            awaiting_power_target = False
                                            awaiting_action = None
                                            game_manager.end_turn()
                                            break
                                    else:
                                        continue
                                    break

                            elif awaiting_action in ('unseen_swap', 'seen_swap'):
                                if selected_slot is None:
                                    if human_idx is not None:
                                        for slot_idx in range(HAND_SIZE):
                                            rect = renderer.get_card_rect(human_idx, slot_idx, game_manager)
                                            if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                                selected_slot = slot_idx
                                                status_message = f"Selected slot {slot_idx + 1}. Now click opponent's card."
                                                status_timer = 5.0
                                                break
                                else:
                                    for p_idx, player in enumerate(game_manager.players):
                                        if player.is_human:
                                            continue
                                        for slot_idx in range(HAND_SIZE):
                                            rect = renderer.get_card_rect(p_idx, slot_idx, game_manager)
                                            if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                                card = game_manager.drawn_card
                                                game_manager.execute_player_action("play_power", {
                                                    "card": card,
                                                    "target_info": {
                                                        "my_slot": selected_slot,
                                                        "target_player": player.seat_index,
                                                        "their_slot": slot_idx,
                                                    },
                                                })
                                                awaiting_power_target = False
                                                awaiting_action = None
                                                selected_slot = None
                                                game_manager.end_turn()
                                                break
                                        else:
                                            continue
                                        break

                        elif awaiting_pair_own_slot and game_manager.state == GameState.DECIDE:
                            human_idx = None
                            for i, p in enumerate(game_manager.players):
                                if p.is_human:
                                    human_idx = i
                                    break
                            if human_idx is not None:
                                for slot_idx in range(HAND_SIZE):
                                    rect = renderer.get_card_rect(human_idx, slot_idx, game_manager)
                                    if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                        drawn = game_manager.drawn_card
                                        matching = game_manager.players[human_idx].known_cards.get(slot_idx)
                                        if matching and matching.rank == drawn.rank:
                                            game_manager.execute_player_action("pair_own", {
                                                "player_slot": slot_idx,
                                                "drawn_card": drawn,
                                            })
                                            awaiting_pair_own_slot = False
                                            game_manager.end_turn()
                                            break

                        elif awaiting_pair_opponent_target and game_manager.state == GameState.DECIDE:
                            if pair_opponent_give_slot is None:
                                human_idx = None
                                for i, p in enumerate(game_manager.players):
                                    if p.is_human:
                                        human_idx = i
                                        break
                                if human_idx is not None:
                                    for slot_idx in range(HAND_SIZE):
                                        rect = renderer.get_card_rect(human_idx, slot_idx, game_manager)
                                        if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                            pair_opponent_give_slot = slot_idx
                                            status_message = "Now click opponent's matching card"
                                            status_timer = 5.0
                                            break
                            else:
                                for p_idx, player in enumerate(game_manager.players):
                                    if player.is_human:
                                        continue
                                    for slot_idx in range(HAND_SIZE):
                                        rect = renderer.get_card_rect(p_idx, slot_idx, game_manager)
                                        if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                            drawn = game_manager.drawn_card
                                            game_manager.execute_player_action("pair_opponent", {
                                                "opponent_index": player.seat_index,
                                                "opponent_slot": slot_idx,
                                                "drawn_card": drawn,
                                                "give_slot": pair_opponent_give_slot,
                                            })
                                            awaiting_pair_opponent_target = False
                                            pair_opponent_give_slot = None
                                            game_manager.end_turn()
                                            break
                                    else:
                                        continue
                                    break

                    if game_manager.state == GameState.TURN_START:
                        deck_rect = renderer.get_deck_rect()
                        if deck_rect.collidepoint(mouse_pos):
                            drawn = game_manager.draw_card()
                            status_message = f"Drew: {drawn.display_name}" if drawn else "Drew a card"
                            status_timer = 2.0
                            selected_slot = None

                if event.type == pygame.KEYDOWN and cp.is_human:
                    if event.key == pygame.K_d:
                        if game_manager.state == GameState.TURN_START and not game_manager.has_drawn_this_turn:
                            result = game_manager.execute_player_action("declare", {})
                            if result.get("success", True):
                                game_manager.resolve_declaration()
                                current_screen = "game_over"

            elif current_screen == "game_over":
                action = game_over_screen.handle_event(event)
                if action == "play_again":
                    game_over_result = None
                    current_screen = "setup"
                    setup_screen = SetupScreen(screen)
                elif action == "menu":
                    game_over_result = None
                    current_screen = "menu"

        if current_screen == "game" and game_manager and not game_manager.current_player().is_human:
            ai_action_delay += dt
            if ai_action_delay >= AI_DELAY:
                _handle_ai_turn(game_manager)
                ai_action_delay = 0.0
                if game_manager.state == GameState.GAME_OVER:
                    current_screen = "game_over"
                else:
                    game_manager.check_game_over()
                    if game_manager.state == GameState.GAME_OVER:
                        current_screen = "game_over"

        screen.fill(BG_GREEN)

        if current_screen == "menu":
            menu_screen.draw()
        elif current_screen == "setup":
            setup_screen.draw()
        elif current_screen == "peek":
            peek_screen.draw(game_manager)
            result = peek_screen.update(dt)
            if result == "peek_done":
                game_manager.start_peek_phase()
                current_screen = "game"
        elif current_screen == "game":
            action_buttons = _create_action_buttons(game_manager, renderer)
            renderer.draw(game_manager)
            for btn in action_buttons.values():
                btn.draw(screen, pygame.font.SysFont("segoeui", 20))
            if status_message:
                status_font = pygame.font.SysFont("segoeui", 22)
                status_surf = status_font.render(status_message, True, GOLD)
                status_rect = status_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 90))
                bg_rect = status_rect.inflate(20, 10)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 180))
                screen.blit(bg_surface, bg_rect.topleft)
                screen.blit(status_surf, status_rect)

            state_text = game_manager.state.value.replace("_", " ").title()
            state_font = pygame.font.SysFont("segoeui", 18)
            state_surf = state_font.render(state_text, True, TEXT_WHITE)
            screen.blit(state_surf, (10, 10))

        elif current_screen == "game_over":
            if game_over_result is None:
                if game_manager:
                    if game_manager.winner:
                        game_over_result = game_manager.resolve_declaration()
                    else:
                        for p in game_manager.players:
                            if hasattr(p, 'has_zero_cards') and p.has_zero_cards:
                                game_over_result = {'winner': p, 'scores': {pl.seat_index: pl.score for pl in game_manager.players}, 'declarer_won': True, 'auto_win': True}
                                break
                        if game_over_result is None:
                            game_over_result = {'winner': None, 'scores': {pl.seat_index: pl.score for pl in game_manager.players}, 'declarer_won': False, 'auto_win': False}
            game_over_screen.draw(game_manager, game_over_result or {})

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def _handle_ai_turn(game_manager: GameManager):
    cp = game_manager.current_player()
    players = game_manager.players

    if game_manager.state == GameState.TURN_START:
        ai = AIDecider(cp, {'players': players})
        if ai.should_declare():
            game_manager.execute_player_action("declare", {})
            game_manager.resolve_declaration()
            return
        game_manager.draw_card()

    if game_manager.state == GameState.DECIDE:
        ai = AIDecider(cp, {'players': players})
        drawn = game_manager.drawn_card
        if drawn:
            decision = ai.choose_action(drawn)
            action = decision['action']

            if action == 'play_power':
                target_info = _ai_power_target(ai, cp, players, drawn)
                game_manager.execute_player_action('play_power', {
                    'card': drawn,
                    'target_info': target_info,
                })
                if drawn.power == 'peek_self' and target_info:
                    slot = target_info.get('slot', 0)
                    if cp.hand[slot] is not None:
                        cp.known_cards[slot] = cp.hand[slot]
                elif drawn.power == 'peek_opponent' and target_info:
                    p_idx = target_info.get('player_index', 0)
                    s_idx = target_info.get('slot', 0)
                    target_p = next((p for p in players if p.seat_index == p_idx), None)
                    if target_p and target_p.hand[s_idx] is not None:
                        cp.known_opponent_cards[(p_idx, s_idx)] = target_p.hand[s_idx]
                elif drawn.power == 'skip':
                    game_manager.skip_next = True

            elif action == 'swap':
                game_manager.execute_player_action('swap', {
                    'my_slot': decision.get('target_slot', ai.estimate_worst_slot()),
                    'drawn_card': drawn,
                })

            elif action == 'discard':
                game_manager.execute_player_action('discard', {'drawn_card': drawn})

            elif action == 'pair_own':
                game_manager.execute_player_action('pair_own', {
                    'player_slot': decision['target_slot'],
                    'drawn_card': drawn,
                })

            elif action == 'pair_opponent':
                give_slot = ai.choose_card_to_give()
                game_manager.execute_player_action('pair_opponent', {
                    'opponent_index': decision['target_player'],
                    'opponent_slot': _find_opponent_slot(cp, players, decision['target_player'], drawn.rank),
                    'drawn_card': drawn,
                    'give_slot': give_slot,
                })

    if game_manager.state in (GameState.PAIR_CHECK, GameState.POWER_RESOLVE, GameState.DECIDE):
        game_manager.end_turn()

    game_manager.check_game_over()


def _ai_power_target(ai, player, players, card):
    power = card.power
    if power == 'peek_self':
        return {'slot': ai.peek_target_own(player.hand)}
    elif power == 'peek_opponent':
        p_idx, s_idx = ai.peek_target_opponent(players)
        return {'player_index': p_idx, 'slot': s_idx}
    elif power == 'seen_swap':
        return {
            'my_slot': ai.estimate_worst_slot() or 0,
            'target_player': ai._pick_opponent_with_most_unknown() or 0,
            'their_slot': 0,
        }
    elif power == 'unseen_swap':
        return {
            'my_slot': ai.estimate_worst_slot() or 0,
            'target_player': ai._pick_opponent_with_most_unknown() or 0,
            'their_slot': 0,
        }
    elif power == 'skip':
        return {}
    return None


def _find_opponent_slot(player, players, opponent_index, rank):
    for (p_idx, s_idx), card in player.known_opponent_cards.items():
        if p_idx == opponent_index and card.rank == rank:
            return s_idx
    return 0


if __name__ == "__main__":
    main()