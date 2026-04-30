import pygame
import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BG_DARK, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM,
    CARD_WHITE, BLACK, RED, GOLD, GOLD_HOVER, GOLD_DIM, TEXT_WHITE, TEXT_BLACK,
    TEXT_DIM, TEXT_DIMMER, PANEL_BG, PANEL_BORDER, PANEL_BORDER_GOLD,
    STATUS_BAR_H, CARD_WIDTH, CARD_HEIGHT, CORNER_RADIUS,
    UI_FONT_SIZE, SMALL_FONT_SIZE,
    DEFAULT_AI_DELAY, DEFAULT_PEEK_REVEAL_TIME, DEFAULT_PEEK_PHASE_SECONDS,
    DEFAULT_ANIMATIONS_ENABLED, DEFAULT_SHOW_OWN_SCORE, DEFAULT_SHOW_KNOWN_MARKER,
    DEFAULT_SHOW_GAME_LOG, DEFAULT_CONFIRM_DECLARE, DEFAULT_LAYOUT_MODE, DEFAULT_FELT,
    AI_DELAY_OPTIONS, AI_DELAY_LABELS, PEEK_REVEAL_OPTIONS, PEEK_REVEAL_LABELS,
    ANIMATION_OPTIONS, ANIMATION_LABELS, LAYOUT_OPTIONS, LAYOUT_LABELS,
    AI_DIFFICULTY_OPTIONS, AI_DIFFICULTY_LABELS, PEEK_PHASE_OPTIONS, PEEK_PHASE_LABELS,
    FELT_COLORS, FELT_LABELS, FELT_COLORS_LIGHT,
    SWAP_GREEN, SWAP_GREEN_HOVER, PEEK_BLUE, PEEK_BLUE_HOVER,
    DECLARE_RED, DECLARE_RED_HOVER, CANCEL_GRAY, CANCEL_GRAY_HOVER,
)
from ui.widgets import Button, ToggleButton


