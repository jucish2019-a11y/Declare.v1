SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

BG_GREEN = (39, 119, 62)
CARD_WHITE = (255, 255, 255)
CARD_BACK_BLUE = (30, 60, 120)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
GOLD = (255, 215, 0)
TEXT_WHITE = (255, 255, 255)
TEXT_BLACK = (0, 0, 0)
HIGHLIGHT = (255, 255, 100)
DIM = (100, 100, 100)

CARD_WIDTH = 80
CARD_HEIGHT = 112
CORNER_RADIUS = 6

CARD_SPREAD = 24

DECK_POSITION = (640, 360)

PLAYER_BOTTOM = (640, 620)
PLAYER_TOP = (640, 100)
PLAYER_LEFT = (120, 360)
PLAYER_RIGHT = (1160, 360)

CARD_VALUES = {
    'A': 1,
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13,
}

BLACK_KING_VALUE = 0

RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUITS = ['spade', 'heart', 'diamond', 'club']

HAND_SIZE = 4
MAX_PAIR_STACK = 2

POWER_CARDS = {
    '7': 'peek_self',
    '8': 'peek_self',
    '9': 'peek_opponent',
    '10': 'peek_opponent',
    'J': 'skip',
    'Q': 'unseen_swap',
    ('K', 'heart'): 'seen_swap',
    ('K', 'diamond'): 'seen_swap',
    ('K', 'spade'): None,
    ('K', 'club'): None,
}

CARD_FONT_SIZE = 18
TITLE_FONT_SIZE = 48
UI_FONT_SIZE = 24
LOG_FONT_SIZE = 16