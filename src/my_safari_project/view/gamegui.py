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
# Import sound effects
from my_safari_project.audio import (
    play_button_click, play_purchase_success, play_insufficient_funds,
    play_place_item, play_day_transition, play_money_received,
    play_jeep_start, play_jeep_move, play_jeep_stop, play_jeep_crash,
    play_animal_sound, play_footsteps, play_game_music
)

# ────────────────────────────── layout constants ──────────────────────────────
SCREEN_W, SCREEN_H = 1200, 800
# Define BOARD_RECT to use most of the screen space
SIDE_PANEL_W       = 200
TOP_BAR_H          = 50
BOTTOM_BAR_H       = 80

BOARD_RECT = pygame.Rect(
    10,                                         # Left margin
    TOP_BAR_H + 10,                             # Top margin
    SCREEN_W - SIDE_PANEL_W - 20,               # Width (full width minus side panel and margins)
    SCREEN_H - TOP_BAR_H - BOTTOM_BAR_H - 20    # Height (remaining vertical space)
)

ZOOM_BTN_SZ = 32                                # size of the + / – buttons

# ────────────────────────────────── GameGUI ───────────────────────────────────
class GameGUI:
    """
    Pure UI layer.

    The only “smart” behaviour it keeps is an *optional* auto-follow of the
    first jeep.  As soon as the player drags or pans, auto-follow is disabled
    until they press the **F** key.
    """

    def __init__(self, controller: GameController):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        self.control: GameController = controller
        #self.board_gui = BoardGUI(self.control.board)
        tile_w = BOARD_RECT.width // self.control.board.width  
        self.board_gui = BoardGUI(self.control.board, default_tile=tile_w)

        #self.board_gui.tile = self.board_gui.MIN_TILE
        self.board_gui.cam = Vector2(
                (controller.board.width - 1) / 2,
                (controller.board.height - 1) / 2)
        self.full_tile = self.board_gui.tile

        # Set viewport boundaries
        self.board_gui.min_x = 0
        self.board_gui.max_x = controller.board.width - 1
        self.board_gui.min_y = 0
        self.board_gui.max_y = controller.board.height - 1

        # Auto-follow flag (can be toggled with "F")
        self.auto_follow = False

        # Fonts
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
        #added for (hover/highlight) ,it lays out the clickable buttons for the shop
        px, py = SCREEN_W - SIDE_PANEL_W, TOP_BAR_H
        y  = py + 50
        for _ in self.shop_items:
            self.item_rects.append(
                pygame.Rect(px + 20, y, SIDE_PANEL_W - 40, 36)
            )
            y += 44
        self.hover_item = -1
        
        # Audio
        self.last_day = -1
        play_game_music()

        #drag state
        self.drag_item_idx = -1
        self.drag_pos      = (0,0)
        self.hover_tile    = None
        self.hover_valid   = False

    # ───────────────────────────── public API ────────────────────────────────
    def update(self, dt: float):
        """Called every frame by your main loop."""
        self._update_ui(dt)
        self._handle_events()
        self._draw()
        self._check_day_transition()

    def exit(self):
        pygame.quit()
        sys.exit()

    # ─────────────────────────────── helpers ────────────────────────────────
    def _update_ui(self, dt: float):
        # optional auto-follow (only if it is ON **and** we’re zoomed-in)
        if (self.auto_follow
                and self.board_gui.tile > self.full_tile
                and self.control.board.jeeps):
            self.board_gui.follow(self.control.board.jeeps[0].position)

        # day/night tint
        self.board_gui.update_day_night(dt)

        # feedback fade
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
        
         #  added: show hand cursor while dragging a shop item ----
        if self.drag_item_idx >= 0:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            
    def _check_day_transition(self):
        """Check if we've transitioned to a new day and play sound if so."""
        current_day = self.control.timer.get_game_time()['days']
        if self.last_day != -1 and current_day != self.last_day:
            play_day_transition()
            
            # If this is a monthly transition, also play money received sound
            if current_day % 30 == 0:
                play_money_received()
                
        self.last_day = current_day

    # ─────────────────────────── event handling ──────────────────────────────
    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.control.running = False
            
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_d:
                    self.control.wildlife_ai.animal_ai.debug_mode = not self.control.wildlife_ai.animal_ai.debug_mode
                    debug_status = "ON" if self.control.wildlife_ai.animal_ai.debug_mode else "OFF"
                    self._feedback(f"Debug mode: {debug_status}")
                    play_button_click()
            
            # ── toggle follow with “F” ─────────────────────────────
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_f:
                self.auto_follow = not self.auto_follow
            
            # ── mouse buttons ─────────────────────────────────────
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if   self.btn_zoom_in .collidepoint(ev.pos):
                    self.board_gui.zoom(+1, ev.pos, BOARD_RECT)
                    play_button_click()
                elif self.btn_zoom_out.collidepoint(ev.pos):
                    self.board_gui.zoom(-1, ev.pos, BOARD_RECT)
                    play_button_click()
                #elif BOARD_RECT.collidepoint(ev.pos):
                    #self.board_gui.start_drag(ev.pos)
                elif BOARD_RECT.collidepoint(ev.pos) and self.drag_item_idx < 0 :
                     # only pan the map if we’re NOT currently dragging a shop item
                     self.board_gui.start_drag(ev.pos)
                
                else:
                    # for i, r in enumerate(self.item_rects):
                    #     if r.collidepoint(ev.pos):
                    #         play_button_click
                    #         self._buy_item(i)
                    #         break
                    for i, rect in enumerate(self.item_rects):
                        if rect.collidepoint(ev.pos):
                            #  stop any camera pan that might have started ──
                            self.board_gui._dragging = False
                            # play click sound for shop entry
                            play_button_click()
                            self.drag_item_idx = i
                            self.drag_pos      = ev.pos
                            self.hover_tile    = None
                            self.hover_valid   = False
                            break
            
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                # if self.board_gui._dragging:
                #     self.board_gui.stop_drag()
                #     self.auto_follow = False   # user took manual control

                if self.drag_item_idx >= 0:
                    # store release-point tile and reuse
                    self.hover_tile = self.board_gui.screen_to_tile(ev.pos, BOARD_RECT) # here we Convert cursor position to board tile and check if that tile is valid
                    self.hover_valid = bool(
                        self.hover_tile
                        and self.control.board.is_placeable(self.hover_tile)
                    )

                    if self.hover_valid:
                        i    = self.drag_item_idx
                        item = self.shop_items[i]
                        cost = item["cost"]
                        if self.control.deduct_funds(cost):
                            name = item["name"]
                            # play placement sound first after the successfull drop
                            play_place_item()
                            match name:
                                case "Ranger": self.control.spawn_ranger(self.hover_tile)
                                case "Plant":  self.control.spawn_plant(self.hover_tile)
                                case "Pond":   self.control.spawn_pond(self.hover_tile)
                                case _:         
                                    self.control.spawn_animal(name.upper(), self.hover_tile)
                                    play_animal_sound(name.lower())
                            play_purchase_success()
                            self._feedback(f"Placed {name} for ${cost}")
                        else:
                            self._feedback("Insufficient funds!")
                    else:
                        self._feedback("Invalid placement!")
  

                    # reset drag state
                    self.drag_item_idx = -1
                    self.hover_tile    = None
                    self.hover_valid   = False

                # still allow panning to stop
                if self.board_gui._dragging:
                    self.board_gui.stop_drag()
                    self.auto_follow = False  # user took manual control
            
            elif ev.type == pygame.MOUSEMOTION:
                # 1. keep panning if the camera is being dragged
                if self.board_gui._dragging:
                    self.board_gui.drag(ev.pos, BOARD_RECT)

                # 2. always update hover & drag information
                prev_hover   = self.hover_item
                self.hover_item = next(
                    (i for i, r in enumerate(self.item_rects) if r.collidepoint(ev.pos)),
                    -1
                )

                if self.drag_item_idx >= 0:            # dragging something from the shop
                    self.drag_pos     = ev.pos # for the ghost
                    tile              = self.board_gui.screen_to_tile(ev.pos, BOARD_RECT)
                    self.hover_tile  = tile
                    self.hover_valid = bool(tile and
                                self.control.board.is_placeable(tile))
                
                #for debugging
                # tile = self.board_gui.screen_to_tile(ev.pos, BOARD_RECT)
                # print("mouse", ev.pos, "→ tile", tile)

                    # Play hover sound if hovering over a new item
                    # (Uncomment if you have a hover sound)
                    # if prev_hover != self.hover_item and self.hover_item != -1:
                    #     play_hover_sound()

            elif ev.type == pygame.MOUSEWHEEL:
                self.board_gui.zoom(ev.y, pygame.mouse.get_pos(), BOARD_RECT)
                # zoom counts as manual camera work
                self.auto_follow = False

    # ───────────────────────────── shop logic ───────────────────────────────
    def _buy_item(self, index: int):
        item = self.shop_items[index]
        if self.control.capital.deductFunds(item["cost"]):
            name = item["name"]
            if name == "Ranger":
                self.control.spawn_ranger()
                play_place_item()
            elif name == "Plant":
                self.control.spawn_plant()
                play_place_item()
            elif name == "Pond":
                self.control.spawn_pond()
                play_place_item()
            else:
                self.control.spawn_animal(name.upper())
                play_place_item()
                # Play animal sound
                play_animal_sound(name.lower())
                
            play_purchase_success()
            self._feedback(f"Purchased {name} for ${item['cost']}")
        else:
            play_insufficient_funds()
            self._feedback("Insufficient funds!")

    def _feedback(self, msg: str):
        self.feedback, self.feedback_timer, self.feedback_alpha = msg, 2.0, 255


    # ───────────────────────────── drawing ───────────────────────────────────
    def _draw(self):
        # 1) clear & render board + UI panels
        self.screen.fill((40, 45, 50))
        self.board_gui.render(
                self.screen,
                BOARD_RECT,
                hover_tile  = self.hover_tile if self.drag_item_idx >= 0 else None,
                hover_valid = self.hover_valid
            )
        self._draw_top_bar()
        self._draw_bottom_bar()
        self._draw_side_panel()
        self._draw_feedback()
        self._draw_zoom_buttons()

        # 2) ghost‐sprite follows cursor while dragging
        if self.drag_item_idx >= 0:
            name = self.shop_items[self.drag_item_idx]["name"].lower()
            img  = (getattr(self.board_gui, name)
                    if name in ("plant", "pond", "ranger") else
                    self.board_gui.animals[
                        __import__("my_safari_project.model.animal",
                                fromlist=["AnimalSpecies"]).AnimalSpecies[name.upper()].value
                    ])

            size  = max(20, self.board_gui.tile)  # Make it at least visible when small
            ghost = pygame.transform.scale(img, (size, size))
            ghost.set_alpha(150)

            if self.hover_tile is not None:
                gx, gy = self.hover_tile
                # correct calculation:
                px = (BOARD_RECT.centerx +
                    (gx - self.board_gui.cam.x) * self.board_gui.tile -
                    size // 2)
                py = (BOARD_RECT.centery +
                    (gy - self.board_gui.cam.y) * self.board_gui.tile -
                    size // 2)
            else:
                # fallback raw mouse position
                mx, my = self.drag_pos
                px, py = mx - size // 2, my - size // 2

            self.screen.blit(ghost, (px, py))
        # 3) finally update the display
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

        #self.item_rects.clear()
        y = py + 50
        for i, item in enumerate(self.shop_items):
            rect = self.item_rects[i]
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