class SettingsMenu:
    PANEL_W = 620
    PANEL_H = 600
    PANEL_X = (SCREEN_WIDTH - PANEL_W) // 2
    PANEL_Y = (SCREEN_HEIGHT - PANEL_H) // 2
    GEAR_X = SCREEN_WIDTH - 52
    GEAR_Y = 8
    GEAR_W = 40
    GEAR_H = 34

    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("georgia", 28, bold=True)
        self.font = pygame.font.SysFont("segoeui", UI_FONT_SIZE)
        self.small_font = pygame.font.SysFont("segoeui", SMALL_FONT_SIZE)
        self.section_font = pygame.font.SysFont("segoeui", UI_FONT_SIZE - 2, bold=True)
        self._hovered = None
        self._controls = []
        self._all_buttons = []
        self._time = 0.0
        self._build_controls()

    def _build_controls(self):
        self._controls = []
        self._all_buttons = []
        sx = self.PANEL_X + 24
        sy = self.PANEL_Y + 56
        line_h = 36
        btn_h = 30

        self._controls.append({
            'type': 'section', 'text': 'CARD LAYOUT',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        for i, (mode, label) in enumerate(zip(LAYOUT_OPTIONS, LAYOUT_LABELS)):
            bx = sx + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, label, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'layout_btn', 'value': mode, 'label': label,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 8

        self._controls.append({
            'type': 'section', 'text': 'TABLE FELT',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        for i, (key, label) in enumerate(zip(FELT_COLORS.keys(), FELT_LABELS)):
            bx = sx + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, label, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'felt_btn', 'value': key, 'label': label,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 8

        self._controls.append({
            'type': 'section', 'text': 'GAME SPEED',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        self._controls.append({
            'type': 'label', 'text': 'AI Delay:',
            'rect': pygame.Rect(sx, sy + 5, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(AI_DELAY_OPTIONS, AI_DELAY_LABELS)):
            bx = sx + 95 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'ai_delay_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Peek Reveal:',
            'rect': pygame.Rect(sx, sy + 5, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(PEEK_REVEAL_OPTIONS, PEEK_REVEAL_LABELS)):
            bx = sx + 95 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'peek_reveal_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Animations:',
            'rect': pygame.Rect(sx, sy + 5, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(ANIMATION_OPTIONS, ANIMATION_LABELS)):
            bx = sx + 95 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'anim_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 8

        self._controls.append({
            'type': 'section', 'text': 'AI DIFFICULTY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        self._controls.append({
            'type': 'label', 'text': 'Note: affects declare threshold',
            'rect': pygame.Rect(sx, sy + 5, 400, 20)
        })
        sy += line_h
        for i, (val, lbl) in enumerate(zip(AI_DIFFICULTY_OPTIONS, AI_DIFFICULTY_LABELS)):
            bx = sx + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'ai_diff_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 8

        self._controls.append({
            'type': 'section', 'text': 'DISPLAY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        self._controls.append({
            'type': 'label', 'text': 'Show Own Score:',
            'rect': pygame.Rect(sx, sy + 5, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'score_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Known Markers:',
            'rect': pygame.Rect(sx, sy + 5, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'marker_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Game Log:',
            'rect': pygame.Rect(sx, sy + 5, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'log_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 8

        self._controls.append({
            'type': 'section', 'text': 'GAMEPLAY',
            'rect': pygame.Rect(sx, sy, 200, 20)
        })
        sy += 28
        self._controls.append({
            'type': 'label', 'text': 'Confirm Declare:',
            'rect': pygame.Rect(sx, sy + 5, 130, 20)
        })
        for i, (val, lbl) in enumerate(zip([True, False], ['ON', 'OFF'])):
            bx = sx + 140 + i * 110
            btn = Button(bx + 50, sy + btn_h // 2, 100, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'confirm_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h
        self._controls.append({
            'type': 'label', 'text': 'Peek Phase:',
            'rect': pygame.Rect(sx, sy + 5, 90, 20)
        })
        for i, (val, lbl) in enumerate(zip(PEEK_PHASE_OPTIONS, PEEK_PHASE_LABELS)):
            bx = sx + 95 + i * 90
            btn = Button(bx + 40, sy + btn_h // 2, 80, btn_h, lbl, 'secondary', font=self.small_font)
            self._controls.append({
                'type': 'peek_phase_btn', 'value': val, 'label': lbl,
                'rect': btn.rect, 'btn': btn
            })
            self._all_buttons.append(btn)
        sy += line_h + 16

        done_rect = pygame.Rect(
            self.PANEL_X + self.PANEL_W // 2 - 80,
            sy, 160, 42
        )
        self.done_button = Button(self.PANEL_X + self.PANEL_W // 2, sy + 21, 160, 42, "Done", 'gold', font=self.font, glow=True)
        self._controls.append({
            'type': 'done_btn', 'rect': done_rect
        })
        self._all_buttons.append(self.done_button)

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
            if self.done_button.contains(event.pos):
                self.done_button.on_press()
                return 'close'
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
                    elif ctype == 'felt_btn':
                        game_settings.felt_style = ctrl['value']
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
                    if 'btn' in ctrl:
                        ctrl['btn'].on_press()
                    return 'updated'
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for btn in self._all_buttons:
                btn.on_release()
        return None

    def _get_human_index(self, gm):
        for i, p in enumerate(gm.players):
            if p.is_human:
                return i
        return None

    def _draw_section_icon(self, icon_type, cx, cy, color):
        if icon_type == 'cards':
            for i in range(3):
                x = cx - 8 + i * 7
                pygame.draw.rect(self.screen, color, (x, cy - 4, 5, 8), border_radius=1)
        elif icon_type == 'speed':
            pygame.draw.circle(self.screen, color, (cx, cy), 7, 1)
            pygame.draw.line(self.screen, color, (cx, cy), (cx + 5, cy - 5), 2)
            pygame.draw.circle(self.screen, color, (cx, cy), 2)
        elif icon_type == 'target':
            pygame.draw.circle(self.screen, color, (cx, cy), 8, 1)
            pygame.draw.circle(self.screen, color, (cx, cy), 5, 1)
            pygame.draw.circle(self.screen, color, (cx, cy), 2)
        elif icon_type == 'eye':
            pygame.draw.ellipse(self.screen, color, (cx - 9, cy - 5, 18, 10), 1)
            pygame.draw.circle(self.screen, color, (cx, cy), 2)
        elif icon_type == 'play':
            pts = [(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 7, cy)]
            pygame.draw.polygon(self.screen, color, pts)
        elif icon_type == 'felt':
            pygame.draw.ellipse(self.screen, color, (cx - 9, cy - 5, 18, 10), 1)
            pygame.draw.ellipse(self.screen, color, (cx - 5, cy - 3, 10, 6), 1)

    def draw(self, game_settings, game_manager, mouse_pos):
        self._time += 0.016
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H)

        panel_shadow = pygame.Surface((self.PANEL_W + 12, self.PANEL_H + 12), pygame.SRCALPHA)
        pygame.draw.rect(panel_shadow, (0, 0, 0, 120), (6, 8, self.PANEL_W, self.PANEL_H), border_radius=14)
        self.screen.blit(panel_shadow, (self.PANEL_X - 6, self.PANEL_Y + 6))

        panel_surf = pygame.Surface((self.PANEL_W, self.PANEL_H), pygame.SRCALPHA)
        for y in range(self.PANEL_H):
            t = y / self.PANEL_H
            r = int(BG_GRADIENT_TOP[0] + (BG_GRADIENT_BOTTOM[0] - BG_GRADIENT_TOP[0]) * t)
            g = int(BG_GRADIENT_TOP[1] + (BG_GRADIENT_BOTTOM[1] - BG_GRADIENT_TOP[1]) * t)
            b = int(BG_GRADIENT_TOP[2] + (BG_GRADIENT_BOTTOM[2] - BG_GRADIENT_TOP[2]) * t)
            for x in range(self.PANEL_W):
                panel_surf.set_at((x, y), (r, g, b, 248))
        self.screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(self.screen, (*GOLD, 150), panel_rect, 2, border_radius=12)

        title_surf = self.title_font.render("SETTINGS", True, GOLD)
        shadow_surf = self.title_font.render("SETTINGS", True, (40, 25, 5))
        title_rect = title_surf.get_rect(center=(self.PANEL_X + self.PANEL_W // 2 + 2, self.PANEL_Y + 34))
        self.screen.blit(shadow_surf, title_rect)
        title_rect2 = title_surf.get_rect(center=(self.PANEL_X + self.PANEL_W // 2, self.PANEL_Y + 32))
        self.screen.blit(title_surf, title_rect2)
        pygame.draw.line(self.screen, (*GOLD_DIM, 100),
                         (self.PANEL_X + 30, self.PANEL_Y + 48),
                         (self.PANEL_X + self.PANEL_W - 30, self.PANEL_Y + 48), 1)

        SECTION_ICONS = {
            'CARD LAYOUT': 'cards',
            'TABLE FELT': 'felt',
            'GAME SPEED': 'speed',
            'AI DIFFICULTY': 'target',
            'DISPLAY': 'eye',
            'GAMEPLAY': 'play',
        }

        for ctrl in self._controls:
            rect = ctrl['rect']
            ctype = ctrl['type']

            if ctype == 'section':
                icon_type = SECTION_ICONS.get(ctrl['text'], '')
                self._draw_section_icon(icon_type, rect.x + 10, rect.y + 9, GOLD_DIM)
                text_surf = self.section_font.render(ctrl['text'], True, GOLD)
                self.screen.blit(text_surf, (rect.x + 28, rect.y))
                pygame.draw.line(self.screen, (*PANEL_BORDER, 120), (rect.x, rect.y + 20),
                                (self.PANEL_X + self.PANEL_W - 24, rect.y + 20), 1)

            elif ctype == 'label':
                lbl_surf = self.small_font.render(ctrl['text'], True, TEXT_DIM)
                self.screen.blit(lbl_surf, (rect.x, rect.y))

            elif ctype in ('layout_btn', 'felt_btn', 'ai_delay_btn', 'peek_reveal_btn', 'anim_btn',
                          'ai_diff_btn', 'score_btn', 'marker_btn', 'log_btn',
                          'confirm_btn', 'peek_phase_btn'):
                active = False
                if ctype == 'layout_btn':
                    active = (game_settings.layout_mode == ctrl['value'])
                elif ctype == 'felt_btn':
                    active = (game_settings.felt_style == ctrl['value'])
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

                btn = ctrl.get('btn')
                if btn:
                    if active:
                        btn.variant = 'gold'
                        btn.base_color = GOLD
                        btn.hover_color = GOLD_HOVER
                        btn.text_color = BG_DARK
                    else:
                        btn.variant = 'secondary'
                        btn.base_color = (55, 55, 60)
                        btn.hover_color = (75, 75, 80)
                        btn.text_color = TEXT_WHITE
                    btn.update(0.016, mouse_pos)
                    btn.draw(self.screen)

                if ctype == 'felt_btn':
                    swatch_color = FELT_COLORS.get(ctrl['value'], (50, 50, 50))
                    swatch_rect = pygame.Rect(rect.right + 8, rect.centery - 7, 14, 14)
                    pygame.draw.rect(self.screen, swatch_color, swatch_rect, border_radius=4)
                    pygame.draw.rect(self.screen, (*GOLD_DIM, 150), swatch_rect, 1, border_radius=4)

            elif ctype == 'done_btn':
                self.done_button.update(0.016, mouse_pos)
                self.done_button.draw(self.screen)

        self._hit_test(mouse_pos)

    def get_gear_rect(self):
        return pygame.Rect(self.GEAR_X, self.GEAR_Y, self.GEAR_W, self.GEAR_H)

    def draw_gear_icon(self, mouse_pos, settings_open=False):
        rect = self.get_gear_rect()
        cx, cy = rect.centerx, rect.centry
        hovered = rect.collidepoint(mouse_pos) and not settings_open
        color = GOLD if hovered or settings_open else TEXT_DIM
        radius = 10
        teeth = 8
        pts = []
        for i in range(teeth * 2):
            angle = math.pi * 2 * i / (teeth * 2) - math.pi / 2
            r = radius + 5 if i % 2 == 0 else radius
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if len(pts) > 2:
            pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.circle(self.screen, BG_DARK, (cx, cy), 4)
        pygame.draw.circle(self.screen, color, (cx, cy), 4, 1)
        return rect
