# my_safari_project/view/gamegui.py
from __future__ import annotations

import sys
from typing import List

import pygame
from pygame.math import Vector2

from my_safari_project.view.boardgui import BoardGUI
from my_safari_project.control.game_controller import (
    GameController,
    RANGER_COST, PLANT_COST, POND_COST,
    HYENA_COST, LION_COST, TIGER_COST,
    BUFFALO_COST, ELEPHANT_COST, GIRAFFE_COST, HIPPO_COST, ZEBRA_COST
)

# ────────────────────────────── layout constants ──────────────────────────────
SCREEN_W, SCREEN_H = 1080, 720
SIDE_PANEL_W       = 320
TOP_BAR_H          = 60
BOTTOM_BAR_H       = 80

BOARD_RECT = pygame.Rect(
    0, TOP_BAR_H,
    SCREEN_W - SIDE_PANEL_W,
    SCREEN_H - TOP_BAR_H - BOTTOM_BAR_H
)

ZOOM_BTN_SZ = 32        # size of the + / – buttons
SPEED_LEVELS = [1, 4, 8] #index 0 for 1x, index 1 for 4x, index 2 for 8x speed levels => logical speeds for buttons 1x,2x,3x
# ────────────────────────────────── GameGUI ───────────────────────────────────
class GameGUI:
    """UI layer.  Relies on an external GameController for model updates."""

    # ─────────────────────────────── lifecycle ────────────────────────────────
    def __init__(self, control: GameController):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        self.control: GameController = control
        self.board_gui = BoardGUI(self.control.board)

        # fonts
        self.font_small  = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large  = pygame.font.SysFont("Verdana", 28, bold=True)

        # zoom buttons (their pos is set every frame)
        self.btn_zoom_in  = pygame.Rect(0, 0, ZOOM_BTN_SZ, ZOOM_BTN_SZ)
        self.btn_zoom_out = pygame.Rect(0, 0, ZOOM_BTN_SZ, ZOOM_BTN_SZ)

        # shop / feedback
        self.feedback       = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0
        self.shop_items: List[dict] = [
            {"name": "Ranger",   "cost": RANGER_COST},
            {"name": "Plant",    "cost": PLANT_COST},
            {"name": "Pond",     "cost": POND_COST},
            {"name": "Hyena",    "cost": HYENA_COST},
            {"name": "Lion",     "cost": LION_COST},
            {"name": "Tiger",    "cost": TIGER_COST},
            {"name": "Buffalo",  "cost": BUFFALO_COST},
            {"name": "Elephant", "cost": ELEPHANT_COST},
            {"name": "Giraffe",  "cost": GIRAFFE_COST},
            {"name": "Hippo",    "cost": HIPPO_COST},
            {"name": "Zebra",    "cost": ZEBRA_COST},
        ]
        self.item_rects: list[pygame.Rect] = []
        self.hover_item = -1

        # make sure we start with at least one poacher for visibility tests
        self.control.spawn_poacher()

      # ───── shop scrolling & speed buttons ─-
        self.shop_scroll = 0   # pixels
        self.btn_pause   = pygame.Rect(0,0,0,0)    # will be sized each frame
        self.btn_speed   = []  # three Rects for 1×,2x and 3×
        
 
    # ───────────────────────────── public API ────────────────────────────────
    def update(self, dt: float):
        """Called every frame by your main loop."""
        self._update_ui(dt)
        self._handle_events()
        self._draw()

    def exit(self):
        pygame.quit()
        sys.exit()

    # ─────────────────────────────── helpers ────────────────────────────────
    def _update_ui(self, dt: float):
        if (not self.board_gui._dragging) and self.control.board.jeeps:
            self.board_gui.follow(self.control.board.jeeps[0].position)
        self.board_gui.update_day_night(dt)

        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
            self.feedback       = ""

    # ─────────────────────────── event handling ──────────────────────────────
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.control.running = False
            
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_d:
                    self.control.wildlife_ai.animal_ai.debug_mode = not self.control.wildlife_ai.animal_ai.debug_mode
                    debug_status = "ON" if self.control.wildlife_ai.animal_ai.debug_mode else "OFF"
                    self._show_feedback(f"Debug mode: {debug_status}")

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # 1) Zoom buttons
                if self.btn_zoom_in.collidepoint(ev.pos):
                    self.board_gui.zoom(+1, Vector2(ev.pos), BOARD_RECT)
                elif self.btn_zoom_out.collidepoint(ev.pos):
                    self.board_gui.zoom(-1, Vector2(ev.pos), BOARD_RECT)

                elif BOARD_RECT.collidepoint(ev.pos):
                    self.board_gui.start_drag(Vector2(ev.pos))

                else:
                    # speed buttons
                    if self.btn_pause.collidepoint(ev.pos):
                        # toggle pause
                        self.control.time_multiplier = 0.0 if self.control.time_multiplier else 1.0
                    for i, r in enumerate(self.btn_speed):
                        if r.collidepoint(ev.pos):
                            self.control.time_multiplier = float(SPEED_LEVELS[i])
                            break
                    for i, rect in enumerate(self.item_rects):
                        if rect.collidepoint(ev.pos):
                            self._buy_item(i)
                            break

            # Left mouse button up → stop dragging
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.board_gui.stop_drag()

            elif ev.type == pygame.MOUSEMOTION:
                if self.board_gui._dragging:
                    # continue panning
                    self.board_gui.drag(Vector2(ev.pos), BOARD_RECT)
                else:
                    self.hover_item = next(
                        (i for i, r in enumerate(self.item_rects)
                         if r.collidepoint(ev.pos)),
                        -1
                    )

            elif ev.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if mx >= SCREEN_W - SIDE_PANEL_W: # over side panel -> scroll bar
                    self.shop_scroll += ev.y * 24
                else: # over board -> zoom functionality
                    self.board_gui.zoom(ev.y, Vector2((mx, my)), BOARD_RECT)

    # ───────────────────────────── shop logic ───────────────────────────────
    def _buy_item(self, index: int):
        item = self.shop_items[index]
        if self.control.capital.deductFunds(item["cost"]):
            name = item["name"]
            if   name == "Ranger":  self.control.spawn_ranger()
            elif name == "Plant":   self.control.spawn_plant()
            elif name == "Pond":    self.control.spawn_pond()
            else:                   self.control.spawn_animal(name.upper())
            self._show_feedback(f"Purchased {name} for ${item['cost']}")
        else:
            self._show_feedback("Insufficient funds!")

    def _show_feedback(self, msg: str):
        self.feedback       = msg
        self.feedback_timer = 2.0
        self.feedback_alpha = 255

    # ───────────────────────────── drawing ───────────────────────────────────
    def _draw(self):
        self.screen.fill((40, 45, 50))
        self.board_gui.render(self.screen, BOARD_RECT)
        self._draw_top_bar()
        self._draw_bottom_bar()
        self._draw_side_panel()
        self._draw_feedback()
        self._draw_zoom_buttons()
        pygame.display.flip()

    # ---------------- top bar ------------------------------------------------
    def _draw_top_bar(self):
        margin, box_h, radius = 10, 30, 8

        def box(text: str, x: int, *, right=False, col=(60,60,232)):
            surf = self.font_medium.render(text, True, (255,255,255))
            w = surf.get_width() + 20
            rx = SCREEN_W - x - w if right else x
            rect = pygame.Rect(rx, (TOP_BAR_H - box_h)//2, w, box_h)
            pygame.draw.rect(self.screen, col, rect, border_radius=radius)
            pygame.draw.rect(self.screen, (255,255,255), rect, 2, border_radius=radius)
            self.screen.blit(surf, (rx+10, rect.y + (box_h - surf.get_height())//2))
            return w

        pygame.draw.rect(self.screen, (60,70,90), (0,0,SCREEN_W,TOP_BAR_H))

        x = margin
        for txt in [f"Tourists: {len(self.control.board.tourists)}",
                    f"Animals: {len(self.control.board.animals)}"]:
            x += box(txt, x) + margin
        box(f"Capital: ${self.control.capital.getBalance():.0f}", margin,
            right=True, col=(0,100,0))

    # ---------------- bottom bar -------------------------------------------
    def _draw_bottom_bar(self):
        margin, oval_h = 20, 50

        def oval(text: str, x: int):
            surf = self.font_medium.render(text, True, (255,255,255))
            ow = surf.get_width() + 40
            rect = pygame.Rect(x, SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - oval_h)//2,
                               ow, oval_h)
            pygame.draw.ellipse(self.screen, (40,45,60), rect)
            pygame.draw.ellipse(self.screen, (255,255,255), rect, 2)
            self.screen.blit(surf, (rect.x + (ow - surf.get_width())//2,
                                    rect.y + (oval_h - surf.get_height())//2))
            return ow

        pygame.draw.rect(self.screen, (60,70,90),
                         (0, SCREEN_H - BOTTOM_BAR_H,
                          SCREEN_W - SIDE_PANEL_W, BOTTOM_BAR_H))

        date, time_s = self.control.timer.get_date_time()
        game_time    = self.control.timer.get_game_time()

        x = margin
        for k in list(game_time.keys())[:4]:
            x += oval(f"{k}: {game_time[k]}", x) + margin

        box_y = SCREEN_H - BOTTOM_BAR_H + 4
        box_x = SCREEN_W - SIDE_PANEL_W - 140
        for i, txt in enumerate((date, time_s)):
            rect = pygame.Rect(box_x, box_y + i*34, 120, 30)
            pygame.draw.rect(self.screen, (153,101,21), rect, border_radius=4)
            pygame.draw.rect(self.screen, (255,255,255), rect, 2, border_radius=4)
            surf = self.font_medium.render(txt, True, (255,255,255))
            self.screen.blit(surf, (rect.x + (120 - surf.get_width())//2,
                                    rect.y + (30  - surf.get_height())//2))

    # ---------------- side panel -------------------------------------------
    def _draw_side_panel(self):
        px, py = SCREEN_W - SIDE_PANEL_W, TOP_BAR_H
        pygame.draw.rect(self.screen, (70,80,100),
                         (px, py, SIDE_PANEL_W, SCREEN_H - py))
        title = self.font_medium.render("Shop", True, (255,255,255))
        self.screen.blit(title, (px + 20, py + 10))

        self.item_rects.clear()
        top  = py + 50    # top of list
        bottom  = SCREEN_H - BOTTOM_BAR_H - 60  # leaving space for the pause buttons
        scroll_limit  = max(0, (len(self.shop_items)*44) - (bottom-top))

        # clamp scroll offset
        self.shop_scroll = max(-scroll_limit, min(0, self.shop_scroll))
        y = top + self.shop_scroll

        for i, item in enumerate(self.shop_items):
            rect = pygame.Rect(px + 20, y, SIDE_PANEL_W - 40, 36)
            self.item_rects.append(rect)

            if top <= rect.bottom <= bottom: # only draw visible ones
                colour = (80,110,160) if i == self.hover_item else (90,100,120)
                pygame.draw.rect(self.screen, colour, rect, border_radius=4)
                txt = self.font_small.render(f"{item['name']}: ${item['cost']}",
                                             True, (255,255,255))
                self.screen.blit(txt, (rect.x + 8, rect.y + 6))
            y += 44

             # scrollbar
            if scroll_limit > 0:
                bar_h = (bottom-top) * (bottom-top) / (bottom-top+scroll_limit)
                bar_y = top - self.shop_scroll * (bottom-top-bar_h) / scroll_limit
                sb_rect = pygame.Rect(SCREEN_W-16, int(bar_y), 8, int(bar_h))
                pygame.draw.rect(self.screen, (40,40,50), (SCREEN_W-16, top, 8, bottom-top))
                pygame.draw.rect(self.screen, (140,140,160), sb_rect, border_radius=3)

        # speed / pause buttons
        self._draw_speed_buttons()

    # ---------------- feedback --------------------------------------------
    def _draw_feedback(self):
        if self.feedback_alpha <= 0:
            return
        surf = self.font_medium.render(self.feedback, True, (128,0,0))
        surf.set_alpha(self.feedback_alpha)
        x = (SCREEN_W - surf.get_width()) // 2
        y = SCREEN_H - BOTTOM_BAR_H - surf.get_height() - 20
        self.screen.blit(surf, (x,y))

    # ---------------- zoom buttons ----------------------------------------
    def _draw_zoom_buttons(self):
        # bottom-right inside BOARD_RECT
        x = BOARD_RECT.right - ZOOM_BTN_SZ - 8
        y = BOARD_RECT.bottom - ZOOM_BTN_SZ*2 - 12
        self.btn_zoom_in.topleft  = (x, y)
        self.btn_zoom_out.topleft = (x, y + ZOOM_BTN_SZ + 4)

        for rect in (self.btn_zoom_in, self.btn_zoom_out):
            pygame.draw.rect(self.screen, (90,100,120), rect, border_radius=4)
            pygame.draw.rect(self.screen, (255,255,255), rect, 2, border_radius=4)

        plus  = self.font_small.render("+", True, (255,255,255))
        minus = self.font_small.render("–", True, (255,255,255))
        self.screen.blit(plus,  (self.btn_zoom_in.centerx  - plus.get_width()//2,
                                 self.btn_zoom_in.centery  - plus.get_height()//2))
        self.screen.blit(minus, (self.btn_zoom_out.centerx - minus.get_width()//2,
                                 self.btn_zoom_out.centery - minus.get_height()//2))
        
    # ───────────────────────── speed buttons ─────────────────────────────
    def _draw_speed_buttons(self):
        panel_x = SCREEN_W - SIDE_PANEL_W
        btn_w, btn_h, gap = 50, 32, 8
        
        #horizontal center inside side-panel
        total_w = btn_w *4 + gap*3 
        start_x = panel_x + (SIDE_PANEL_W - total_w)//2

        #verticall center inside bottom-bar 
        y = SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - btn_h)//2

        rects = []
        for i in range(4):
            x = start_x + i*(btn_w+gap)
            rects.append(pygame.Rect(x, y, btn_w, btn_h))
        self.btn_pause, self.btn_speed = rects[0], rects[1:]

        # colours
        green_bg  = (25,120, 25)
        grey_bg   = (85, 90,110)
        white     = (255,255,255)

        for i, r in enumerate(rects):
            is_active = ((i == 0 and self.control.time_multiplier == 0) or
                        (i > 0 and self.control.time_multiplier == SPEED_LEVELS[i-1]))


            #pause button (index 0) 
            if i == 0:
                #circular green button
                radius = min(r.width, r.height) // 2 - 2
                centre = r.center
                paused = (self.control.time_multiplier == 0)

                # background
                if paused:
                    pygame.draw.circle(self.screen, green_bg, centre, radius)
                    pygame.draw.circle(self.screen, white, centre, radius, 2)

                if paused:
                    # draw resume button ||
                    bw = max(4, radius//3)
                    bh = int(radius*1.0)
                    gap = bw//2
                    for dx in (-gap-bw//2, gap+bw//2):
                        bar = pygame.Rect(centre[0]+dx-bw//2,
                                          centre[1]-bh//2, bw, bh)
                        pygame.draw.rect(self.screen, white, bar, border_radius=2)
                else:
                    # draw pause icon (|>)
                    pts = [
                        (centre[0]-radius//3, centre[1]-radius//2),
                        (centre[0]-radius//3, centre[1]+radius//2),
                        (centre[0]+radius//2, centre[1])
                    ]
                    pygame.draw.polygon(self.screen, white, pts)

            #3 different speed buttons (1×/2×/3×)
            else:
                bg = green_bg if is_active else grey_bg
                pygame.draw.rect(self.screen, bg, r, border_radius=4)
                pygame.draw.rect(self.screen, white, r, 2, border_radius=4)
                label = f"{i}×"
                txt = self.font_small.render(label, True, white)
                self.screen.blit(txt, (r.centerx - txt.get_width() // 2,
                                       r.centery - txt.get_height() // 2))
