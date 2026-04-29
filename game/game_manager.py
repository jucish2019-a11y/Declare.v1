from enum import Enum

from config import HAND_SIZE, MAX_PAIR_STACK, PEEK_REVEAL_SECONDS, POWER_LABELS
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
        self.peek_reveal: dict | None = None
        self.declaration_result: dict | None = None

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
        name = "You" if self.current_player().is_human else self.current_player().name
        self.game_log.append(f"{name} drew {self.drawn_card.display_name}")
        return self.drawn_card

    def _format_log(self, action: str, details: dict, result: dict) -> str:
        player = self.current_player()
        name = "You" if player.is_human else player.name

        if action == "declare":
            return f"{name} declared!"

        if action == "play_power":
            card = details.get('card')
            power = card.power if card else None
            label = POWER_LABELS.get(power, power or 'power')
            if power in ('peek_self', 'peek_opponent'):
                if power == 'peek_self':
                    return f"{name} used {label} on slot {result.get('slot')}"
                else:
                    return f"{name} used {label} on P{result.get('player_index')} slot {result.get('slot')}"
            return f"{name} used {label}"

        if action == "swap":
            slot = details.get('my_slot')
            swapped_card = result.get('swapped_card')
            card_str = swapped_card.display_name if swapped_card else ''
            if player.is_human:
                return f"{name} swapped with slot {slot} (discarded {card_str})"
            return f"{name} swapped card"

        if action == "discard":
            discarded = result.get('discarded_card') or details.get('drawn_card')
            card_str = discarded.display_name if discarded else ''
            return f"{name} discarded {card_str}"

        if action == "pair_own":
            return f"{name} paired own card"

        if action == "pair_opponent":
            return f"{name} paired opponent's card"

        return f"{name}: {action}"

    def execute_player_action(self, action: str, details: dict) -> dict:
        valid = get_valid_actions(self.current_player(), self.drawn_card, self.has_drawn_this_turn)
        if action not in valid:
            return {"success": False, "reason": "invalid_action"}
        result = self.rules_engine.execute_action(self.current_player(), action, details)

        if action == "declare":
            self.current_player().is_declaring = True
            self.state = GameState.RESOLVE_DECLARE
        elif action == "play_power":
            card = details.get('card')
            power = card.power if card else None
            if power in ('peek_self', 'peek_opponent'):
                peeked_card = result.get('card')
                if power == 'peek_self':
                    self.peek_reveal = {
                        'card': peeked_card,
                        'slot': result.get('slot'),
                        'timer': PEEK_REVEAL_SECONDS,
                    }
                else:
                    self.peek_reveal = {
                        'card': peeked_card,
                        'player_index': result.get('player_index'),
                        'slot': result.get('slot'),
                        'timer': PEEK_REVEAL_SECONDS,
                    }
                self.state = GameState.DECIDE
            elif power == 'skip':
                self.state = GameState.TURN_END
            elif power in ('unseen_swap', 'seen_swap'):
                self.state = GameState.DECIDE
            else:
                self.state = GameState.DECIDE
        elif action in ("swap", "discard", "pair_own", "pair_opponent"):
            self.state = GameState.DECIDE

        log_entry = self._format_log(action, details, result)
        self.game_log.append(log_entry)
        return result

    def resolve_power_if_needed(self, power_result: dict):
        if power_result.get('skip'):
            self.skip_next = True
        self.state = GameState.DECIDE

    def end_turn(self):
        self.state = GameState.TURN_END
        self.next_turn()

    def resolve_declaration(self) -> dict:
        result = resolve_declare(self.current_player(), self.players)
        self.declaration_result = result
        self.winner = result.get('winner')
        self.state = GameState.GAME_OVER
        return result

    def check_game_over(self) -> bool:
        for player in self.players:
            if has_zero_cards(player):
                scores = {p.seat_index: calculate_score(p) for p in self.players}
                self.declaration_result = {
                    'winner': player,
                    'scores': scores,
                    'declarer_won': True,
                    'auto_win': True,
                }
                self.winner = player
                self.state = GameState.GAME_OVER
                return True
        rules_result = self.rules_engine.check_game_over()
        if rules_result is not None:
            self.declaration_result = rules_result
            self.winner = rules_result.get('winner')
            self.state = GameState.GAME_OVER
            return True
        return False

    def update(self, dt: float):
        if self.peek_reveal is not None:
            self.peek_reveal['timer'] -= dt
            if self.peek_reveal['timer'] <= 0:
                self.peek_reveal = None

    def cancel_targeting(self):
        pass

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