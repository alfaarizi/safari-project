from __future__ import annotations
import os
from typing import Tuple

import pygame
from pygame import Surface, Rect

from my_safari_project.model.board import Board
from my_safari_project.model.road  import Road


class BoardGUI:
    # ------------------------------------------------ static helpers
    @staticmethod
    def _lerp(c1: Tuple[int, int, int, int],
              c2: Tuple[int, int, int, int],
              t: float) -> Tuple[int, int, int, int]:
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    # ------------------------------------------------ ctor / assets
    def __init__(self, board: Board):
        self.board = board
        self.tile  = 32   # will be recalculated each frame

        self._load_assets()

        # day / night
        self._dn_enabled = True
        self._dn_timer   = 0.0          # seconds
        self._dn_period  = 8 * 60       # 8-min real-time cycle
        self.dn_opacity  = 0.0

    def _load_img(self, root: str, name: str, alpha=True) -> Surface:
        for ext in ("png", "jpg", "jpeg"):
            path = os.path.join(root, f"{name}.{ext}")
            if os.path.exists(path):
                surf = pygame.image.load(path)
                return surf.convert_alpha() if alpha else surf.convert()
        # 1 × 1 fall-back
        s = pygame.Surface((1, 1),
                           pygame.SRCALPHA if alpha else 0)
        s.fill((200, 200, 200, 180) if alpha else (200, 200, 200))
        return s

    def _load_assets(self):
        root = os.path.join(os.path.dirname(__file__), "images")
        self.desert  = self._load_img(root, "desert",  alpha=False)
        self.plant   = self._load_img(root, "plant")
        self.pond    = self._load_img(root, "pond")
        self.jeep    = self._load_img(root, "jeep")
        self.ranger  = self._load_img(root, "ranger")
        self.poacher = self._load_img(root, "poacher")

    # ------------------------------------------------ public helpers

    def update_day_night(self, dt):
        self._dn_timer = (self._dn_timer + dt) % self._dn_period
        t = self._dn_timer
        if t < 270:
            self.dn_opacity = 0.0
        elif t < 300:
            self.dn_opacity = (t - 270) / 30
        elif t < 450:
            self.dn_opacity = 1.0
        else:
            self.dn_opacity = 1.0 - ((t - 450) / 30)

    # ------------------------------------------------ main render
    def render(self, screen: Surface, rect: Rect):
        x0, y0, w, h = rect
        cols, rows   = self.board.width, self.board.height
        if cols <= 0 or rows <= 0:
            return

        # keep tiles square and as large as possible
        self.tile = side = max(4, min(w // cols, h // rows))

        BW, BH = cols * side, rows * side
        ox = x0 + (w - BW) // 2
        oy = y0 + (h - BH) // 2

        # 1 – desert bg
        screen.blit(pygame.transform.scale(self.desert, (BW, BH)), (ox, oy))

        # 2 – roads (each Road.pos is the *top-left* cell of that road tile)
        road_colour = (105, 105, 105)
        for r in self.board.roads:           # type: Road
            px = ox + int(r.pos.x * side)
            py = oy + int(r.pos.y * side)
            pygame.draw.rect(screen, road_colour,
                             (px, py, side, side))

        # 3 – ponds (1.5 × 1.2)
        pw, ph = int(side * 1.5), int(side * 1.2)
        for pond in self.board.ponds:
            loc = pond.location
            screen.blit(pygame.transform.scale(self.pond, (pw, ph)),
                        (ox + int(loc.x * side),
                         oy + int(loc.y * side)))

        # 4 – plants (1.0 × 1.2, bottom-aligned)
        gw, gh = side, int(side * 1.2)
        for plant in self.board.plants:
            loc = plant.location
            px = ox + int(loc.x * side)
            py = oy + int(loc.y * side - (gh - side))
            screen.blit(pygame.transform.scale(self.plant, (gw, gh)), (px, py))

        # 5 – jeeps (2 × 2 cells, centred on path centre)
        JW = JH = side * 2
        for jeep in self.board.jeeps:
            center = jeep.position            # already *centre of tile*
            jx = ox + int(center.x * side - side)
            jy = oy + int(center.y * side - side)
            screen.blit(pygame.transform.scale(self.jeep, (JW, JH)),
                        (jx, jy))

        # 6 – rangers / poachers (1 × 1)
        for ranger in self.board.rangers:
            loc = ranger.position
            screen.blit(pygame.transform.scale(self.ranger, (side, side)),
                        (ox + int(loc.x * side),
                         oy + int(loc.y * side)))
        for po in self.board.poachers:
            loc = po.position
            screen.blit(pygame.transform.scale(self.poacher, (side, side)),
                        (ox + int(loc.x * side),
                         oy + int(loc.y * side)))

        # 7 – thin grid & border
        pygame.draw.rect(screen, (128, 128, 128), (ox, oy, BW, BH), 2)
        for c in range(cols + 1):
            pygame.draw.line(screen, (0, 0, 0),
                             (ox + c * side, oy),
                             (ox + c * side, oy + BH), 1)
        for r in range(rows + 1):
            pygame.draw.line(screen, (0, 0, 0),
                             (ox, oy + r * side),
                             (ox + BW, oy + r * side), 1)

        # 8 – day/night overlay
        if self.dn_opacity > 0.0:
            tint = self._lerp((255, 255, 255, 0),
                              (0, 0, 70, 160),
                              self.dn_opacity)
            ov = pygame.Surface((BW, BH), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))
