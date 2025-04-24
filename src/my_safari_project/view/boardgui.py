from __future__ import annotations
import os
from typing import Tuple

import pygame
from pygame import Surface, Rect
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.road  import Road


class BoardGUI:

    # -------------------- helpers -----------------------------
    @staticmethod
    def _lerp(c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    # -------------------- lifecycle ---------------------------
    def __init__(self, board: Board, default_tile: int = 32):
        self.board = board
        self.tile  = default_tile           # pixel size of one cell

        # camera centre (world coordinates, **centre of a tile**)
        self.cam = Vector2(board.entrance) + Vector2(0.5, 0.5)

        #   desert, plant, pond, jeep, ranger, poacher
        self._load_assets()

        # day / night
        self._dn_enabled = True
        self._dn_timer   = 0.0
        self._dn_period  = 8*60      # 8-min real-time cycle
        self.dn_opacity  = 0.0

    def _load_img(self, root: str, name: str, alpha=True) -> Surface:
        for ext in ("png", "jpg", "jpeg"):
            path = os.path.join(root, f"{name}.{ext}")
            if os.path.exists(path):
                img = pygame.image.load(path)
                return img.convert_alpha() if alpha else img.convert()
        # fall-back 1×1 surface
        surf = pygame.Surface((1, 1),
                              pygame.SRCALPHA if alpha else 0)
        surf.fill((200, 200, 200, 180) if alpha else (200, 200, 200))
        return surf

    def _load_assets(self):
        root = os.path.join(os.path.dirname(__file__), "images")
        self.desert  = self._load_img(root, "desert",  alpha=False)
        self.plant   = self._load_img(root, "plant")
        self.pond    = self._load_img(root, "pond")
        self.jeep    = self._load_img(root, "jeep")
        self.ranger  = self._load_img(root, "ranger")
        self.poacher = self._load_img(root, "poacher")
        self.animals   = [
            self._load_img(root,"carnivores/hyena"),
            self._load_img(root,"carnivores/lion"),
            self._load_img(root,"carnivores/tiger"),
            self._load_img(root,"herbivores/buffalo"),
            self._load_img(root,"herbivores/elephant"),
            self._load_img(root,"herbivores/giraffe"),
            self._load_img(root,"herbivores/hippo"),
            self._load_img(root,"herbivores/zebra")
        ]

    # -------------------- external API ------------------------
    def follow(self, world_pos: Vector2):
        """Update the camera so the supplied world-coordinate is centred."""
        self.cam.update(world_pos)

    def update_day_night(self, dt: float):
        if not self._dn_enabled:
            return
        self._dn_timer = (self._dn_timer + dt) % self._dn_period
        t = self._dn_timer
        if   t < 270: self.dn_opacity = 0.0
        elif t < 300: self.dn_opacity = (t - 270) / 30
        elif t < 450: self.dn_opacity = 1.0
        else:         self.dn_opacity = 1.0 - ((t - 450) / 30)

    # -------------------- render ------------------------------
    def render(self, screen: Surface, rect: Rect):
        if self.board.width == 0 or self.board.height == 0:
            return

        # compute tile size that fits **at least** the rect height & width
        cols_v = rect.width  // self.tile
        rows_v = rect.height // self.tile
        self.tile = max(4, min(self.tile, rect.width // cols_v, rect.height // rows_v))

        side = self.tile
        half_w_tiles = rect.width  // (2 * side)
        half_h_tiles = rect.height // (2 * side)

        # world coords visible
        min_x = int(self.cam.x) - half_w_tiles - 1
        min_y = int(self.cam.y) - half_h_tiles - 1
        max_x = int(self.cam.x) + half_w_tiles + 2
        max_y = int(self.cam.y) + half_h_tiles + 2

        # top-left pixel on screen that corresponds to (min_x,min_y)
        ox = rect.x + (rect.width  // 2) - int((self.cam.x - min_x) * side)
        oy = rect.y + (rect.height // 2) - int((self.cam.y - min_y) * side)

        # ---------- background desert (big blit is fastest) ----
        vis_cols = max_x - min_x
        vis_rows = max_y - min_y
        desert_scaled = pygame.transform.scale(self.desert,
                                               (vis_cols * side,
                                                vis_rows * side))
        screen.blit(desert_scaled, (ox, oy))

        # ---------- draw road tiles ----------------------------
        road_col = (105, 105, 105)
        for r in self.board.roads:          # type: Road
            if not (min_x <= r.pos.x < max_x and min_y <= r.pos.y < max_y):
                continue
            px = ox + int((r.pos.x - min_x) * side)
            py = oy + int((r.pos.y - min_y) * side)
            pygame.draw.rect(screen, road_col, (px, py, side, side))

        # ---------- ponds / plants -----------------------------
        pw, ph = side, side
        for pond in self.board.ponds:
            loc = pond.location
            if not (min_x-1 <= loc.x < max_x+1 and min_y-1 <= loc.y < max_y+1):
                continue
            px = ox + int((loc.x - min_x) * side)
            py = oy + int((loc.y - min_y) * side)
            screen.blit(pygame.transform.scale(self.pond, (pw, ph)),
                        (px, py))

        gw, gh = side, int(side * 1.2)
        for plant in self.board.plants:
            loc = plant.location
            if not (min_x-1 <= loc.x < max_x+1 and min_y-1 <= loc.y < max_y+1):
                continue
            px = ox + int((loc.x - min_x) * side)
            py = oy + int((loc.y - min_y) * side - (gh - side))
            screen.blit(pygame.transform.scale(self.plant, (gw, gh)),
                        (px, py))
            
        # ---------- animals -----------------------------
        aw, ah = side, side
        for animal in self.board.animals:
            loc = getattr(animal, "position", Vector2(0,0))
            px = ox + int((loc.x - min_x) * side)
            py = oy + int((loc.y - min_y) * side)
            screen.blit(pygame.transform.scale(self.animals[animal.species], (aw, ah)),
                        (px, py))

        # ---------- jeeps (2×2) --------------------------------
        jw = jh = side * 2
        for jeep in self.board.jeeps:
            c = jeep.position  # centre of jeep in world coords
            if not (min_x - 2 <= c.x < max_x + 2 and min_y - 2 <= c.y < max_y + 2):
                continue
            # top-left pixel so the jeep is centred on (c.x,c.y)
            px = ox + int((c.x - min_x) * side - jw / 2)
            py = oy + int((c.y - min_y) * side - jh / 2)
            screen.blit(pygame.transform.scale(self.jeep, (jw, jh)), (px, py))

        # ---------- rangers / poachers -------------------------
        for entity, img in (
            (self.board.rangers,  self.ranger),
            (self.board.poachers, self.poacher)
        ):
            for e in entity:
                loc = e.position
                if not (min_x-1 <= loc.x < max_x+1 and min_y-1 <= loc.y < max_y+1):
                    continue
                px = ox + int((loc.x - min_x) * side)
                py = oy + int((loc.y - min_y) * side)
                screen.blit(pygame.transform.scale(img, (side, side)),
                            (px, py))

        # ---------- grid ---------------------------------------
        grid_col = (80, 80, 80)

        for c in range(vis_cols + 1):
            x = ox + c * side
            pygame.draw.line(screen, grid_col,
                             (x, oy),
                             (x, oy + vis_rows * side), 1)
        for r in range(vis_rows + 1):
            y = oy + r * side
            pygame.draw.line(screen, grid_col,
                             (ox, y),
                             (ox + vis_cols * side, y), 1)

        # ---------- day / night tint ---------------------------
        if self.dn_opacity > 0.0:
            tint = self._lerp((255, 255, 255, 0),
                              (0, 0, 70, 160),
                              self.dn_opacity)
            ov = pygame.Surface((vis_cols * side, vis_rows * side),
                                pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))
