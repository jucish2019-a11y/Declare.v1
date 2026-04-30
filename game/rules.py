from __future__ import annotations
import pygame
from config import HAND_SIZE, POWER_LABELS, SWAP_REVEAL_SECONDS
from game.card import Card
from game.player import Player


def calculate_score(player: Player) -> int:
    return sum(card.value for card in player.hand if card is not None)


def has_zero_cards(player: Player) -> bool:
    return all(slot is None for slot in player.hand)


def can_declare(player: Player, has_drawn_this_turn: bool) -> bool:
    return not player.is_declaring


def resolve_declare(declarer: Player, all_players: list) -> dict:
    scores = {}
    for p in all_players:
        scores[p.seat_index] = calculate_score(p)

    if has_zero_cards(declarer):
        return {
            'winner': declarer,
            'scores': scores,
            'declarer_won': True,
            'auto_win': True,
        }

    declarer_score = scores[declarer.seat_index]
    declarer_won = all(
        declarer_score < scores[p.seat_index]
        for p in all_players
        if p.seat_index != declarer.seat_index
    )

    result_scores = dict(scores)
    if not declarer_won:
        result_scores[declarer.seat_index] = declarer_score * 2

    return {
        'winner': declarer if declarer_won else None,
        'scores': result_scores,
        'declarer_won': declarer_won,
        'auto_win': False,
    }


def format_action_log(action: str, player_name: str, details: dict = None, card: Card = None) -> str:
    if action == 'declare':
        return f"{player_name} declared!"

    if action == 'draw':
        card_str = card.display_name if card else '?'
        return f"{player_name} drew {card_str}"

    if action == 'swap':
        slot = details.get('my_slot') if details else None
        if slot is not None:
            return f"{player_name} swapped with slot {slot}"
        return f"{player_name} swapped card"

    if action == 'discard':
        card_str = card.display_name if card else '?'
        return f"{player_name} discarded {card_str}"

    if action in ('pair_own',):
        return f"{player_name} paired own card"

    if action in ('pair_opponent',):
        return f"{player_name} paired opponent's card"

    if action == 'play_power':
        power = details.get('power') if details else None
        label = POWER_LABELS.get(power, power or 'power')
        if power == 'peek_self':
            slot = details.get('slot') if details else None
            return f"{player_name} used {label} on slot {slot}" if slot is not None else f"{player_name} used {label}"
        if power == 'peek_opponent':
            p_idx = details.get('target_player') if details else None
            return f"{player_name} used {label} on P{p_idx}" if p_idx is not None else f"{player_name} used {label}"
        return f"{player_name} used {label}"

    if action == 'self_pair':
        return f"{player_name} self-paired cards"

    if action == 'shuffle':
        return f"{player_name} shuffled their cards"

    if action == 'react_drop_self':
        card_str = card.display_name if card else '?'
        return f"{player_name} dropped {card_str} to match discard"

    if action == 'react_drop_opponent':
        return f"{player_name} called opponent's matching card"

    return f"{player_name}: {action}"


def validate_pair(card1: Card, card2: Card) -> bool:
    return card1.rank == card2.rank


def execute_pair_drop(player: Player, player_slot: int, drawn_card: Card) -> dict:
    removed = player.remove_card(player_slot)
    return {
        'action': 'pair_own',
        'slots_removed': [player_slot],
        'card_discarded': [removed, drawn_card],
    }


def execute_pair_opponent(player: Player, opponent: Player, opponent_slot: int, drawn_card: Card, give_slot: int) -> dict:
    opponent.remove_card(opponent_slot)
    given_card = player.remove_card(give_slot)
    opponent.receive_card(given_card, opponent_slot)
    return {
        'action': 'pair_opponent',
        'opponent_index': opponent.seat_index,
        'opponent_slot_removed': opponent_slot,
        'card_given_slot': give_slot,
    }


def execute_self_pair(player: Player, slot_a: int, slot_b: int) -> dict:
    card_a = player.remove_card(slot_a)
    card_b = player.remove_card(slot_b)
    return {
        'action': 'self_pair',
        'slots_removed': [slot_a, slot_b],
        'cards_discarded': [card_a, card_b],
    }


def can_self_pair(player: Player) -> list:
    return player.find_self_pairs()


