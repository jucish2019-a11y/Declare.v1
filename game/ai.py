import random
from config import CARD_VALUES, POWER_CARDS
from game.card import Card


class AIDecider:
    THRESHOLDS = {'easy': 8, 'normal': 10, 'hard': 12}

    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state

    def should_declare(self) -> bool:
        if self.player.has_zero_cards:
            return True
        estimated_sum = 0
        for i, slot in enumerate(self.player.hand):
            if slot is None:
                continue
            if i in self.player.known_cards:
                estimated_sum += self.player.known_cards[i].value
            else:
                estimated_sum += sum(CARD_VALUES.values()) / len(CARD_VALUES)
        threshold = self.THRESHOLDS.get(self.player.difficulty, 10)
        return estimated_sum < threshold

    def choose_action(self, drawn_card: Card) -> dict:
        for slot_idx, card in self.player.known_cards.items():
            if self.player.hand[slot_idx] is not None and card.rank == drawn_card.rank:
                return {'action': 'pair_own', 'target_slot': slot_idx}

        for (p_idx, s_idx), card in self.player.known_opponent_cards.items():
            if card.rank == drawn_card.rank:
                give_slot = self.choose_card_to_give()
                return {
                    'action': 'pair_opponent',
                    'target_slot': give_slot,
                    'target_player': p_idx,
                }

        if drawn_card.power is not None:
            beneficial = self._is_power_beneficial(drawn_card)
            if beneficial:
                return {
                    'action': 'play_power',
                    'power': drawn_card.power,
                    'target_player': self._power_target(drawn_card),
                }

        worst_slot = self.estimate_worst_slot()
        if worst_slot is not None and drawn_card.value < self._slot_estimated_value(worst_slot):
            return {'action': 'swap', 'target_slot': worst_slot}

        return {'action': 'discard'}

    def _slot_estimated_value(self, slot_idx: int) -> int:
        if slot_idx in self.player.known_cards:
            return self.player.known_cards[slot_idx].value
        return sum(CARD_VALUES.values()) / len(CARD_VALUES)

    def estimate_worst_slot(self) -> int:
        active = self.player.get_active_slots()
        if not active:
            return None
        best_slot = None
        best_value = -1
        for slot_idx in active:
            est = self._slot_estimated_value(slot_idx)
            if est > best_value:
                best_value = est
                best_slot = slot_idx
        return best_slot

    def choose_card_to_give(self) -> int:
        known_active = []
        for slot_idx in self.player.get_active_slots():
            if slot_idx in self.player.known_cards:
                known_active.append((slot_idx, self.player.known_cards[slot_idx].value))
        if known_active:
            known_active.sort(key=lambda x: x[1], reverse=True)
            return known_active[0][0]
        active = self.player.get_active_slots()
        if active:
            return random.choice(active)
        return 0

    def _is_power_beneficial(self, card: Card) -> bool:
        power = card.power
        if power in ('peek_self', 'peek_opponent'):
            unknown_own = [i for i in self.player.get_active_slots() if i not in self.player.known_cards]
            if power == 'peek_self' and unknown_own:
                return True
            if power == 'peek_opponent':
                return True
        if power in ('unseen_swap', 'seen_swap'):
            return True
        if power == 'skip':
            return True
        return False

    def _power_target(self, card: Card) -> int:
        power = card.power
        if power in ('peek_opponent', 'seen_swap'):
            return self._pick_opponent_with_most_unknown()
        return None

    def _pick_opponent_with_most_unknown(self) -> int:
        best_player = None
        best_count = -1
        for p in self.game_state['players']:
            if p.seat_index == self.player.seat_index:
                continue
            unknown = sum(
                1 for i in p.get_active_slots()
                if (p.seat_index, i) not in self.player.known_opponent_cards
            )
            if unknown > best_count:
                best_count = unknown
                best_player = p.seat_index
        return best_player

    def peek_target_own(self, hand) -> int:
        unknown = [i for i in range(len(hand)) if hand[i] is not None and i not in self.player.known_cards]
        if unknown:
            return random.choice(unknown)
        active = [i for i in range(len(hand)) if hand[i] is not None]
        return random.choice(active) if active else 0

    def peek_target_opponent(self, players) -> tuple:
        best_player = None
        best_slot = None
        best_unknown = -1
        for p in players:
            if p.seat_index == self.player.seat_index:
                continue
            for i in range(len(p.hand)):
                if p.hand[i] is not None and (p.seat_index, i) not in self.player.known_opponent_cards:
                    unknown_count = sum(
                        1 for j in range(len(p.hand))
                        if p.hand[j] is not None and (p.seat_index, j) not in self.player.known_opponent_cards
                    )
                    if unknown_count > best_unknown:
                        best_unknown = unknown_count
                        best_player = p.seat_index
                        best_slot = i
                    break
        if best_player is not None:
            return (best_player, best_slot)
        for p in players:
            if p.seat_index != self.player.seat_index:
                for i in range(len(p.hand)):
                    if p.hand[i] is not None:
                        return (p.seat_index, i)
        return (0, 0)