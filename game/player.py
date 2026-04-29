import random
from config import HAND_SIZE
from game.card import Card


class Player:
    def __init__(self, name: str, is_human: bool, seat_index: int):
        self.name = name
        self.is_human = is_human
        self.seat_index = seat_index
        self.hand: list = [None] * HAND_SIZE
        self.known_cards: dict = {}
        self.known_opponent_cards: dict = {}
        self.has_peeked_initial: bool = False
        self.is_declaring: bool = False

    @property
    def has_zero_cards(self) -> bool:
        return all(slot is None for slot in self.hand)

    @property
    def card_count(self) -> int:
        return sum(1 for slot in self.hand if slot is not None)

    @property
    def score(self) -> int:
        return sum(slot.value for slot in self.hand if slot is not None)

    def receive_card(self, card: Card, slot: int):
        self.hand[slot] = card

    def remove_card(self, slot: int) -> Card:
        card = self.hand[slot]
        self.hand[slot] = None
        self.known_cards.pop(slot, None)
        return card

    def swap_cards(self, my_slot: int, other_player, their_slot: int):
        my_card = self.hand[my_slot]
        their_card = other_player.hand[their_slot]
        self.hand[my_slot] = their_card
        other_player.hand[their_slot] = my_card
        self.known_cards.pop(my_slot, None)
        other_player.known_cards.pop(their_slot, None)
        self.known_opponent_cards.pop((other_player.seat_index, their_slot), None)
        other_player.known_opponent_cards.pop((self.seat_index, my_slot), None)

    def get_active_slots(self) -> list:
        return [i for i, slot in enumerate(self.hand) if slot is not None]

    def reset_targeting_state(self):
        pass


class HumanPlayer(Player):
    def __init__(self, name: str, seat_index: int):
        super().__init__(name, is_human=True, seat_index=seat_index)


class AIPlayer(Player):
    def __init__(self, name: str, seat_index: int, difficulty: str = 'normal'):
        super().__init__(name, is_human=False, seat_index=seat_index)
        self.difficulty = difficulty