def can_react_to_discard(reacting_player: Player, discarded_rank: str) -> list:
    matching = []
    for slot in reacting_player.get_active_slots():
        if slot in reacting_player.known_cards and reacting_player.known_cards[slot].rank == discarded_rank:
            matching.append(slot)
    return matching


def can_call_opponent_card(reacting_player: Player, opponent: Player, discarded_rank: str) -> list:
    matching = []
    for slot in opponent.get_active_slots():
        if (opponent.seat_index, slot) in reacting_player.known_opponent_cards:
            if reacting_player.known_opponent_cards[(opponent.seat_index, slot)].rank == discarded_rank:
                matching.append(slot)
    return matching


def validate_reactive_drop(player: Player, slot: int, expected_rank: str) -> bool:
    if player.hand[slot] is None:
        return False
    return player.hand[slot].rank == expected_rank


def execute_reactive_drop_self(player: Player, slot: int) -> dict:
    card = player.remove_card(slot)
    return {
        'action': 'react_drop_self',
        'slot': slot,
        'card': card,
    }


def execute_reactive_drop_opponent(reacting_player: Player, opponent: Player, opponent_slot: int, give_slot: int) -> dict:
    opponent_card = opponent.remove_card(opponent_slot)
    given_card = reacting_player.remove_card(give_slot)
    opponent.receive_card(given_card, opponent_slot)
    return {
        'action': 'react_drop_opponent',
        'opponent_index': opponent.seat_index,
        'opponent_slot': opponent_slot,
        'give_slot': give_slot,
        'opponent_card': opponent_card,
        'given_card': given_card,
    }


def execute_wrong_drop_penalty(player: Player, original_slot: int, all_players: list, deck) -> dict:
    target_seat = None
    for p in all_players:
        for key in player.known_opponent_cards:
            if key[0] == p.seat_index:
                target_seat = p.seat_index
                break
        if target_seat is not None:
            break

    target_player = None
    if target_seat is not None:
        target_player = next((p for p in all_players if p.seat_index == target_seat), None)

    if target_player is not None:
        target_player.shuffle_hand(all_players)

    penalty_card = None
    penalty_slot = None
    if deck and not deck.is_empty:
        penalty_card = deck.draw()
        if penalty_card is not None:
            penalty_slot = player.add_penalty_card(penalty_card)

    return {
        'action': 'wrong_drop_penalty',
        'original_slot': original_slot,
        'target_player_shuffled': target_seat,
        'penalty_card': penalty_card,
        'penalty_slot': penalty_slot,
    }


def resolve_power(card: Card, current_player: Player, all_players: list, target_info: dict = None) -> dict:
    power = card.power

    if power is None:
        return {'action': 'no_power'}

    if power == 'peek_self':
        slot = target_info['slot']
        peeked_card = current_player.hand[slot]
        current_player.known_cards[slot] = peeked_card
        return {'action': 'peek_self', 'slot': slot, 'card': peeked_card}

    if power == 'peek_opponent':
        target_index = target_info['player_index']
        target_slot = target_info['slot']
        target_player = next(p for p in all_players if p.seat_index == target_index)
        peeked_card = target_player.hand[target_slot]
        current_player.known_opponent_cards[(target_index, target_slot)] = peeked_card
        return {
            'action': 'peek_opponent',
            'player_index': target_index,
            'slot': target_slot,
            'card': peeked_card,
        }

    if power == 'skip':
        return {'action': 'skip', 'skip_next': True}

    if power == 'unseen_swap':
        my_slot = target_info['my_slot']
        target_player_index = target_info['target_player']
        their_slot = target_info['their_slot']
        target_player = next(p for p in all_players if p.seat_index == target_player_index)
        current_player.swap_cards(my_slot, target_player, their_slot)
        current_player.known_cards.pop(my_slot, None)
        target_player.known_cards.pop(their_slot, None)
        current_player.known_opponent_cards.pop((target_player_index, their_slot), None)
        target_player.known_opponent_cards.pop((current_player.seat_index, my_slot), None)
        target_player.mark_received_card(their_slot, SWAP_REVEAL_SECONDS, pygame.time.get_ticks() / 1000.0)
        return {
            'action': 'unseen_swap',
            'my_slot': my_slot,
            'target_player': target_player_index,
            'their_slot': their_slot,
        }

    if power == 'seen_swap':
        my_slot = target_info['my_slot']
        target_player_index = target_info['target_player']
        their_slot = target_info['their_slot']
        target_player = next(p for p in all_players if p.seat_index == target_player_index)
        my_card_before = current_player.hand[my_slot]
        their_card_before = target_player.hand[their_slot]
        current_player.swap_cards(my_slot, target_player, their_slot)
        current_player.known_cards[my_slot] = their_card_before
        current_player.known_cards.pop(their_slot, None)
        current_player.known_opponent_cards[(target_player_index, their_slot)] = my_card_before
        target_player.mark_received_card(their_slot, SWAP_REVEAL_SECONDS, pygame.time.get_ticks() / 1000.0)
        return {
            'action': 'seen_swap',
            'my_slot': my_slot,
            'target_player': target_player_index,
            'their_slot': their_slot,
            'card_received': their_card_before,
            'card_given': my_card_before,
        }

    return {'action': 'no_power'}


