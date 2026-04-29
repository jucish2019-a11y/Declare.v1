import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_GREEN, BG_DARK, CARD_WHITE, BLACK, RED,
    GOLD, TEXT_WHITE, TEXT_BLACK, TEXT_DIM, PANEL_BG, PANEL_BORDER,
    STATUS_BAR_H, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS,
    UI_FONT_SIZE, SMALL_FONT_SIZE,
    DEFAULT_AI_DELAY, DEFAULT_PEEK_REVEAL_TIME, DEFAULT_PEEK_PHASE_SECONDS,
    DEFAULT_ANIMATIONS_ENABLED, DEFAULT_SHOW_OWN_SCORE, DEFAULT_SHOW_KNOWN_MARKER,
    DEFAULT_SHOW_GAME_LOG, DEFAULT_CONFIRM_DECLARE, DEFAULT_LAYOUT_MODE,
    AI_DELAY_OPTIONS, AI_DELAY_LABELS, PEEK_REVEAL_OPTIONS, PEEK_REVEAL_LABELS,
    ANIMATION_OPTIONS, ANIMATION_LABELS, LAYOUT_OPTIONS, LAYOUT_LABELS,
    AI_DIFFICULTY_OPTIONS, AI_DIFFICULTY_LABELS, PEEK_PHASE_OPTIONS, PEEK_PHASE_LABELS,
)


