# Declare

A card game of memory, strategy, and bluffing — built with Python and Pygame.

## Rules

### Setup
- Each player receives **4 cards face-down**
- You may peek at your **bottom 2 cards once** — memorize them!

### Gameplay
Players take turns. On your turn:
1. **Draw** a card from the deck
2. **Choose** one of the following actions:
   - **Play a power card** (if the drawn card has a power)
   - **Swap** the drawn card with one of your face-down cards
   - **Discard** the drawn card
   - **Pair** the drawn card with a matching card (yours or an opponent's known card)

### Declaring
- When you believe you have the lowest score, **declare** at the start of your turn (before drawing)
- You win if your score is **strictly lower** than all other players
- If you're wrong, you receive a **2× penalty** on your score
- Having **zero cards** is an automatic win

### Card Values

| Card | Value | Power |
|------|-------|-------|
| A | 1 | — |
| 2–6 | face value | — |
| 7, 8 | face value | Peek at one of your own cards |
| 9, 10 | face value | Peek at an opponent's card |
| J | 11 | Skip next player's turn |
| Q | 12 | Unseen swap (swap without looking) |
| Red K (♥♦) | 13 | Seen swap (swap, you see both cards) |
| Black K (♠♣) | 0 | — |

### Pairing
- You can pair **2 cards of the same rank** at any point during your turn
- Pairing your own cards: both are discarded
- Pairing with an opponent's known card: both are discarded, but you **give one of your cards** to that opponent
- Maximum stack size: 2 cards

## Installation

```bash
pip install -r requirements.txt
```

## How to Play

```bash
python main.py
```

### Controls
- **Mouse click** — interact with cards, buttons, deck
- **D key** — shortcut to declare
- Game supports **2–4 players** with human or AI opponents

## Project Structure

```
declare/
├── main.py              # Entry point and game loop
├── config.py            # Game constants and configuration
├── game/
│   ├── card.py          # Card and Deck classes
│   ├── player.py        # Player, HumanPlayer, AIPlayer
│   ├── rules.py         # Rules engine and scoring
│   ├── game_manager.py  # State machine and turn flow
│   └── ai.py            # AI decision logic
├── ui/
│   ├── renderer.py      # Pygame rendering
│   ├── animations.py    # Card animations
│   └── screens.py      # Menu, setup, peek, game over screens
└── assets/              # (programmatic — no external assets needed)
```

## License

MIT