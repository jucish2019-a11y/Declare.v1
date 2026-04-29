from config import HAND_SIZE
from game.card import Card
from game.player import Player


def calculate_score(player: Player) -> int:
    return sum(card.value for card in player.hand if card is not None)


def has_zero_cards(player: Player) -> bool:
    return all(slot is None for slot in player.hand)


def can_declare(player: Player, has_drawn_this_turn: bool) -> bool:
    return not has_drawn_this_turn


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

    if not declarer_won:
        scores[declarer.seat_index] = declarer_score * 2

    return {
        'winner': declarer if declarer_won else None,
        'scores': scores,
        'declarer_won': declarer_won,
        'auto_win': False,
    }


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