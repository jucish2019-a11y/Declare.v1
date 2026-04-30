from __future__ import annotations
import random
from config import CARD_VALUES, POWER_CARDS, POWER_LABELS
from game.card import Card


class AIDecider:
    THRESHOLDS = {'easy': 8, 'medium': 10, 'normal': 10, 'hard': 12}

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
                return {
                    'action': 'pair_own',
                    'target_slot': slot_idx,
                    'log_message': f"{self.player.name} paired own card (slot {slot_idx})",
                }

        for (p_idx, s_idx), card in self.player.known_opponent_cards.items():
            if card.rank == drawn_card.rank:
                give_slot = self.choose_card_to_give()
                return {
                    'action': 'pair_opponent',
                    'target_slot': give_slot,
                    'target_player': p_idx,
                    'log_message': f"{self.player.name} paired opponent's card",
                }

        if drawn_card.power is not None:
            beneficial = self._is_power_beneficial(drawn_card)
            if beneficial:
                label = POWER_LABELS.get(drawn_card.power, drawn_card.power)
                return {
                    'action': 'play_power',
                    'power': drawn_card.power,
                    'target_player': self._power_target(drawn_card),
                    'log_message': f"{self.player.name} used {label}",
                }

        worst_slot = self.estimate_worst_slot()
        if worst_slot is not None and drawn_card.value < self._slot_estimated_value(worst_slot):
            return {
                'action': 'swap',
                'target_slot': worst_slot,
                'log_message': f"{self.player.name} swapped card",
            }

        return {
            'action': 'discard',
            'log_message': f"{self.player.name} discarded {drawn_card.display_name}",
        }

    def should_self_pair(self) -> list | None:
        pairs = self.player.find_self_pairs()
        if pairs:
            return pairs
        return None

    def should_react_to_discard(self, discarded_rank: str) -> dict | None:
        own_matches = []
        for slot in self.player.get_active_slots():
            if slot in self.player.known_cards and self.player.known_cards[slot].rank == discarded_rank:
                own_matches.append(slot)

        if own_matches:
            difficulty = self.player.difficulty
            react_chance = {'easy': 0.4, 'medium': 0.75, 'normal': 0.75, 'hard': 0.95}
            if random.random() < react_chance.get(difficulty, 0.75):
                best_slot = max(own_matches, key=lambda s: self.player.known_cards[s].value)
                return {
                    'type': 'react_drop_self',
                    'slot': best_slot,
                }
            return None

        players = self.game_state.get('players', [])
        for opp in players:
            if opp.seat_index == self.player.seat_index:
                continue
            opp_matches = []
            for slot in opp.get_active_slots():
                if (opp.seat_index, slot) in self.player.known_opponent_cards:
                    if self.player.known_opponent_cards[(opp.seat_index, slot)].rank == discarded_rank:
                        opp_matches.append((opp.seat_index, slot))

            if opp_matches:
                difficulty = self.player.difficulty
                react_chance = {'easy': 0.2, 'medium': 0.5, 'normal': 0.5, 'hard': 0.8}
                if random.random() < react_chance.get(difficulty, 0.5):
                    opp_idx, opp_slot = opp_matches[0]
                    give_slot = self.choose_card_to_give()
                    return {
                        'type': 'react_drop_opponent',
                        'opponent_index': opp_idx,
                        'opponent_slot': opp_slot,
                        'give_slot': give_slot,
                    }

        return None

    def should_react(self, reaction_rank: str, difficulty: str) -> bool:
        if reaction_rank not in self.player.known_cards.values():
            return False
        react_chance = {'easy': 0.5, 'medium': 0.8, 'normal': 0.8, 'hard': 1.0}
        return random.random() < react_chance.get(difficulty, 0.8)

    def choose_reaction_slot(self, reaction_rank: str) -> int | None:
        matches = [s for s in self.player.get_active_slots() if s in self.player.known_cards and self.player.known_cards[s].rank == reaction_rank]
        if not matches:
            return None
        return max(matches, key=lambda s: self.player.known_cards[s].value)

    def should_shuffle(self) -> bool:
        known_by_others = 0
        players = self.game_state.get('players', [])
        for opp in players:
            if opp.seat_index == self.player.seat_index:
                continue
            for key, card in opp.known_opponent_cards.items():
                if key[0] == self.player.seat_index:
                    known_by_others += 1

        if known_by_others == 0:
            return False

        difficulty = self.player.difficulty
        shuffle_thresholds = {'easy': 3, 'medium': 2, 'normal': 2, 'hard': 1}
        threshold = shuffle_thresholds.get(difficulty, 2)
        return known_by_others >= threshold

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