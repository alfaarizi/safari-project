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
    BUFFALO_COST, ELEPHANT_COST, GIRAFFE_COST, HIPPO_COST, ZEBRA_COST,CHIP_COST
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

ZOOM_BTN_SZ = 32        # size of the + / – buttons
SPEED_LEVELS = [1, 4, 8] #index 0 for 1x, index 1 for 4x, index 2 for 8x speed levels => logical speeds for buttons 1x,2x,3x
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

        self.auto_follow = False
        self.feedback = ""
        self.feedback_timer = 0
        self.feedback_alpha = 0
        self.last_day = -1
        self.hover_item = -1
        self.item_rects = []

        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 32)

        self.btn_zoom_in = pygame.Rect(0, 0, ZOOM_BTN_SZ, ZOOM_BTN_SZ)
        self.btn_zoom_out = pygame.Rect(0, 0, ZOOM_BTN_SZ, ZOOM_BTN_SZ)


        # Initialize shop items
        self.shop_items = [
            {"name": "Ranger", "cost": RANGER_COST},
            {"name": "Plant", "cost": PLANT_COST},
            {"name": "Pond", "cost": POND_COST},
            {"name": "Hyena", "cost": HYENA_COST},
            {"name": "Lion", "cost": LION_COST},
            {"name": "Tiger", "cost": TIGER_COST},
            {"name": "Buffalo", "cost": BUFFALO_COST},
            {"name": "Elephant", "cost": ELEPHANT_COST},
            {"name": "Giraffe", "cost": GIRAFFE_COST},
            {"name": "Hippo", "cost": HIPPO_COST},
            {"name": "Zebra", "cost": ZEBRA_COST},
            {"name": "Jeep", "cost": 50, "type": "jeep"},
            {"name": "Straight H Road", "cost": 10, "type": "h_road"},
            {"name": "Straight V Road", "cost": 10, "type": "v_road"}
        ]
        self.item_rects: list[pygame.Rect] = []

        self.dragging_road = None
        self.dragging_jeep = False
        self.drag_start = None

        self.control: GameController = controller
        tile_w = BOARD_RECT.width // self.control.board.width  
        self.board_gui = BoardGUI(self.control.board, default_tile=tile_w)
        self.feedback_queue = []

        # Set initial zoom to show full board
        self.board_gui.tile = self.board_gui.MIN_TILE
        self.full_tile = self.board_gui.tile

        # Initialize camera to show the full board
        self.board_gui.cam = Vector2(
            self.control.board.width / 2,  # Center the camera horizontally
            self.control.board.height / 2  # Center the camera vertically
        )

        # Adjust viewport boundaries to match board dimensions
        self.board_gui.min_x = 0
        self.board_gui.max_x = controller.board.width
        self.board_gui.min_y = 0
        self.board_gui.max_y = controller.board.height

        # Calculate initial zoom to fit board width
        board_width_pixels = BOARD_RECT.width
        board_height_pixels = BOARD_RECT.height
        width_ratio = board_width_pixels / controller.board.width
        height_ratio = board_height_pixels / controller.board.height
        self.board_gui.tile = min(width_ratio, height_ratio) * 0.9  # 90% to add some margin

        self.selected_poacher = None
        self.attack_button_rect = None

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

        # ───── shop scrolling & speed buttons ─-
        self.shop_scroll = 0   # pixels
        self.btn_pause   = pygame.Rect(0,0,0,0)    # will be sized each frame
        self.btn_speed   = []  # three Rects for 1×,2x and 3×

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
        self.board_gui.update_day_night(dt, self.control.timer.elapsed_seconds, pygame.mouse.get_pos())
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
        elapsed = self.control.timer.elapsed_seconds
        self.board_gui.update_day_night(dt, elapsed, pygame.mouse.get_pos())

        # feedback fade
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            if self.feedback_queue:
                self._pop_next_feedback()
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
        mouse_pos = pygame.mouse.get_pos()

        for ev in pygame.event.get():

            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_d:
                self.control.wildlife_ai.animal_ai.debug_mode = not self.control.wildlife_ai.animal_ai.debug_mode
                debug_status = "ON" if self.control.wildlife_ai.animal_ai.debug_mode else "OFF"
                self._feedback(f"Debug mode: {debug_status}")

            # -----------------------------------------------------------------
            #  LEFT-CLICK  (button 1)
            # -----------------------------------------------------------------
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.control.chip_placement_mode:
                    world_pos = self.board_gui.screen_to_world(ev.pos)
                    if world_pos:
                        chip_placed = self.control.handle_chip_click(world_pos)
                        if chip_placed:
                            return 
                
                # Check if clicking the attack button
                if self.attack_button_rect and self.attack_button_rect.collidepoint(ev.pos):
                    if self.selected_poacher and self.control.board.rangers:
                        nearest = min(
                            self.control.board.rangers,
                            key=lambda r: r.position.distance_to(self.selected_poacher.position)
                        )
                        nearest.set_target(self.selected_poacher.position)
                        nearest.assigned_poacher = self.selected_poacher
                        self._feedback(f"Ranger {nearest.name} is attacking {self.selected_poacher.name}!")
                    self.attack_button_rect = None
                    self.selected_poacher = None
                    return

                # Clicked on the board?
                if BOARD_RECT.collidepoint(ev.pos):
                    world_pos = self.board_gui.screen_to_world(ev.pos)
                    clicked_poacher = None
                    for poacher in self.control.board.poachers:
                        if poacher.visible and poacher.position.distance_to(world_pos) < 1.0:
                            clicked_poacher = poacher
                            break

                    if clicked_poacher:
                        self.selected_poacher = clicked_poacher
                        self._feedback(f"Selected {clicked_poacher.name} at {tuple(map(int, clicked_poacher.position))}")
                    else:
                        # Clicked board but not on poacher → clear selection
                        self.selected_poacher = None
                        self.attack_button_rect = None

                    self.board_gui.start_drag(ev.pos)

                # --- zoom buttons --------------------------------------------
                if self.btn_zoom_in.collidepoint(ev.pos):
                    play_button_click()
                    self.board_gui.zoom(+1, ev.pos, BOARD_RECT)
                    continue
                elif self.btn_zoom_out.collidepoint(ev.pos):
                    play_button_click()
                    self.board_gui.zoom(-1, ev.pos, BOARD_RECT)
                    continue
                elif BOARD_RECT.collidepoint(ev.pos) and self.drag_item_idx < 0 :
                     # only pan the map if we’re NOT currently dragging a shop item
                     self.board_gui.start_drag(ev.pos)
                else:
                    # speed buttons
                    if self.btn_pause.collidepoint(ev.pos):
                        # toggle pause
                        self.control.time_multiplier = 0.0 if self.control.time_multiplier else 1.0
                    for i, r in enumerate(self.btn_speed):
                        if r.collidepoint(ev.pos):
                            self.control.time_multiplier = float(SPEED_LEVELS[i])
                            break

                # --- place a road segment (drag-and-drop) --------------------
                if self.dragging_road and BOARD_RECT.collidepoint(ev.pos):
                    board_pos = self.board_gui.screen_to_board(ev.pos, BOARD_RECT)
                    x, y = int(board_pos.x), int(board_pos.y)

                    if self.control.capital.getBalance() >= 10:
                        if self.control.board.add_road_segment(x, y,
                                                               self.dragging_road["type"]):
                            self.control.capital.deductFunds(10)
                            play_place_item()
                            self._feedback("Road placed for $10")
                        else:
                            play_insufficient_funds()
                            self._feedback("Cannot place road here!")
                    else:
                        play_insufficient_funds()
                        self._feedback("Insufficient funds!")

                    self.dragging_road = None
                    continue

                # --- place a jeep (drag-and-drop) ----------------------------
                if self.dragging_jeep and BOARD_RECT.collidepoint(ev.pos):
                    board_pos = self.board_gui.screen_to_board(ev.pos, BOARD_RECT)
                    placed = self.control.try_spawn_jeep(board_pos)
                    if placed:
                        play_purchase_success()
                        self._feedback("Jeep purchased for $50")
                    else:
                        play_insufficient_funds()
                        self._feedback("Must click on an existing road!")
                    self.dragging_jeep = False
                    continue

                # --- start panning the camera --------------------------------
                if BOARD_RECT.collidepoint(ev.pos):
                    self.board_gui.start_drag(ev.pos)
                    continue

                # --- click in the shop ---------------------------------------
                for i, r in enumerate(self.item_rects):
                    if r.collidepoint(ev.pos):
                        item = self.shop_items[i]
                        play_button_click()
                        
                        self.board_gui._dragging = False
                        # play click sound for shop entry
                        self.drag_item_idx = i
                        self.drag_pos      = ev.pos
                        self.hover_tile    = None
                        self.hover_valid   = False

                        if item.get("type") == "jeep":
                            self.dragging_jeep = True  # start jeep drag
                        elif item.get("type") in ("h_road", "v_road"):
                            self.dragging_road = item  # start road drag
                        # else:
                        #     self._buy_item(i)  # normal purchase
                        break  # stop scanning items

            # -----------------------------------------------------------------
            #  BUTTON RELEASE
            # -----------------------------------------------------------------
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

            # -----------------------------------------------------------------
            #  MOUSE MOVE
            # -----------------------------------------------------------------
            elif ev.type == pygame.MOUSEMOTION:
                # 1. keep panning if the camera is being dragged
                if self.board_gui._dragging:
                    self.board_gui.drag(ev.pos, BOARD_RECT)                
                else:
                    self.hover_item = next(
                        (i for i, r in enumerate(self.item_rects)
                         if r.collidepoint(ev.pos)),
                        -1
                    )

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
                mx, my = pygame.mouse.get_pos()
                if mx >= SCREEN_W - SIDE_PANEL_W: # over side panel -> scroll bar
                    self.shop_scroll += ev.y * 24
                else: # over board -> zoom functionality
                    self.board_gui.zoom(ev.y, Vector2((mx, my)), BOARD_RECT)

    # ───────────────────────────── shop logic ───────────────────────────────
    def _buy_item(self, index: int):
        item = self.shop_items[index]
        # Skip road items
        if "type" in item:
            return

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
            elif name == "Light Chip":
                self.control.enter_chip_mode()
                return
            else:
                self.control.spawn_animal(name.upper())
                play_place_item()
                play_animal_sound(name.lower())

            play_purchase_success()
            self._feedback(f"Purchased {name} for ${item['cost']}")
        else:
            play_insufficient_funds()
            self._feedback("Insufficient funds!")

    def _feedback(self, msg: str):
        self.feedback_queue.append(msg)
        if self.feedback_timer <= 0:
            self._pop_next_feedback()


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

        if self.dragging_road and BOARD_RECT.collidepoint(pygame.mouse.get_pos()):
            mouse_pos = pygame.mouse.get_pos()
            board_pos = self.board_gui.screen_to_board(mouse_pos, BOARD_RECT)
            x, y = int(board_pos.x), int(board_pos.y)

            cells_to_preview = []
            if self.dragging_road["type"] == "h_road":
                if 0 <= y < self.control.board.height:
                    start_x = x
                    max_cells = min(10, self.control.board.width - start_x if start_x >= 0 else 10)
                    for i in range(max_cells):
                        cur_x = start_x + i
                        if 0 <= cur_x < self.control.board.width:
                            if any(r.pos == Vector2(cur_x, y) for r in self.control.board.roads):
                                break
                            cells_to_preview.append((cur_x, y))
            else:  # v_road
                if 0 <= x < self.control.board.width:
                    start_y = y
                    max_cells = min(10, self.control.board.height - start_y if start_y >= 0 else 10)
                    for i in range(max_cells):
                        cur_y = start_y + i
                        if 0 <= cur_y < self.control.board.height:
                            if any(r.pos == Vector2(x, cur_y) for r in self.control.board.roads):
                                break
                            cells_to_preview.append((x, cur_y))

            # Draw preview cells
            for cell_x, cell_y in cells_to_preview:
                screen_pos = self.board_gui.board_to_screen(Vector2(cell_x, cell_y), BOARD_RECT)
                preview_rect = pygame.Rect(
                    int(screen_pos.x - self.board_gui.tile / 2),
                    int(screen_pos.y - self.board_gui.tile / 2),
                    int(self.board_gui.tile),
                    int(self.board_gui.tile)
                )
                pygame.draw.rect(self.screen, (105, 105, 105, 128), preview_rect)
                pygame.draw.rect(self.screen, (255, 255, 255), preview_rect, 1)
        
        self._draw_top_bar()
        self._draw_bottom_bar()
        self._draw_side_panel()
        self._draw_feedback()
        self._draw_zoom_buttons()

        # 2) ghost‐sprite follows cursor while dragging
        if self.drag_item_idx >= 0:

            name = self.shop_items[self.drag_item_idx]["name"].lower()
            print(name)
            if name not in ["jeep", "straight v road", "straight h road"]:
                img  = (getattr(self.board_gui, name) 
                if name in ("plant", "pond", "ranger") 
                else self.board_gui.animals[
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
        
        # 3) draw selected rangers (controllable-rangers)
        if self.selected_poacher and self.selected_poacher in self.control.board.poachers:
            # Convert poacher world position to screen position
            world_pos = self.selected_poacher.position
            tile_size = self.board_gui.tile
            cam = self.board_gui.cam
            board_rect = BOARD_RECT

            # Translate world to screen
            px = int(board_rect.centerx + (world_pos.x - cam.x) * tile_size)
            py = int(board_rect.centery + (world_pos.y - cam.y) * tile_size)

            # Create attack button rect relative to poacher position
            self.attack_button_rect = pygame.Rect(px + 20, py - 10, 80, 30)

            pygame.draw.rect(self.screen, (200, 50, 50), self.attack_button_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), self.attack_button_rect, 2, border_radius=5)
            label = self.font_small.render("Attack", True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=self.attack_button_rect.center))

        # 4) finally update the display
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
        bottom = SCREEN_H - BOTTOM_BAR_H - 32  #  speed buttons row - gap_above_buttons

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
                frac  = (bottom - top)/(bottom - top + scroll_limit)
                bar_h = max(20, int((bottom-top) * frac))   #never smaller than 20 px
                bar_y = top - self.shop_scroll * (bottom-top-bar_h) / scroll_limit
                rail_x = px + SIDE_PANEL_W - 16  # inside the panel, not at screen edge
                sb_rect = pygame.Rect(rail_x, int(bar_y), 8, int(bar_h))
                pygame.draw.rect(self.screen, (40,40,50), (rail_x, top, 8, bottom-top))
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
        btn_h, gap = 32, 8
        num_btns = 4 
        #the width inside the panel that we can use for the play/pause and speed buttons 
        usable_w = SIDE_PANEL_W - 40 - gap*(num_btns-1)
        btn_w = max(34, usable_w // num_btns)


        #horizontal center inside side-panel
        total_w = btn_w *4 + gap*3 
        start_x = panel_x + (SIDE_PANEL_W - total_w)//2

        #verticall center inside bottom-bar 
        y = SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - btn_h)//2
        total_w = btn_w * 4 + gap * 3
        start_x = panel_x + (SIDE_PANEL_W - total_w) // 2

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

                #drawing the outline for both play/pause button 
                pygame.draw.circle(self.screen, white, centre, radius, 2)

                # background
                if paused:
                    pygame.draw.circle(self.screen, green_bg, centre, radius-1)

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

    # ───────────────────────── others ─────────────────────────────
    def _pop_next_feedback(self):
        if self.feedback_queue:
            self.feedback = self.feedback_queue.pop(0)
            self.feedback_timer = 2.0
            self.feedback_alpha = 255