def get_valid_actions(player: Player, drawn_card: Card = None, has_drawn: bool = False) -> list:
    actions = []

    if not has_drawn:
        if can_declare(player, False):
            actions.append('declare')
        actions.append('draw')
        return actions

    if drawn_card is None:
        return actions

    if drawn_card.power is not None:
        actions.append('play_power')

    actions.append('swap')
    actions.append('discard')

    for slot in player.get_active_slots():
        if slot in player.known_cards and player.known_cards[slot].rank == drawn_card.rank:
            if 'pair_own' not in actions:
                actions.append('pair_own')
            break

    for key, card in player.known_opponent_cards.items():
        if card.rank == drawn_card.rank:
            actions.append('pair_opponent')
            break

    if can_declare(player, True):
        actions.append('declare')

    return actions


class RulesEngine:
    def __init__(self, players: list, deck, discard_pile: list):
        self.players = players
        self.deck = deck
        self.discard_pile = discard_pile
        self.turn_log: list = []

    def execute_action(self, player, action: str, details: dict) -> dict:
        result = {'action': action, 'player': player.seat_index}

        if action == 'declare':
            declare_result = resolve_declare(player, self.players)
            result.update(declare_result)

        elif action == 'draw':
            drawn = self.deck.draw()
            result['drawn_card'] = drawn

        elif action == 'play_power':
            card = details.get('card')
            power_result = resolve_power(card, player, self.players, details.get('target_info'))
            result.update(power_result)
            self.discard_pile.append(card)
            card.face_up = True

        elif action == 'swap':
            my_slot = details['my_slot']
            drawn_card = details['drawn_card']
            swapped = player.remove_card(my_slot)
            player.receive_card(drawn_card, my_slot)
            player.known_cards[my_slot] = drawn_card
            self.discard_pile.append(swapped)
            swapped.face_up = True
            result['swapped_card'] = swapped
            result['slot'] = my_slot

        elif action == 'discard':
            drawn_card = details['drawn_card']
            self.discard_pile.append(drawn_card)
            drawn_card.face_up = True
            result['discarded_card'] = drawn_card

        elif action == 'pair_own':
            player_slot = details['player_slot']
            drawn_card = details['drawn_card']
            pair_result = execute_pair_drop(player, player_slot, drawn_card)
            result.update(pair_result)
            self.discard_pile.extend(pair_result['card_discarded'])

        elif action == 'pair_opponent':
            opponent = next(p for p in self.players if p.seat_index == details['opponent_index'])
            opponent_slot = details['opponent_slot']
            drawn_card = details['drawn_card']
            give_slot = details['give_slot']
            pair_result = execute_pair_opponent(player, opponent, opponent_slot, drawn_card, give_slot)
            result.update(pair_result)
            self.discard_pile.append(drawn_card)

        elif action == 'self_pair':
            slot_a = details['slot_a']
            slot_b = details['slot_b']
            pair_result = execute_self_pair(player, slot_a, slot_b)
            result.update(pair_result)
            self.discard_pile.extend(pair_result['cards_discarded'])
            for c in pair_result['cards_discarded']:
                c.face_up = True

        elif action == 'shuffle':
            player.shuffle_hand(self.players)

        self.turn_log.append(result)
        return result

    def check_game_over(self):
        for p in self.players:
            if p.is_declaring:
                return resolve_declare(p, self.players)

        for p in self.players:
            if has_zero_cards(p):
                return {
                    'winner': p,
                    'scores': {pl.seat_index: calculate_score(pl) for pl in self.players},
                    'declarer_won': True,
                    'auto_win': True,
                }

        return None