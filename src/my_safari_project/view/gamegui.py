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

        self.state          = "DRAGGING" 
        self.drag_item_idx  = -1
        self.drag_pos       = (0,0)
        self.hover_tile     = None
        self.hover_valid    = False

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
    #     for ev in pygame.event.get():
    #         if ev.type == pygame.QUIT:
    #             self.control.running = False

    #         elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
    #             # 1) Zoom buttons
    #             if self.btn_zoom_in.collidepoint(ev.pos):
    #                 self.board_gui.zoom(+1, Vector2(ev.pos), BOARD_RECT)
    #             elif self.btn_zoom_out.collidepoint(ev.pos):
    #                 self.board_gui.zoom(-1, Vector2(ev.pos), BOARD_RECT)

    #             elif BOARD_RECT.collidepoint(ev.pos):
    #                 self.board_gui.start_drag(Vector2(ev.pos))

    #             else:
    #                 for i, rect in enumerate(self.item_rects):
    #                     if rect.collidepoint(ev.pos):
    #                         self._buy_item(i)
    #                         break

    #         # Left mouse button up → stop dragging
    #         elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
    #             self.board_gui.stop_drag()

    #         elif ev.type == pygame.MOUSEMOTION:
    #             if self.board_gui._dragging:
    #                 # continue panning
    #                 self.board_gui.drag(Vector2(ev.pos), BOARD_RECT)
    #             else:
    #                 self.hover_item = next(
    #                     (i for i, r in enumerate(self.item_rects)
    #                      if r.collidepoint(ev.pos)),
    #                     -1
    #                 )

    #         elif ev.type == pygame.MOUSEWHEEL:
    #             # ev.y == +1 (wheel up) or -1 (wheel down)
    #             self.board_gui.zoom(ev.y, Vector2(pygame.mouse.get_pos()), BOARD_RECT)
        for ev in pygame.event.get():
    # ------- quit -------------------------------------------------
            if ev.type == pygame.QUIT:
                self.control.running = False

            # ------- mouse down -------------------------------------------
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # start dragging from the shop
                if self.state == "DRAGGING":
                    for i,r in enumerate(self.item_rects):
                        if r.collidepoint(ev.pos):
                            self.state = "DRAGGING"
                            self.drag_item_idx = i
                            self.drag_pos      = ev.pos
                            self.hover_tile = None 
                            self.hover_valid = False 
                            break
                # camera pan
                if self.state == "DRAGGING" and BOARD_RECT.collidepoint(ev.pos):
                    self.board_gui.start_drag(Vector2(ev.pos))

            # ------- mouse move -------------------------------------------
            elif ev.type == pygame.MOUSEMOTION:
                self.drag_pos = ev.pos
                
                if self.state == "DRAGGING" and self.drag_item_idx >= 0:
                    tile = self.board_gui.screen_to_tile(ev.pos, BOARD_RECT)
                    self.hover_tile  = tile
                    
                    self.hover_valid = (tile is not None and self.control.board.is_placeable(tile))

                elif self.board_gui._dragging:
                    self.board_gui.drag(Vector2(ev.pos), BOARD_RECT)
                else:
                    self.hover_item = next((i for i,r in enumerate(self.item_rects)
                                            if r.collidepoint(ev.pos)), -1)
                #this line is for debugging 
                # if self.hover_tile is not None:
                #     print("mouse", ev.pos, "→ tile", self.hover_tile)


            # ------- mouse up ---------------------------------------------
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self.state == "DRAGGING" and self.drag_item_idx >= 0:
                    if self.hover_tile is not None and self.hover_valid:
                        self._place_item(self.drag_item_idx, self.hover_tile)
                    else:
                        # user clicked without dragging -> show feedback
                        self._show_feedback("Drag the item onto the board, then release it.")
                    self.drag_item_idx = -1
                    self.hover_tile    = None
                    self.hover_valid   = False
                self.board_gui.stop_drag()

            # ------- wheel -------------------------------------------------
            elif ev.type == pygame.MOUSEWHEEL:
                self.board_gui.zoom(ev.y, Vector2(pygame.mouse.get_pos()), BOARD_RECT)

    def _place_item(self, idx: int, tile: Vector2):
        item = self.shop_items[idx]
        if not self.control.capital.deductFunds(item["cost"]):
            self._show_feedback("Insufficient funds!")
            return
        name = item["name"]
        match name:
            case "Ranger":  self.control.spawn_ranger(tile)
            case "Plant":   self.control.spawn_plant(tile)
            case "Pond":    self.control.spawn_pond(tile)
            case _:         self.control.spawn_animal(name.upper(), tile)
        self._show_feedback(f"Placed {name} for ${item['cost']}")
        
        if tile is None:
           self._show_feedback("Drag the item onto the board first.")
           return
    


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
    # def _draw(self):
    #     self.screen.fill((40, 45, 50))
    #     self.board_gui.render(self.screen, BOARD_RECT)
    #     self._draw_top_bar()
    #     self._draw_bottom_bar()
    #     self._draw_side_panel()
    #     self._draw_feedback()
    #     self._draw_zoom_buttons()
    #     pygame.display.flip()

    def _draw(self):
        self.screen.fill((40, 45, 50))
        #drawing the board with red/green highlight
        self.board_gui.render(
            self.screen,
            BOARD_RECT,
            hover_tile  = self.hover_tile if self.state == "DRAGGING" else None,
            hover_valid = self.hover_valid,
        )


        if self.state == "DRAGGING" and self.drag_item_idx >= 0:
            name = self.shop_items[self.drag_item_idx]["name"].lower()
            if name in ("plant", "pond", "ranger"):
                img = getattr(self.board_gui, name, None)# plant / pond / ranger
            else:
                img = self.board_gui.animals.get(name)      

            if img is not None:
                ghost = pygame.transform.scale(img, (32, 32))
                ghost.set_alpha(180)
                self.screen.blit(ghost, (self.drag_pos[0] - 16, self.drag_pos[1] - 16))
                

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
        y = py + 50
        for i, item in enumerate(self.shop_items):
            rect = pygame.Rect(px + 20, y, SIDE_PANEL_W - 40, 36)
            self.item_rects.append(rect)
            colour = (80,110,160) if i == self.hover_item else (90,100,120)
            pygame.draw.rect(self.screen, colour, rect, border_radius=4)
            txt = self.font_small.render(f"{item['name']}: ${item['cost']}",
                                         True, (255,255,255))
            self.screen.blit(txt, (rect.x + 8, rect.y + 6))
            y += 44

    # ---------------- feedback --------------------------------------------
    def _draw_feedback(self):
        if self.feedback_alpha <= 0:
            return
        surf = self.font_medium.render(self.feedback, True, (128,0,0))
        surf.set_alpha(self.feedback_alpha)
        # x = (SCREEN_W - surf.get_width()) // 2
        # y = SCREEN_H - BOTTOM_BAR_H - surf.get_height() - 20
        x = BOARD_RECT.x + (BOARD_RECT.width - surf.get_width()) // 2
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