class SettingsMenu:
    PANEL_W = 600
    PANEL_H = 580
    PANEL_X = (SCREEN_WIDTH - PANEL_W) // 2
    PANEL_Y = (SCREEN_HEIGHT - PANEL_H) // 2
    GEAR_X = SCREEN_WIDTH - 52
    GEAR_Y = 8
    GEAR_W = 40
    GEAR_H = 34

    SOFT_AMBER = (220, 170, 50)
    SOFT_AMBER_HOVER = (240, 190, 60)

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("arial", UI_FONT_SIZE)
        self.small_font = pygame.font.SysFont("arial", SMALL_FONT_SIZE)
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        self.section_font = pygame.font.SysFont("arial", UI_FONT_SIZE - 2, bold=True)
        self._hovered = None
        self._controls = []
        self._build_controls()

    def _build_controls(self):
        self._controls = []
        sx = self.PANEL_X + 20
        sy = self.PANEL_Y + 52
        line_h = 34
        btn_h = 28

        self._controls.append({
            'type': 'section', 'text': 'CARD LAYOUT',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 26
        for i, (mode, label) in enumerate(zip(LAYOUT_OPTIONS, LAYOUT_LABELS)):
            bx = sx + i * 105
            self._controls.append({
                'type': 'layout_btn', 'value': mode, 'label': label,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h + 12

        self._controls.append({
            'type': 'section', 'text': 'GAME SPEED',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 26
        self._controls.append({
            'type': 'label', 'text': 'AI Delay:',
            'rect': pygame.Rect(sx, sy + 4, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(AI_DELAY_OPTIONS, AI_DELAY_LABELS)):
            bx = sx + 95 + i * 105
            self._controls.append({
                'type': 'ai_delay_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Peek Reveal:',
            'rect': pygame.Rect(sx, sy + 4, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(PEEK_REVEAL_OPTIONS, PEEK_REVEAL_LABELS)):
            bx = sx + 95 + i * 105
            self._controls.append({
                'type': 'peek_reveal_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Animations:',
            'rect': pygame.Rect(sx, sy + 4, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(ANIMATION_OPTIONS, ANIMATION_LABELS)):
            bx = sx + 95 + i * 105
            self._controls.append({
                'type': 'anim_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h + 12

        self._controls.append({
            'type': 'section', 'text': 'AI DIFFICULTY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 26
        self._controls.append({
            'type': 'label', 'text': 'Note: difficulty affects declare threshold',
            'rect': pygame.Rect(sx, sy + 4, 400, 20)
        })
        sy += line_h
        for i, (val, lbl) in enumerate(zip(AI_DIFFICULTY_OPTIONS, AI_DIFFICULTY_LABELS)):
            bx = sx + i * 105
            self._controls.append({
                'type': 'ai_diff_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h + 12

        self._controls.append({
            'type': 'section', 'text': 'DISPLAY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 26
        self._controls.append({
            'type': 'label', 'text': 'Show Own Score:',
            'rect': pygame.Rect(sx, sy + 4, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 105
            self._controls.append({
                'type': 'score_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Known Markers:',
            'rect': pygame.Rect(sx, sy + 4, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 105
            self._controls.append({
                'type': 'marker_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Game Log:',
            'rect': pygame.Rect(sx, sy + 4, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 105
            self._controls.append({
                'type': 'log_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h + 12

        self._controls.append({
            'type': 'section', 'text': 'GAMEPLAY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 26
        self._controls.append({
            'type': 'label', 'text': 'Confirm Declare:',
            'rect': pygame.Rect(sx, sy + 4, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 105
            self._controls.append({
                'type': 'confirm_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 100, btn_h)
            })
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Peek Phase:',
            'rect': pygame.Rect(sx, sy + 4, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(PEEK_PHASE_OPTIONS, PEEK_PHASE_LABELS)):
            bx = sx + 95 + i * 85
            self._controls.append({
                'type': 'peek_phase_btn', 'value': val, 'label': lbl,
                'rect': pygame.Rect(bx, sy, 80, btn_h)
            })
        sy += line_h + 14

        done_rect = pygame.Rect(
            self.PANEL_X + self.PANEL_W // 2 - 70,
            sy, 140, 38
        )
        self._controls.append({
            'type': 'done_btn', 'rect': done_rect
        })

    def _draw_rounded_rect(self, surface, color, rect, radius):
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def _hit_test(self, mouse_pos):
        self._hovered = None
        for ctrl in self._controls:
            if ctrl['rect'].collidepoint(mouse_pos):
                self._hovered = ctrl
                return ctrl
        return None

    def handle_event(self, event, game_settings, game_manager):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for ctrl in self._controls:
                if ctrl['rect'].collidepoint(mouse_pos):
                    ctype = ctrl['type']
                    if ctype == 'done_btn':
                        return 'close'
                    elif ctype == 'layout_btn':
                        game_settings.layout_mode = ctrl['value']
                        if game_manager and ctrl['value'] == 'free':
                            human_idx = self._get_human_index(game_manager)
                            if human_idx is not None:
                                hp = game_manager.players[human_idx]
                                hp.layout_mode = 'free'
                                from ui.renderer import Renderer
                                r = Renderer(self.screen)
                                r.init_free_positions(hp, game_manager)
                    elif ctype == 'ai_delay_btn':
                        game_settings.ai_delay = ctrl['value']
                    elif ctype == 'peek_reveal_btn':
                        game_settings.peek_reveal_time = ctrl['value']
                    elif ctype == 'anim_btn':
                        game_settings.animations_enabled = ctrl['value']
                    elif ctype == 'ai_diff_btn':
                        if game_manager:
                            for p in game_manager.players:
                                if not p.is_human:
                                    game_settings.ai_difficulties[p.seat_index] = ctrl['value']
                    elif ctype == 'score_btn':
                        game_settings.show_own_score = ctrl['value']
                    elif ctype == 'marker_btn':
                        game_settings.show_known_marker = ctrl['value']
                    elif ctype == 'log_btn':
                        game_settings.show_game_log = ctrl['value']
                    elif ctype == 'confirm_btn':
                        game_settings.confirm_declare = ctrl['value']
                    elif ctype == 'peek_phase_btn':
                        game_settings.peek_phase_seconds = ctrl['value']
                    return 'updated'
        return None

    def _get_human_index(self, gm):
        for i, p in enumerate(gm.players):
            if p.is_human:
                return i
        return None

    def draw(self, game_settings, game_manager, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H)

        panel_shadow = pygame.Surface((self.PANEL_W + 8, self.PANEL_H + 8), pygame.SRCALPHA)
        pygame.draw.rect(panel_shadow, (0, 0, 0, 100), (4, 6, self.PANEL_W, self.PANEL_H), border_radius=12)
        self.screen.blit(panel_shadow, (self.PANEL_X - 4, self.PANEL_Y + 4))

        panel_surf = pygame.Surface((self.PANEL_W, self.PANEL_H), pygame.SRCALPHA)
        panel_surf.fill((*PANEL_BG, 248))
        self.screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 2, border_radius=10)

        title_surf = self.title_font.render("Settings", True, GOLD)
        shadow_surf = self.title_font.render("Settings", True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(self.PANEL_X + self.PANEL_W // 2 + 1, self.PANEL_Y + 33))
        self.screen.blit(shadow_surf, title_rect)
        title_rect2 = title_surf.get_rect(center=(self.PANEL_X + self.PANEL_W // 2, self.PANEL_Y + 32))
        self.screen.blit(title_surf, title_rect2)

        SECTION_ICONS = {
            'CARD LAYOUT': '\u25a6',
            'GAME SPEED': '\u231a',
            'AI DIFFICULTY': '\u2699',
            'DISPLAY': '\u25ce',
            'GAMEPLAY': '\u2694',
        }

        for ctrl in self._controls:
            rect = ctrl['rect']
            ctype = ctrl['type']

            if ctype == 'section':
                icon = SECTION_ICONS.get(ctrl['text'], '')
                icon_surf = self.section_font.render(icon, True, GOLD)
                self.screen.blit(icon_surf, (rect.x, rect.y))
                text_surf = self.section_font.render(ctrl['text'], True, GOLD)
                self.screen.blit(text_surf, (rect.x + 18, rect.y))
                pygame.draw.line(self.screen, PANEL_BORDER, (rect.x, rect.y + 18),
                                (self.PANEL_X + self.PANEL_W - 20, rect.y + 18), 1)

            elif ctype == 'label':
                lbl_surf = self.small_font.render(ctrl['text'], True, TEXT_DIM)
                self.screen.blit(lbl_surf, (rect.x, rect.y))

            elif ctype in ('layout_btn', 'ai_delay_btn', 'peek_reveal_btn', 'anim_btn',
                          'ai_diff_btn', 'score_btn', 'marker_btn', 'log_btn',
                          'confirm_btn', 'peek_phase_btn'):
                active = False
                if ctype == 'layout_btn':
                    active = (game_settings.layout_mode == ctrl['value'])
                elif ctype == 'ai_delay_btn':
                    active = abs(game_settings.ai_delay - ctrl['value']) < 0.05
                elif ctype == 'peek_reveal_btn':
                    active = abs(game_settings.peek_reveal_time - ctrl['value']) < 0.05
                elif ctype == 'anim_btn':
                    active = (game_settings.animations_enabled == ctrl['value'])
                elif ctype == 'ai_diff_btn':
                    if game_manager:
                        diff_val = game_settings.ai_difficulties.get(
                            game_manager.players[0].seat_index if game_manager.players else 0, 'medium')
                        active = (diff_val == ctrl['value'])
                elif ctype in ('score_btn', 'marker_btn', 'log_btn', 'confirm_btn'):
                    attr_map = {'score_btn': 'show_own_score', 'marker_btn': 'show_known_marker',
                                'log_btn': 'show_game_log', 'confirm_btn': 'confirm_declare'}
                    active = (getattr(game_settings, attr_map.get(ctype, ''), False) == ctrl['value'])
                elif ctype == 'peek_phase_btn':
                    active = abs(game_settings.peek_phase_seconds - ctrl['value']) < 0.05

                hovered = (self._hovered is ctrl)
                active_color = self.SOFT_AMBER if active else ((120, 120, 120) if hovered else (70, 70, 70))
                txt_color = BG_DARK if active else (TEXT_WHITE if hovered else TEXT_DIM)

                shadow_s = pygame.Surface((rect.width + 3, rect.height + 3), pygame.SRCALPHA)
                pygame.draw.rect(shadow_s, (0, 0, 0, 50), (1, 2, rect.width, rect.height), border_radius=5)
                self.screen.blit(shadow_s, (rect.x - 1, rect.y + 2))

                self._draw_rounded_rect(self.screen, active_color, rect, 5)

                c_r = max(active_color[0] - 35, 0)
                c_g = max(active_color[1] - 35, 0)
                c_b = max(active_color[2] - 35, 0)
                pygame.draw.line(self.screen, (c_r, c_g, c_b),
                                (rect.left + 2, rect.bottom - 2), (rect.right - 2, rect.bottom - 2), 2)
                pygame.draw.line(self.screen, (c_r, c_g, c_b),
                                (rect.right - 2, rect.top + 2), (rect.right - 2, rect.bottom - 2), 2)
                l_r = min(active_color[0] + 45, 255)
                l_g = min(active_color[1] + 45, 255)
                l_b = min(active_color[2] + 45, 255)
                pygame.draw.line(self.screen, (l_r, l_g, l_b),
                                (rect.left + 2, rect.top + 2), (rect.right - 2, rect.top + 2), 2)
                pygame.draw.line(self.screen, (l_r, l_g, l_b),
                                (rect.left + 2, rect.top + 2), (rect.left + 2, rect.bottom - 2), 2)

                lbl_surf = self.small_font.render(ctrl['label'], True, txt_color)
                lbl_rect = lbl_surf.get_rect(center=rect.center)
                self.screen.blit(lbl_surf, lbl_rect)

            elif ctype == 'done_btn':
                hovered = rect.collidepoint(mouse_pos)
                bg_color = (20, 20, 20) if hovered else (15, 15, 15)

                shadow_s = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
                pygame.draw.rect(shadow_s, (0, 0, 0, 60), (2, 3, rect.width, rect.height), border_radius=8)
                self.screen.blit(shadow_s, (rect.x - 2, rect.y + 3))

                self._draw_rounded_rect(self.screen, bg_color, rect, 8)
                pygame.draw.rect(self.screen, GOLD, rect, 1, border_radius=8)

                l_r = min(GOLD[0] + 30, 255)
                l_g = min(GOLD[1] + 30, 255)
                l_b = min(GOLD[2] + 30, 255)
                pygame.draw.line(self.screen, (l_r, l_g, l_b),
                                (rect.left + 3, rect.top + 3), (rect.right - 3, rect.top + 3), 1)
                pygame.draw.line(self.screen, (l_r, l_g, l_b),
                                (rect.left + 3, rect.top + 3), (rect.left + 3, rect.bottom - 3), 1)

                done_surf = self.font.render("Done", True, GOLD)
                done_rect = done_surf.get_rect(center=rect.center)
                self.screen.blit(done_surf, done_rect)

        self._hit_test(mouse_pos)

    def get_gear_rect(self):
        return pygame.Rect(self.GEAR_X, self.GEAR_Y, self.GEAR_W, self.GEAR_H)

    def draw_gear_icon(self, mouse_pos, settings_open=False):
        rect = self.get_gear_rect()
        hovered = rect.collidepoint(mouse_pos) and not settings_open
        bg_col = (20, 20, 15) if hovered else (12, 12, 10)
        border_col = GOLD if hovered else (80, 70, 30)
        gear_col = GOLD if hovered else (180, 150, 50)
        bg_rect = pygame.Rect(rect.x - 4, rect.y - 4, rect.width + 8, rect.height + 8)
        self._draw_rounded_rect(self.screen, bg_col, bg_rect, 6)
        pygame.draw.rect(self.screen, border_col, bg_rect, 1, border_radius=6)
        gear_surf = self.font.render('\u2699', True, gear_col)
        gear_rect = gear_surf.get_rect(center=rect.center)
        self.screen.blit(gear_surf, gear_rect)
        return rect