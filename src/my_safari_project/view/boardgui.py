import os
from typing import Tuple
import pygame
from pygame import Surface
from pygame.math import Vector2
from my_safari_project.model.board import Board


class BoardGUI:
    """Renders Board into a supplied Rect."""

    # ---------- helpers --------------------------------------------------
    @staticmethod
    def _lerp(c1: Tuple[int, int, int, int],
              c2: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    def __init__(self, board: Board, tile=32):
        self.board = board
        self.tile = tile          # will be recalculated each frame
        self._load_images()

        # day / night
        self._dn_enabled = True
        self._dn_timer = 0.0        # seconds
        self._dn_period = 8 * 60    # 8 min = 5 day + 3 night – same as before
        self.dn_opacity = 0.0

    # ---------- asset loading -------------------------------------------
    def _load_img(self, root: str, name: str, alpha=True) -> Surface:
        for ext in ("png", "jpg", "jpeg"):
            path = os.path.join(root, f"{name}.{ext}")
            if os.path.exists(path):
                img = pygame.image.load(path)
                return img.convert_alpha() if alpha else img.convert()
        s = pygame.Surface((self.tile, self.tile),
                           pygame.SRCALPHA if alpha else 0)
        s.fill((200, 200, 200, 180) if alpha else (200, 200, 200))
        return s

    def _load_images(self):
        base = os.path.dirname(__file__)
        imgs = os.path.join(base, "images")
        self.desert = self._load_img(imgs, "desert", alpha=False)
        self.plant  = self._load_img(imgs, "plant")
        self.pond   = self._load_img(imgs, "pond")
        self.jeep   = self._load_img(imgs, "jeep")
        self.ranger = self._load_img(imgs, "ranger")
        self.poacher = self._load_img(imgs, "poacher")

    # ---------- public API ----------------------------------------------
    def update_day_night(self, dt: float):
        if not self._dn_enabled:
            return
        self._dn_timer = (self._dn_timer + dt) % self._dn_period
        t = self._dn_timer
        if t < 270:
            self.dn_opacity = 0.0            # pure day
        elif t < 300:
            self.dn_opacity = (t - 270) / 30  # dusk
        elif t < 450:
            self.dn_opacity = 1.0            # night
        else:
            self.dn_opacity = 1 - ((t - 450) / 30)  # dawn

    def render(self, screen: Surface, rect: pygame.Rect):
        x0, y0, w, h = rect
        cols, rows = self.board.width, self.board.height

        # keep square tiles
        self.tile = side = max(4, min(w // cols, h // rows))
        BW, BH = cols * side, rows * side
        ox = x0 + (w - BW) // 2
        oy = y0 + (h - BH) // 2

        # 1- desert
        bg = pygame.transform.scale(self.desert, (BW, BH))
        screen.blit(bg, (ox, oy))

        # 2- roads ---------------------------------------------------------
        road_col = (105, 105, 105)
        road_thk = side * 2

        for road in self.board.roads:
            if hasattr(road, "points") and road.points and len(road.points) >= 2:
                # cell list -> draw filled rect per cell so it’s very visible
                for p in road.points:
                    cx, cy = int(p.x), int(p.y)
                    pygame.draw.rect(screen, road_col,
                                     (ox + cx * side, oy + cy * side,
                                      side, side))
            else:
                sp = getattr(road, "start_point", None)
                ep = getattr(road, "end_point", None)
                if sp is None or ep is None:
                    continue
                x1 = ox + int(sp[0] * side + side / 2)
                y1 = oy + int(sp[1] * side + side / 2)
                x2 = ox + int(ep[0] * side + side / 2)
                y2 = oy + int(ep[1] * side + side / 2)
                pygame.draw.line(screen, road_col, (x1, y1), (x2, y2), road_thk)

        # 3- ponds ---------------------------------------------------------
        PW, PH = int(side * 1.5), int(side * 1.2)
        for pond in self.board.ponds:
            loc = getattr(pond, "location", Vector2(0, 0))
            screen.blit(pygame.transform.scale(self.pond, (PW, PH)),
                        (ox + int(loc.x * side), oy + int(loc.y * side)))

        # 4- plants --------------------------------------------------------
        GW, GH = side, int(side * 1.2)
        for plant in self.board.plants:
            loc = getattr(plant, "location", Vector2(0, 0))
            px = ox + int(loc.x * side)
            py = oy + int(loc.y * side - (GH - side))
            screen.blit(pygame.transform.scale(self.plant, (GW, GH)), (px, py))

        # 5- jeeps (2×2) ---------------------------------------------------
        JW = JH = side * 2
        for jeep in self.board.jeeps:
            loc = getattr(jeep, "position", Vector2(0, 0))
            jx = ox + int(loc.x * side - side / 2)
            jy = oy + int(loc.y * side - side / 2)
            screen.blit(pygame.transform.scale(self.jeep, (JW, JH)), (jx, jy))

        # 6- rangers / poachers -------------------------------------------
        for r in self.board.rangers:
            loc = getattr(r, "position", Vector2(0, 0))
            screen.blit(pygame.transform.scale(self.ranger, (side, side)),
                        (ox + int(loc.x * side), oy + int(loc.y * side)))
        for p in self.board.poachers:
            loc = getattr(p, "position", Vector2(0, 0))
            screen.blit(pygame.transform.scale(self.poacher, (side, side)),
                        (ox + int(loc.x * side), oy + int(loc.y * side)))

        # 7- grid + border -------------------------------------------------
        pygame.draw.rect(screen, (128, 128, 128), (ox, oy, BW, BH), 2)
        for c in range(cols + 1):
            pygame.draw.line(screen, (0, 0, 0),
                             (ox + c * side, oy),
                             (ox + c * side, oy + BH), 1)
        for r in range(rows + 1):
            pygame.draw.line(screen, (0, 0, 0),
                             (ox, oy + r * side),
                             (ox + BW, oy + r * side), 1)

        # 8- day / night tint ---------------------------------------------
        if self.dn_opacity > 0:
            tint = self._lerp((255, 255, 255, 0), (0, 0, 70, 160), self.dn_opacity)
            ov = pygame.Surface((BW, BH), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))
