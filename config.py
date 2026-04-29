SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
AI_DELAY = 0.8
PEEK_REVEAL_SECONDS = 2.5

BG_GREEN = (39, 119, 62)
BG_DARK = (20, 20, 20)
CARD_WHITE = (255, 255, 255)
CARD_BACK_BLUE = (30, 60, 120)
CARD_BACK_PATTERN = (40, 80, 150)
CARD_SHADOW = (15, 15, 15)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
GOLD = (255, 215, 0)
TEXT_WHITE = (255, 255, 255)
TEXT_BLACK = (0, 0, 0)
TEXT_DIM = (180, 180, 180)
HIGHLIGHT = (255, 255, 100)
DIM = (100, 100, 100)
PANEL_BG = (15, 15, 15)
PANEL_BORDER = (60, 60, 60)
POWER_GLOW = (80, 180, 255)
EMPTY_SLOT = (60, 90, 60)
KNOWN_TINT = (255, 215, 0, 40)
DECLARE_RED = (220, 40, 40)
DECLARE_RED_HOVER = (255, 70, 70)
CANCEL_GRAY = (100, 100, 100)
CANCEL_GRAY_HOVER = (140, 140, 140)
PEEK_BLUE = (70, 140, 220)
PEEK_BLUE_HOVER = (100, 170, 250)
SWAP_GREEN = (40, 130, 60)
SWAP_GREEN_HOVER = (60, 170, 80)
DISCARD_ORANGE = (200, 120, 30)
DISCARD_ORANGE_HOVER = (230, 150, 50)
PAIR_TEAL = (40, 140, 160)
PAIR_TEAL_HOVER = (60, 170, 190)

STATUS_BAR_H = 42
ACTION_BAR_Y = 650
ACTION_BAR_H = 70

CARD_WIDTH = 80
CARD_HEIGHT = 112
CORNER_RADIUS = 8

CARD_SPREAD = 30

DECK_CENTER = (520, 330)
DRAWN_CARD_POS = (720, 330)
DISCARD_POS = (620, 330)

PLAYER_BOTTOM = (640, 510)
PLAYER_TOP = (640, 170)
PLAYER_LEFT = (200, 350)
PLAYER_RIGHT = (1080, 350)

LOG_PANEL_X = 950
LOG_PANEL_Y = 420
LOG_PANEL_W = 310
LOG_PANEL_H = 220

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

POWER_LABELS = {
    'peek_self': 'Peek Self',
    'peek_opponent': 'Peek Opponent',
    'skip': 'Skip Next',
    'unseen_swap': 'Unseen Swap',
    'seen_swap': 'Seen Swap',
}

POWER_COLORS = {
    'peek_self': PEEK_BLUE,
    'peek_opponent': PEEK_BLUE,
    'skip': DECLARE_RED,
    'unseen_swap': SWAP_GREEN,
    'seen_swap': SWAP_GREEN,
}

CARD_FONT_SIZE = 18
CARD_BIG_FONT_SIZE = 28
TITLE_FONT_SIZE = 56
SUBTITLE_FONT_SIZE = 22
UI_FONT_SIZE = 20
LOG_FONT_SIZE = 15
SMALL_FONT_SIZE = 14