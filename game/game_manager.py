from enum import Enum

from config import HAND_SIZE, MAX_PAIR_STACK
from game.card import Card, Deck
from game.player import Player, HumanPlayer, AIPlayer
from game.rules import RulesEngine, get_valid_actions, resolve_declare, resolve_power, has_zero_cards, calculate_score


class GameState(Enum):
    MENU = "menu"
    SETUP = "setup"
    PEEK_PHASE = "peek_phase"
    TURN_START = "turn_start"
    DRAW = "draw"
    DECIDE = "decide"
    POWER_RESOLVE = "power_resolve"
    PAIR_CHECK = "pair_check"
    TURN_END = "turn_end"
    RESOLVE_DECLARE = "resolve_declare"
    GAME_OVER = "game_over"


class GameManager:
    def __init__(self, player_configs: list[dict]):
        self.players: list[Player] = []
        for config in player_configs:
            if config["is_human"]:
                self.players.append(HumanPlayer(config["name"], len(self.players)))
            else:
                self.players.append(AIPlayer(config["name"], len(self.players), "medium"))
        self.deck: Deck = None
        self.discard_pile: list[Card] = []
        self.rules_engine: RulesEngine = None
        self.state: GameState = GameState.MENU
        self.current_player_index: int = 0
        self.drawn_card: Card | None = None
        self.has_drawn_this_turn: bool = False
        self.skip_next: bool = False
        self.round_number: int = 0
        self.game_log: list[str] = []
        self.winner: Player | None = None
        self.peek_timer: float = 0

    def setup_game(self):
        self.deck = Deck()
        self.discard_pile = []
        self.rules_engine = RulesEngine(self.players, self.deck, self.discard_pile)
        for player in self.players:
            for slot in range(HAND_SIZE):
                card = self.deck.draw()
                player.receive_card(card, slot)
        self.state = GameState.PEEK_PHASE
        self.current_player_index = 0
        self.round_number = 1

    def start_peek_phase(self):
        for player in self.players:
            if isinstance(player, HumanPlayer):
                for slot in [2, 3]:
                    card = player.hand[slot]
                    if card is not None:
                        player.known_cards[slot] = card
                player.has_peeked_initial = True
        self.state = GameState.TURN_START

    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.skip_next:
            self.skip_next = False
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.has_drawn_this_turn = False
        self.drawn_card = None
        if self.current_player().is_declaring:
            self.state = GameState.RESOLVE_DECLARE
        else:
            self.state = GameState.TURN_START

    def draw_card(self) -> Card:
        if self.deck.is_empty:
            self.deck.reshuffle(self.discard_pile)
            self.discard_pile.clear()
        self.drawn_card = self.deck.draw()
        self.drawn_card.face_up = True
        self.has_drawn_this_turn = True
        self.state = GameState.DECIDE
        return self.drawn_card

    def execute_player_action(self, action: str, details: dict) -> dict:
        valid = get_valid_actions(self.current_player(), self.drawn_card, self.has_drawn_this_turn)
        if action not in valid:
            return {"success": False, "reason": "invalid_action"}
        result = self.rules_engine.execute_action(self.current_player(), action, details)
        if action == "declare":
            self.current_player().is_declaring = True
            self.state = GameState.RESOLVE_DECLARE
        elif action in ("pair_own", "pair_opponent"):
            self.state = GameState.PAIR_CHECK
        elif action == "play_power" or result.get("action") in ("peek_self", "peek_opponent", "skip", "unseen_swap", "seen_swap"):
            self.state = GameState.POWER_RESOLVE
        entry = f"{self.current_player().name}: {action}"
        if details:
            entry += f" {details}"
        self.game_log.append(entry)
        return result

    def resolve_power_if_needed(self, power_result: dict):
        if power_result.get("skip"):
            self.skip_next = True
        self.state = GameState.DECIDE

    def end_turn(self):
        self.state = GameState.TURN_END
        self.next_turn()

    def resolve_declaration(self) -> dict:
        result = resolve_declare(self.current_player(), self.players)
        self.winner = result.get("winner")
        self.state = GameState.GAME_OVER
        return result

    def check_game_over(self) -> bool:
        for player in self.players:
            if has_zero_cards(player):
                self.winner = player
                self.state = GameState.GAME_OVER
                return True
        rules_result = self.rules_engine.check_game_over()
        if rules_result is not None:
            self.winner = rules_result.get("winner")
            self.state = GameState.GAME_OVER
            return True
        return False

    def get_game_state_info(self) -> dict:
        from game.rules import get_valid_actions as _get_valid_actions
        valid = _get_valid_actions(self.current_player(), self.drawn_card, self.has_drawn_this_turn)
        return {
            "state": self.state,
            "current_player": self.current_player(),
            "current_player_index": self.current_player_index,
            "drawn_card": self.drawn_card,
            "deck_remaining": self.deck.remaining if self.deck else 0,
            "valid_actions": valid,
            "game_log": self.game_log[-10:],
        }