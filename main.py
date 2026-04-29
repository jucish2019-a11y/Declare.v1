import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BG_GREEN, BG_DARK, CARD_WHITE, BLACK, RED, GOLD, TEXT_WHITE, TEXT_BLACK,
    TEXT_DIM, HIGHLIGHT, DIM, PANEL_BG, CARD_BACK_BLUE,
    DECLARE_RED, DECLARE_RED_HOVER, CANCEL_GRAY, CANCEL_GRAY_HOVER,
    PEEK_BLUE, PEEK_BLUE_HOVER, SWAP_GREEN, SWAP_GREEN_HOVER,
    DISCARD_ORANGE, DISCARD_ORANGE_HOVER, PAIR_TEAL, PAIR_TEAL_HOVER,
    STATUS_BAR_H, ACTION_BAR_Y, ACTION_BAR_H,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD, HAND_SIZE,
    DECK_CENTER, DRAWN_CARD_POS, DISCARD_POS,
    PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    LOG_PANEL_X, LOG_PANEL_Y, LOG_PANEL_W, LOG_PANEL_H,
    UI_FONT_SIZE, SMALL_FONT_SIZE, POWER_LABELS,
    ANIM_DRAW_DURATION, ANIM_SWAP_DURATION, ANIM_UNSEEN_SWAP_DURATION,
    ANIM_SEEN_SWAP_DURATION, ANIM_DISCARD_DURATION, ANIM_PAIR_FLY_DURATION,
    ANIM_NOTIFICATION_DURATION, CARD_GRID_SPACING_X, CARD_GRID_SPACING_Y,
)
from game.game_manager import GameManager, GameState
from game.player import HumanPlayer
from game.ai import AIDecider
from game.rules import get_valid_actions
from game.settings import GameSettings
from ui.renderer import Renderer, _get_seat_position, _player_area_bounds
from ui.screens import MenuScreen, SetupScreen, PeekScreen, GameOverScreen
from ui.settings import SettingsMenu


