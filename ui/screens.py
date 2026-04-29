import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_GREEN, CARD_WHITE, CARD_BACK_BLUE,
    BLACK, RED, GOLD, TEXT_WHITE, TEXT_BLACK, HIGHLIGHT, DIM,
    CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS, CARD_SPREAD,
    PLAYER_BOTTOM, PLAYER_TOP, PLAYER_LEFT, PLAYER_RIGHT,
    TITLE_FONT_SIZE, UI_FONT_SIZE, LOG_FONT_SIZE, HAND_SIZE,
)


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=TEXT_WHITE, font_size=UI_FONT_SIZE):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(screen, BLACK, self.rect, width=2, border_radius=CORNER_RADIUS)
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos, mouse_click) -> bool:
        if mouse_click and self.rect.collidepoint(mouse_pos):
            return True
        return False

    def update_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)


class MenuScreen:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", TITLE_FONT_SIZE, bold=True)
        self.subtitle_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.buttons = [
            Button(SCREEN_WIDTH // 2, 360, 260, 54, "New Game", (40, 100, 50), (60, 140, 70)),
            Button(SCREEN_WIDTH // 2, 430, 260, 54, "Settings", (40, 100, 50), (60, 140, 70)),
            Button(SCREEN_WIDTH // 2, 500, 260, 54, "Quit", (140, 40, 40), (180, 60, 60)),
        ]

    def draw(self):
        self.screen.fill(BG_GREEN)
        title_surf = self.title_font.render("DECLARE", True, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.subtitle_font.render("A Card Game of Memory & Strategy", True, TEXT_WHITE)
        subtitle_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(subtitle_surf, subtitle_rect)

        card_decor_y = 160
        for dx in [-180, -90, 90, 180]:
            rect = pygame.Rect(SCREEN_WIDTH // 2 + dx - CARD_WIDTH // 2, card_decor_y - CARD_HEIGHT // 2, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(self.screen, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
            pygame.draw.rect(self.screen, (20, 40, 80), rect, width=2, border_radius=CORNER_RADIUS)

        for button in self.buttons:
            button.draw(self.screen, self.button_font)

    def handle_event(self, event) -> str:
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons[0].is_clicked(event.pos, True):
                return "new_game"
            if self.buttons[1].is_clicked(event.pos, True):
                return "settings"
            if self.buttons[2].is_clicked(event.pos, True):
                return "quit"
        return None


class SetupScreen:
    def __init__(self, screen, num_players=2):
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.small_font = pygame.font.SysFont("segoeui", 20)
        self.num_players = num_players
        self.players_config = []
        for i in range(4):
            self.players_config.append({"name": f"Player {i + 1}", "is_human": i == 0})
        self.active_input = None
        self.player_count_buttons = []
        for idx, count in enumerate([2, 3, 4]):
            bx = SCREEN_WIDTH // 2 - 100 + idx * 100
            self.player_count_buttons.append(
                Button(bx, 180, 80, 40, str(count), (40, 100, 50), (60, 140, 70))
            )
        self.start_button = Button(SCREEN_WIDTH // 2, 620, 260, 54, "Start Game", (40, 100, 50), (60, 140, 70))
        self.back_button = Button(120, 680, 160, 44, "Back", (140, 40, 40), (180, 60, 60))
        self.toggle_buttons = []
        self.name_rects = []
        self._build_player_ui()

    def _build_player_ui(self):
        self.toggle_buttons = []
        self.name_rects = []
        for i in range(4):
            y = 250 + i * 80
            toggle = Button(800, y, 120, 36, "", (40, 100, 50), (60, 140, 70), font_size=20)
            self.toggle_buttons.append(toggle)
            name_rect = pygame.Rect(300, y - 18, 380, 36)
            self.name_rects.append(name_rect)

    def draw(self):
        self.screen.fill(BG_GREEN)

        title_surf = self.title_font.render("SETUP", True, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_surf, title_rect)

        label_surf = self.label_font.render("Number of Players:", True, TEXT_WHITE)
        self.screen.blit(label_surf, label_surf.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        for idx, btn in enumerate(self.player_count_buttons):
            count_val = [2, 3, 4][idx]
            if self.num_players == count_val:
                btn.color = GOLD
                btn.hover_color = (255, 230, 100)
                btn.text_color = TEXT_BLACK
            else:
                btn.color = (40, 100, 50)
                btn.hover_color = (60, 140, 70)
                btn.text_color = TEXT_WHITE
            btn.draw(self.screen, self.button_font)

        for i in range(self.num_players):
            y = 250 + i * 80
            config = self.players_config[i]
            label = self.label_font.render(f"Player {i + 1}:", True, TEXT_WHITE)
            self.screen.blit(label, (200, y - 12))

            name_rect = self.name_rects[i]
            border_color = HIGHLIGHT if self.active_input == i else DIM
            pygame.draw.rect(self.screen, CARD_WHITE, name_rect, border_radius=CORNER_RADIUS)
            pygame.draw.rect(self.screen, border_color, name_rect, width=2, border_radius=CORNER_RADIUS)
            name_surf = self.small_font.render(config["name"], True, TEXT_BLACK)
            self.screen.blit(name_surf, (name_rect.x + 8, name_rect.y + 7))

            toggle = self.toggle_buttons[i]
            toggle.text = "Human" if config["is_human"] else "AI"
            toggle.color = (50, 130, 60) if config["is_human"] else (80, 80, 160)
            toggle.hover_color = (70, 170, 80) if config["is_human"] else (110, 110, 200)
            toggle.rect.centery = y
            toggle.draw(self.screen, self.small_font)

        self.start_button.draw(self.screen, self.button_font)
        self.back_button.draw(self.screen, self.small_font)

    def handle_event(self, event) -> str:
        if event.type == pygame.MOUSEMOTION:
            for btn in self.player_count_buttons:
                btn.update_hover(event.pos)
            for btn in self.toggle_buttons[:self.num_players]:
                btn.update_hover(event.pos)
            self.start_button.update_hover(event.pos)
            self.back_button.update_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, btn in enumerate(self.player_count_buttons):
                if btn.is_clicked(event.pos, True):
                    self.num_players = [2, 3, 4][idx]
                    return None

            for i in range(self.num_players):
                toggle = self.toggle_buttons[i]
                toggle.rect.centery = 250 + i * 80
                if toggle.is_clicked(event.pos, True):
                    self.players_config[i]["is_human"] = not self.players_config[i]["is_human"]
                    return None

                name_rect = self.name_rects[i]
                if name_rect.collidepoint(event.pos):
                    self.active_input = i
                elif self.active_input == i:
                    self.active_input = None

            if self.start_button.is_clicked(event.pos, True):
                return "start_game"
            if self.back_button.is_clicked(event.pos, True):
                return "back"

        if event.type == pygame.KEYDOWN and self.active_input is not None:
            i = self.active_input
            if i < self.num_players:
                if event.key == pygame.K_BACKSPACE:
                    self.players_config[i]["name"] = self.players_config[i]["name"][:-1]
                elif event.key == pygame.K_RETURN:
                    self.active_input = None
                elif len(self.players_config[i]["name"]) < 20 and event.unicode.isprintable() and event.unicode != '':
                    self.players_config[i]["name"] += event.unicode
        return None


class PeekScreen:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.card_font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.peek_cards = []
        self.card_reveal_timer = 5.0
        self.elapsed = 0.0
        self.revealed = True
        self.done_button = Button(SCREEN_WIDTH // 2, 550, 300, 54, "I've memorized them!", (40, 100, 50), (60, 140, 70))

    def draw(self, game_manager):
        self.screen.fill(BG_GREEN)

        title_surf = self.title_font.render("PEEK PHASE", True, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_surf, title_rect)

        if game_manager is None:
            return

        human = None
        for p in game_manager.players:
            if p.is_human:
                human = p
                break

        if human is None:
            return

        subtitle = self.label_font.render("Memorize your bottom 2 cards!", True, TEXT_WHITE)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        timer_text = self.label_font.render(f"Time remaining: {max(0, self.card_reveal_timer - self.elapsed):.1f}s", True, TEXT_WHITE)
        self.screen.blit(timer_text, timer_text.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        all_cards = human.hand
        start_x = SCREEN_WIDTH // 2 - (HAND_SIZE * (CARD_WIDTH + CARD_SPREAD)) // 2 + CARD_SPREAD
        for slot_idx in range(HAND_SIZE):
            card_x = start_x + slot_idx * (CARD_WIDTH + CARD_SPREAD)
            card_y = 300
            card = all_cards[slot_idx]
            if card is None:
                continue
            is_peek_slot = slot_idx in (2, 3) and self.revealed
            if is_peek_slot:
                self._draw_card_face(card_x, card_y, card)
            else:
                self._draw_card_back(card_x, card_y)

            label = self.label_font.render(f"Slot {slot_idx + 1}", True, TEXT_WHITE)
            self.screen.blit(label, label.get_rect(center=(card_x + CARD_WIDTH // 2, card_y + CARD_HEIGHT + 20)))

        self.done_button.draw(self.screen, self.button_font)

    def _draw_card_face(self, x, y, card):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        self.screen.blit(rank_surf, (x + 6, y + 4))
        sym_surf = self.card_font.render(card.suit_symbol, True, color)
        self.screen.blit(sym_surf, (x + 6, y + 22))
        center_surf = self.card_font.render(card.display_name, True, color)
        center_rect = center_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        self.screen.blit(center_surf, center_rect)

    def _draw_card_back(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_BACK_BLUE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, (20, 40, 80), rect, width=2, border_radius=CORNER_RADIUS)
        inner = pygame.Rect(x + 8, y + 8, CARD_WIDTH - 16, CARD_HEIGHT - 16)
        pygame.draw.rect(self.screen, (40, 80, 160), inner, border_radius=4)

    def handle_event(self, event) -> str:
        if event.type == pygame.MOUSEMOTION:
            self.done_button.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.done_button.is_clicked(event.pos, True):
                self.revealed = False
                return "peek_done"
        return None

    def update(self, dt):
        if self.revealed:
            self.elapsed += dt
            if self.elapsed >= self.card_reveal_timer:
                self.revealed = False
                return "peek_done"
        return None


class GameOverScreen:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("segoeui", TITLE_FONT_SIZE, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.button_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.card_font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", LOG_FONT_SIZE)
        self.play_again_button = Button(SCREEN_WIDTH // 2 - 140, 650, 240, 50, "Play Again", (40, 100, 50), (60, 140, 70))
        self.menu_button = Button(SCREEN_WIDTH // 2 + 140, 650, 240, 50, "Main Menu", (140, 40, 40), (180, 60, 60))

    def draw(self, game_manager, result: dict):
        self.screen.fill(BG_GREEN)

        title_surf = self.title_font.render("GAME OVER", True, GOLD)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        self.screen.blit(title_surf, title_rect)

        if result and result.get("winner"):
            winner = result["winner"]
            winner_text = f"{winner.name} wins!"
            winner_surf = self.label_font.render(winner_text, True, GOLD)
            self.screen.blit(winner_surf, winner_surf.get_rect(center=(SCREEN_WIDTH // 2, 110)))
        elif result and result.get("declarer_won") is False:
            declarer_lost_surf = self.label_font.render("The declarer lost!", True, RED)
            self.screen.blit(declarer_lost_surf, declarer_lost_surf.get_rect(center=(SCREEN_WIDTH // 2, 110)))
        else:
            draw_surf = self.label_font.render("It's a draw!", True, TEXT_WHITE)
            self.screen.blit(draw_surf, draw_surf.get_rect(center=(SCREEN_WIDTH // 2, 110)))

        if game_manager is None:
            return

        num_players = len(game_manager.players)
        scores = result.get("scores", {}) if result else {}

        total_width = SCREEN_WIDTH
        section_width = total_width // num_players

        for i, player in enumerate(game_manager.players):
            px = section_width * i + section_width // 2
            py = 160

            name_surf = self.label_font.render(player.name, True, TEXT_WHITE)
            self.screen.blit(name_surf, name_surf.get_rect(center=(px, py)))

            score_val = scores.get(player.seat_index, 0)
            score_surf = self.small_font.render(f"Score: {score_val}", True, GOLD)
            self.screen.blit(score_surf, score_surf.get_rect(center=(px, py + 30)))

            card_start_x = px - (HAND_SIZE * (CARD_WIDTH + CARD_SPREAD - 10)) // 2
            for slot_idx in range(HAND_SIZE):
                card = player.hand[slot_idx]
                cx = card_start_x + slot_idx * (CARD_WIDTH + CARD_SPREAD - 10)
                cy = py + 60
                if card is not None:
                    self._draw_card_face(cx, cy, card)
                else:
                    self._draw_empty_slot(cx, cy)

        self.play_again_button.draw(self.screen, self.button_font)
        self.menu_button.draw(self.screen, self.button_font)

    def _draw_card_face(self, x, y, card):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, CARD_WHITE, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, BLACK, rect, width=2, border_radius=CORNER_RADIUS)
        color = RED if card.is_red else BLACK
        rank_surf = self.card_font.render(card.rank, True, color)
        self.screen.blit(rank_surf, (x + 6, y + 4))
        sym_surf = self.card_font.render(card.suit_symbol, True, color)
        self.screen.blit(sym_surf, (x + 6, y + 22))
        center_surf = self.card_font.render(card.display_name, True, color)
        center_rect = center_surf.get_rect(center=(x + CARD_WIDTH // 2, y + CARD_HEIGHT // 2))
        self.screen.blit(center_surf, center_rect)

    def _draw_empty_slot(self, x, y):
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        pygame.draw.rect(self.screen, DIM, rect, border_radius=CORNER_RADIUS)
        pygame.draw.rect(self.screen, BLACK, rect, width=1, border_radius=CORNER_RADIUS)

    def handle_event(self, event) -> str:
        if event.type == pygame.MOUSEMOTION:
            self.play_again_button.update_hover(event.pos)
            self.menu_button.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_again_button.is_clicked(event.pos, True):
                return "play_again"
            if self.menu_button.is_clicked(event.pos, True):
                return "menu"
        return None