def _build_action_buttons(gm, ui_font):
    buttons = {}
    cp = gm.current_player()
    valid = get_valid_actions(cp, gm.drawn_card, gm.has_drawn_this_turn)
    if not valid:
        return buttons
    btn_y = ACTION_BAR_Y + ACTION_BAR_H // 2
    btn_h = 44
    if gm.state == GameState.TURN_START:
        x = SCREEN_WIDTH // 2 - 120
        if 'declare' in valid:
            w = 160
            rect = pygame.Rect(x - w // 2, btn_y - btn_h // 2, w, btn_h)
            buttons['declare'] = {'rect': rect, 'text': 'Declare', 'color': DECLARE_RED, 'hover_color': DECLARE_RED_HOVER, 'font': ui_font}
            x += 180
        if 'draw' in valid:
            w = 140
            rect = pygame.Rect(x - w // 2, btn_y - btn_h // 2, w, btn_h)
            buttons['draw'] = {'rect': rect, 'text': 'Draw', 'color': SWAP_GREEN, 'hover_color': SWAP_GREEN_HOVER, 'font': ui_font}
    elif gm.state == GameState.DECIDE:
        x = SCREEN_WIDTH // 2 - 360
        spacing = 10
        if 'play_power' in valid and gm.drawn_card and gm.drawn_card.power:
            power = gm.drawn_card.power
            label = POWER_LABELS.get(power, 'Power')
            w = 150
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['play_power'] = {'rect': rect, 'text': label, 'color': PEEK_BLUE, 'hover_color': PEEK_BLUE_HOVER, 'font': ui_font}
            x += w + spacing
        if 'swap' in valid:
            w = 110
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['swap'] = {'rect': rect, 'text': 'Swap', 'color': SWAP_GREEN, 'hover_color': SWAP_GREEN_HOVER, 'font': ui_font}
            x += w + spacing
        if 'discard' in valid:
            w = 120
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['discard'] = {'rect': rect, 'text': 'Discard', 'color': DISCARD_ORANGE, 'hover_color': DISCARD_ORANGE_HOVER, 'font': ui_font}
            x += w + spacing
        if 'pair_own' in valid:
            w = 130
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['pair_own'] = {'rect': rect, 'text': 'Pair Own', 'color': PAIR_TEAL, 'hover_color': PAIR_TEAL_HOVER, 'font': ui_font}
            x += w + spacing
        if 'pair_opponent' in valid:
            w = 160
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['pair_opponent'] = {'rect': rect, 'text': 'Pair Opponent', 'color': PAIR_TEAL, 'hover_color': PAIR_TEAL_HOVER, 'font': ui_font}
            x += w + spacing
        if 'declare' in valid:
            w = 130
            rect = pygame.Rect(x, btn_y - btn_h // 2, w, btn_h)
            buttons['declare'] = {'rect': rect, 'text': 'Declare', 'color': DECLARE_RED, 'hover_color': DECLARE_RED_HOVER, 'font': ui_font}
    return buttons


def _build_cancel_button(text, ui_font):
    w = 140
    h = 40
    rect = pygame.Rect(SCREEN_WIDTH // 2 - w // 2, ACTION_BAR_Y + ACTION_BAR_H + 2, w, h)
    return {'rect': rect, 'text': text, 'font': ui_font}


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
    return {}


def _find_opponent_slot(player, players, opponent_index, rank):
    for (p_idx, s_idx), card in player.known_opponent_cards.items():
        if p_idx == opponent_index and card.rank == rank:
            return s_idx
    return 0


def _get_human_index(game_manager):
    for i, p in enumerate(game_manager.players):
        if p.is_human:
            return i
    return None


def _clamp_to_bounds(cx, cy, bounds):
    x_min, y_min, x_max, y_max = bounds
    cx = max(x_min + CARD_WIDTH // 2, min(x_max - CARD_WIDTH // 2, cx))
    cy = max(y_min + CARD_HEIGHT // 2, min(y_max - CARD_HEIGHT // 2, cy))
    return (cx, cy)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Declare")
    clock = pygame.time.Clock()

    ui_font = pygame.font.SysFont("arial", UI_FONT_SIZE)
    small_font = pygame.font.SysFont("arial", SMALL_FONT_SIZE)

    game_manager = None
    current_screen = "menu"
    game_over_result = None
    settings_open = False
    game_settings = GameSettings()

    renderer = Renderer(screen)
    menu_screen = MenuScreen(screen)
    setup_screen = SetupScreen(screen)
    peek_screen = PeekScreen(screen, game_settings.peek_phase_seconds)
    game_over_screen = GameOverScreen(screen)
    settings_menu = SettingsMenu(screen)

    awaiting = None
    selected_slot = None
    swap_second_click = False
    pair_opponent_give_slot = None
    status_message = ""
    turn_end_timer = 0.0

    ai_phase = 'idle'
    ai_timer = 0.0

    dragging_slot = None
    drag_offset = (0, 0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        if game_manager:
            game_manager.update(dt)
        renderer.update(dt)

        if turn_end_timer > 0:
            turn_end_timer -= dt
            if turn_end_timer <= 0:
                turn_end_timer = 0
                game_manager.end_turn()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if awaiting is not None:
                    awaiting = None
                    selected_slot = None
                    swap_second_click = False
                    pair_opponent_give_slot = None
                    status_message = ""
                    game_manager.cancel_targeting()
                    continue

                if settings_open and current_screen == "game":
                    settings_open = False
                    continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                if current_screen == "game" and game_manager is not None:
                    settings_open = not settings_open
                    awaiting = None
                    selected_slot = None
                    swap_second_click = False
                    pair_opponent_give_slot = None
                    status_message = ""
                    game_manager.cancel_targeting()
                    continue

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
                    peek_screen = PeekScreen(screen, game_settings.peek_phase_seconds)
                    current_screen = "peek"
                elif action == "back":
                    current_screen = "menu"

            elif current_screen == "peek":
                action = peek_screen.handle_event(event)
                if action == "peek_done":
                    game_manager.start_peek_phase()
                    awaiting = None
                    selected_slot = None
                    turn_end_timer = 0
                    ai_phase = 'idle'
                    ai_timer = 0
                    current_screen = "game"

            elif current_screen == "game":
                if settings_open:
                    result = settings_menu.handle_event(event, game_settings, game_manager)
                    if result == 'close':
                        settings_open = False
                    elif result == 'updated':
                        pass
                    continue

                if game_manager is None:
                    current_screen = "menu"
                    continue

                if game_manager.state == GameState.GAME_OVER:
                    if game_over_result is None:
                        game_over_result = game_manager.declaration_result or {
                            'winner': game_manager.winner,
                            'scores': {p.seat_index: p.score for p in game_manager.players},
                            'declarer_won': False,
                            'auto_win': False,
                        }
                    current_screen = "game_over"
                    continue

                cp = game_manager.current_player()
                if not cp.is_human:
                    continue

                if turn_end_timer > 0:
                    continue

                if renderer.is_animating():
                    continue

                human_idx = _get_human_index(game_manager)
                action_buttons = _build_action_buttons(game_manager, ui_font)
                cancel_button = None
                if awaiting is not None:
                    cancel_button = _build_cancel_button("Cancel", ui_font)
                    if awaiting == 'swap':
                        status_message = "Click one of your cards to swap with the drawn card"
                    elif awaiting == 'peek_self':
                        status_message = "Click one of your unknown cards to peek"
                    elif awaiting == 'peek_opponent':
                        status_message = "Click an opponent's card to peek"
                    elif awaiting in ('unseen_swap', 'seen_swap'):
                        if selected_slot is None:
                            status_message = "Click one of YOUR cards first"
                        else:
                            status_message = "Now click an OPPONENT's card to swap"
                    elif awaiting == 'pair_own':
                        status_message = "Click your matching card to pair"
                    elif awaiting == 'pair_opponent':
                        if pair_opponent_give_slot is None:
                            status_message = "Click YOUR card to give away"
                        else:
                            status_message = "Click OPPONENT's matching card"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_btn = None
                    for name, btn in action_buttons.items():
                        if btn['rect'].collidepoint(mouse_pos):
                            clicked_btn = name
                            break

                    if cancel_button and cancel_button['rect'].collidepoint(mouse_pos):
                        awaiting = None
                        selected_slot = None
                        swap_second_click = False
                        pair_opponent_give_slot = None
                        status_message = ""
                        game_manager.cancel_targeting()
                        continue

                    gear_rect = renderer.get_gear_rect()
                    if gear_rect.collidepoint(mouse_pos):
                        settings_open = not settings_open
                        awaiting = None
                        selected_slot = None
                        swap_second_click = False
                        pair_opponent_give_slot = None
                        status_message = ""
                        game_manager.cancel_targeting()
                        continue

                    if clicked_btn:
                        if clicked_btn == 'draw' and game_manager.state == GameState.TURN_START:
                            game_manager.draw_card()
                            renderer.push_draw_animation(game_manager)
                            status_message = ""
                            awaiting = None

                        elif clicked_btn == 'declare':
                            if game_settings.confirm_declare:
                                awaiting = 'confirm_declare'
                                selected_slot = None
                                swap_second_click = False
                                pair_opponent_give_slot = None
                                status_message = "Are you sure? Click again to Declare."
                            else:
                                game_manager.execute_player_action("declare", {})
                                game_manager.resolve_declaration()
                                game_over_result = game_manager.declaration_result
                                current_screen = "game_over"

                        elif clicked_btn == 'swap' and game_manager.state == GameState.DECIDE:
                            awaiting = 'swap'
                            selected_slot = None
                            status_message = "Click one of your cards to swap with the drawn card"

                        elif clicked_btn == 'discard' and game_manager.state == GameState.DECIDE:
                            renderer.push_discard_animation(game_manager)
                            game_manager.execute_player_action("discard", {"drawn_card": game_manager.drawn_card})
                            turn_end_timer = ANIM_DISCARD_DURATION + 0.1
                            status_message = ""

                        elif clicked_btn == 'play_power' and game_manager.state == GameState.DECIDE:
                            card = game_manager.drawn_card
                            if card and card.power:
                                if card.power == 'peek_self':
                                    awaiting = 'peek_self'
                                    selected_slot = None
                                    status_message = "Click one of your unknown cards to peek"
                                elif card.power == 'peek_opponent':
                                    awaiting = 'peek_opponent'
                                    selected_slot = None
                                    status_message = "Click an opponent's card to peek"
                                elif card.power in ('unseen_swap', 'seen_swap'):
                                    awaiting = card.power
                                    selected_slot = None
                                    swap_second_click = False
                                    status_message = "Click one of YOUR cards first"
                                elif card.power == 'skip':
                                    game_manager.execute_player_action("play_power", {
                                        "card": card,
                                        "target_info": {},
                                    })
                                    game_manager.skip_next = True
                                    turn_end_timer = 0.5

                        elif clicked_btn == 'pair_own' and game_manager.state == GameState.DECIDE:
                            awaiting = 'pair_own'
                            selected_slot = None
                            status_message = "Click your matching card to pair"

                        elif clicked_btn == 'pair_opponent' and game_manager.state == GameState.DECIDE:
                            awaiting = 'pair_opponent'
                            pair_opponent_give_slot = None
                            selected_slot = None
                            status_message = "Click YOUR card to give away"

                    else:
                        if awaiting is not None:
                            if awaiting == 'swap':
                                if human_idx is not None:
                                    rects = renderer.get_card_rects(human_idx, game_manager)
                                    for slot_idx, rect in enumerate(rects):
                                        if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                            swapped_card = game_manager.players[human_idx].hand[slot_idx]
                                            renderer.push_swap_animation(game_manager, slot_idx, swapped_card)
                                            game_manager.execute_player_action("swap", {
                                                "my_slot": slot_idx,
                                                "drawn_card": game_manager.drawn_card,
                                            })
                                            awaiting = None
                                            status_message = ""
                                            turn_end_timer = ANIM_SWAP_DURATION + 0.1
                                            break

                            elif awaiting == 'peek_self':
                                if human_idx is not None:
                                    rects = renderer.get_card_rects(human_idx, game_manager)
                                    for slot_idx, rect in enumerate(rects):
                                        if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                            center = renderer.get_card_center(human_idx, slot_idx, game_manager)
                                            renderer.push_peek_lift_animation(game_manager, center)
                                            result = game_manager.execute_player_action("play_power", {
                                                "card": game_manager.drawn_card,
                                                "target_info": {"slot": slot_idx},
                                            })
                                            peeked_card = game_manager.players[human_idx].hand[slot_idx]
                                            card_rects = renderer.get_card_rects(human_idx, game_manager)
                                            if slot_idx < len(card_rects):
                                                r = card_rects[slot_idx]
                                                renderer.set_peek_reveal(peeked_card, r.x, r.y, game_settings.peek_reveal_time)
                                            awaiting = None
                                            status_message = ""
                                            turn_end_timer = 0.5
                                            break

                            elif awaiting == 'peek_opponent':
                                for player in game_manager.players:
                                    if player.is_human:
                                        continue
                                    rects = renderer.get_card_rects(player.seat_index, game_manager)
                                    for slot_idx, rect in enumerate(rects):
                                        if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                            center = renderer.get_card_center(player.seat_index, slot_idx, game_manager)
                                            renderer.push_peek_lift_animation(game_manager, center)
                                            result = game_manager.execute_player_action("play_power", {
                                                "card": game_manager.drawn_card,
                                                "target_info": {"player_index": player.seat_index, "slot": slot_idx},
                                            })
                                            peeked_card = player.hand[slot_idx]
                                            card_rects = renderer.get_card_rects(player.seat_index, game_manager)
                                            if slot_idx < len(card_rects):
                                                r = card_rects[slot_idx]
                                                renderer.set_peek_reveal(peeked_card, r.x, r.y, game_settings.peek_reveal_time)
                                            awaiting = None
                                            status_message = ""
                                            turn_end_timer = 0.5
                                            break
                                    else:
                                        continue
                                    break

                            elif awaiting in ('unseen_swap', 'seen_swap'):
                                if selected_slot is None:
                                    if human_idx is not None:
                                        rects = renderer.get_card_rects(human_idx, game_manager)
                                        for slot_idx, rect in enumerate(rects):
                                            if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                                selected_slot = slot_idx
                                                status_message = "Now click an OPPONENT's card to swap"
                                                break
                                else:
                                    for player in game_manager.players:
                                        if player.is_human:
                                            continue
                                        rects = renderer.get_card_rects(player.seat_index, game_manager)
                                        for slot_idx, rect in enumerate(rects):
                                            if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                                if awaiting == 'seen_swap':
                                                    their_card_before = player.hand[slot_idx]
                                                    renderer.push_seen_swap_animation(
                                                        game_manager, selected_slot,
                                                        player.seat_index, slot_idx,
                                                        their_card_before,
                                                    )
                                                else:
                                                    renderer.push_unseen_swap_animation(
                                                        game_manager, selected_slot,
                                                        player.seat_index, slot_idx,
                                                    )
                                                game_manager.execute_player_action("play_power", {
                                                    "card": game_manager.drawn_card,
                                                    "target_info": {
                                                        "my_slot": selected_slot,
                                                        "target_player": player.seat_index,
                                                        "their_slot": slot_idx,
                                                    },
                                                })
                                                awaiting = None
                                                selected_slot = None
                                                status_message = ""
                                                turn_end_timer = 0.7
                                                break
                                        else:
                                            continue
                                        break

                            elif awaiting == 'pair_own':
                                if human_idx is not None:
                                    rects = renderer.get_card_rects(human_idx, game_manager)
                                    for slot_idx, rect in enumerate(rects):
                                        if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                            drawn = game_manager.drawn_card
                                            matching = game_manager.players[human_idx].known_cards.get(slot_idx)
                                            if matching and matching.rank == drawn.rank:
                                                pair_card = game_manager.players[human_idx].hand[slot_idx]
                                                pos = renderer.get_card_center(human_idx, slot_idx, game_manager)
                                                drawn_pos = DRAWN_CARD_POS
                                                renderer.push_pair_fly_animation(game_manager, pos, pair_card, drawn_pos, drawn)
                                                game_manager.execute_player_action("pair_own", {
                                                    "player_slot": slot_idx,
                                                    "drawn_card": drawn,
                                                })
                                                awaiting = None
                                                status_message = ""
                                                turn_end_timer = ANIM_PAIR_FLY_DURATION + 0.1
                                            break

                            elif awaiting == 'pair_opponent':
                                if pair_opponent_give_slot is None:
                                    if human_idx is not None:
                                        rects = renderer.get_card_rects(human_idx, game_manager)
                                        for slot_idx, rect in enumerate(rects):
                                            if rect.collidepoint(mouse_pos) and game_manager.players[human_idx].hand[slot_idx] is not None:
                                                pair_opponent_give_slot = slot_idx
                                                status_message = "Click OPPONENT's matching card"
                                                break
                                else:
                                    for player in game_manager.players:
                                        if player.is_human:
                                            continue
                                        rects = renderer.get_card_rects(player.seat_index, game_manager)
                                        for slot_idx, rect in enumerate(rects):
                                            if rect.collidepoint(mouse_pos) and player.hand[slot_idx] is not None:
                                                opp_pos = renderer.get_card_center(player.seat_index, slot_idx, game_manager)
                                                give_pos = renderer.get_card_center(human_idx, pair_opponent_give_slot, game_manager)
                                                renderer.push_pair_fly_animation(game_manager, opp_pos, None, give_pos, None)
                                                game_manager.execute_player_action("pair_opponent", {
                                                    "opponent_index": player.seat_index,
                                                    "opponent_slot": slot_idx,
                                                    "drawn_card": game_manager.drawn_card,
                                                    "give_slot": pair_opponent_give_slot,
                                                })
                                                awaiting = None
                                                pair_opponent_give_slot = None
                                                status_message = ""
                                                turn_end_timer = 0.5
                                                break
                                        else:
                                            continue
                                        break

                            elif awaiting == 'confirm_declare':
                                if clicked_btn == 'declare':
                                    game_manager.execute_player_action("declare", {})
                                    game_manager.resolve_declaration()
                                    game_over_result = game_manager.declaration_result
                                    current_screen = "game_over"
                                awaiting = None
                                status_message = ""

                        else:
                            human_player = game_manager.players[human_idx]
                            if human_idx is not None and cp.is_human and dragging_slot is None:
                                card_rects = renderer.get_card_rects(human_idx, game_manager)
                                for slot_idx, rect in enumerate(card_rects):
                                    if rect.collidepoint(mouse_pos) and human_player.hand[slot_idx] is not None:
                                        center = renderer.get_card_center(human_idx, slot_idx, game_manager)
                                        dragging_slot = slot_idx
                                        drag_offset = (
                                            mouse_pos[0] - center[0],
                                            mouse_pos[1] - center[1],
                                        )
                                        renderer.dragging_card = slot_idx
                                        renderer.drag_pos = mouse_pos
                                        break

                elif event.type == pygame.MOUSEMOTION:
                    if dragging_slot is not None:
                        renderer.drag_pos = mouse_pos

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if dragging_slot is not None and human_idx is not None:
                        human_player = game_manager.players[human_idx]
                        num_players = len(game_manager.players)
                        bounds = _player_area_bounds(human_player.seat_index, num_players)
                        drop_cx = mouse_pos[0] - drag_offset[0]
                        drop_cy = mouse_pos[1] - drag_offset[1]
                        clamped = _clamp_to_bounds(drop_cx, drop_cy, bounds)
                        human_player.card_positions[dragging_slot] = clamped
                        dragging_slot = None
                        renderer.dragging_card = None
                        renderer.drag_pos = None

            elif current_screen == "game_over":
                action = game_over_screen.handle_event(event)
                if action == "play_again":
                    game_over_result = None
                    current_screen = "setup"
                    setup_screen = SetupScreen(screen)
                elif action == "menu":
                    game_over_result = None
                    current_screen = "menu"

        if current_screen == "game" and game_manager is not None:
            cp = game_manager.current_player()
            if not cp.is_human and turn_end_timer <= 0:
                if renderer.is_animating():
                    continue
                ai_timer += dt
                ai_idx = cp.seat_index

                if ai_phase == 'idle':
                    ai_phase = 'drawing'
                    ai_timer = 0.0

                if ai_phase == 'drawing' and ai_timer >= game_settings.ai_delay:
                    should_declare = AIDecider(cp, {'players': game_manager.players}).should_declare()
                    if should_declare:
                        game_manager.execute_player_action("declare", {})
                        game_manager.resolve_declaration()
                        game_over_result = game_manager.declaration_result
                        current_screen = "game_over"
                        ai_phase = 'idle'
                        ai_timer = 0
                        continue
                    game_manager.draw_card()
                    renderer.push_draw_animation(game_manager)
                    ai_phase = 'acting'
                    ai_timer = 0.0

                if ai_phase == 'acting' and ai_timer >= 0.5:
                    ai = AIDecider(cp, {'players': game_manager.players})
                    drawn = game_manager.drawn_card
                    if drawn:
                        decision = ai.choose_action(drawn)
                        action_key = decision['action']

                        if action_key == 'play_power':
                            target_info = _ai_power_target(ai, cp, game_manager.players, drawn)
                            power = drawn.power

                            if power in ('peek_self', 'peek_opponent'):
                                game_manager.execute_player_action('play_power', {
                                    'card': drawn,
                                    'target_info': target_info,
                                })
                                if power == 'peek_self' and target_info:
                                    slot = target_info.get('slot', 0)
                                    if cp.hand[slot] is not None:
                                        cp.known_cards[slot] = cp.hand[slot]
                                    renderer.push_ai_peek_animation(ai_idx, slot, game_manager)
                                elif power == 'peek_opponent' and target_info:
                                    p_idx = target_info.get('player_index', 0)
                                    s_idx = target_info.get('slot', 0)
                                    target_p = next((p for p in game_manager.players if p.seat_index == p_idx), None)
                                    if target_p and target_p.hand[s_idx] is not None:
                                        cp.known_opponent_cards[(p_idx, s_idx)] = target_p.hand[s_idx]
                                    renderer.push_ai_peek_animation(p_idx, s_idx, game_manager)

                            elif power == 'skip':
                                game_manager.execute_player_action('play_power', {
                                    'card': drawn,
                                    'target_info': target_info,
                                })
                                game_manager.skip_next = True
                                renderer.push_ai_skip_animation(game_manager, ai_idx)

                            elif power in ('unseen_swap', 'seen_swap'):
                                my_slot = target_info.get('my_slot', 0)
                                target_player_idx = target_info.get('target_player', 0)
                                their_slot = target_info.get('their_slot', 0)
                                their_card_before = None
                                if power == 'seen_swap':
                                    target_p = next((p for p in game_manager.players if p.seat_index == target_player_idx), None)
                                    if target_p:
                                        their_card_before = target_p.hand[their_slot]
                                my_pos = renderer.get_card_center(ai_idx, my_slot, game_manager)
                                their_pos = renderer.get_card_center(target_player_idx, their_slot, game_manager)
                                game_manager.execute_player_action('play_power', {
                                    'card': drawn,
                                    'target_info': target_info,
                                })
                                if power == 'seen_swap':
                                    renderer.push_seen_swap_animation(
                                        game_manager, my_slot, target_player_idx, their_slot,
                                        their_card_before,
                                    )
                                else:
                                    renderer.push_unseen_swap_animation(
                                        game_manager, my_slot, target_player_idx, their_slot,
                                    )

                            else:
                                game_manager.execute_player_action('play_power', {
                                    'card': drawn,
                                    'target_info': target_info,
                                })

                        elif action_key == 'swap':
                            slot = decision.get('target_slot', ai.estimate_worst_slot())
                            renderer.push_ai_swap_animation(game_manager, ai_idx, slot)
                            game_manager.execute_player_action('swap', {
                                'my_slot': slot,
                                'drawn_card': drawn,
                            })

                        elif action_key == 'discard':
                            renderer.push_discard_animation(game_manager)
                            game_manager.execute_player_action('discard', {'drawn_card': drawn})

                        elif action_key == 'pair_own':
                            slot = decision.get('target_slot', 0)
                            pair_pos = renderer.get_card_center(ai_idx, slot, game_manager)
                            drawn_pos = DRAWN_CARD_POS
                            renderer.push_ai_pair_animation(game_manager, pair_pos, drawn_pos)
                            game_manager.execute_player_action('pair_own', {
                                'player_slot': slot,
                                'drawn_card': drawn,
                            })

                        elif action_key == 'pair_opponent':
                            give_slot = ai.choose_card_to_give()
                            opp_slot = _find_opponent_slot(cp, game_manager.players, decision['target_player'], drawn.rank)
                            opp_idx = decision.get('target_player', 0)
                            opp_pos = renderer.get_card_center(opp_idx, opp_slot, game_manager)
                            give_pos = renderer.get_card_center(ai_idx, give_slot, game_manager)
                            renderer.push_ai_pair_animation(game_manager, opp_pos, give_pos)
                            game_manager.execute_player_action('pair_opponent', {
                                'opponent_index': decision['target_player'],
                                'opponent_slot': opp_slot,
                                'drawn_card': drawn,
                                'give_slot': give_slot,
                            })

                    ai_phase = 'ending'
                    ai_timer = 0.0

                if ai_phase == 'ending' and ai_timer >= 0.3:
                    game_manager.end_turn()
                    ai_phase = 'idle'
                    ai_timer = 0.0
                    awaiting = None
                    selected_slot = None
                    pair_opponent_give_slot = None
                    status_message = ""
                    if game_manager.state == GameState.GAME_OVER:
                        game_over_result = game_manager.declaration_result
                        current_screen = "game_over"

        if current_screen == "game" and game_manager is not None:
            if game_manager.state == GameState.GAME_OVER:
                if game_over_result is None:
                    game_over_result = game_manager.declaration_result or {
                        'winner': game_manager.winner,
                        'scores': {p.seat_index: p.score for p in game_manager.players},
                        'declarer_won': False,
                        'auto_win': False,
                    }
                current_screen = "game_over"
                continue

        if game_manager and game_manager.current_player().is_human and game_manager.state == GameState.TURN_START:
            awaiting = None
            selected_slot = None
            pair_opponent_give_slot = None
            swap_second_click = False
            status_message = ""

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
                awaiting = None
                selected_slot = None
                ai_phase = 'idle'
                ai_timer = 0
                current_screen = "game"

        elif current_screen == "game":
            if game_manager is None:
                current_screen = "menu"
            else:
                cp = game_manager.current_player()
                action_buttons = _build_action_buttons(game_manager, ui_font)
                cancel_btn = None
                if awaiting is not None and cp.is_human:
                    cancel_btn = _build_cancel_button("Cancel", ui_font)
                renderer.draw(game_manager, mouse_pos, action_buttons, cancel_btn, status_message, awaiting)

        elif current_screen == "game_over":
            if game_over_result is None and game_manager:
                game_over_result = game_manager.declaration_result or {
                    'winner': game_manager.winner,
                    'scores': {p.seat_index: p.score for p in game_manager.players},
                    'declarer_won': False,
                    'auto_win': False,
                }
            game_over_screen.draw(game_manager, game_over_result or {})

        if current_screen == "game":
            if settings_open and game_manager:
                settings_menu.draw(game_settings, game_manager, mouse_pos)
            elif game_manager:
                renderer.draw_gear_icon(mouse_pos, settings_open)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()