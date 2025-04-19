import os
import pygame
from pygame import Surface
from pygame.math import Vector2
from typing import Dict, Any, Tuple, List

from my_safari_project.model.board import Board

class BoardGUI:
    """
    Renders the safari board into a given Rect:
      - Desert background stretched to fill the board area
      - Plants (scaled to 1×tileW × 1.2×tileH, bottom‑aligned)
      - Ponds  (scaled to 1.5×tileW × 1.2×tileH)
      - Jeeps  (1×tileW × 0.5×tileH)
      - Rangers & Poachers (1×tileW × 1×tileH)
      - Roads  (lines connecting their points)
      - Day/night overlay with proper timing
    """

    @staticmethod
    def _lerp_color(c1: Tuple[int,int,int,int], c2: Tuple[int,int,int,int], t: float) -> Tuple[int,int,int,int]:
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
            int(c1[3] + (c2[3] - c1[3]) * t),
        )

    def __init__(
        self,
        board: Board,
        tileW: int = 64,
        tileH: int = 64,
        isometric: bool = False,
    ):
        self.board           = board
        self.tileW           = tileW
        self.tileH           = tileH
        self.isometric       = isometric

        # Day/night cycle
        self._day_night_enabled = True
        self._day_night_timer   = 0.0
        self._total_cycle_time  = 8 * 60
        self.dayNightOpacity    = 0.0

        # Sprites
        self.desert_img    : Surface = None
        self.plant_img     : Surface = None
        self.pond_img      : Surface = None
        self.jeep_img      : Surface = None
        self.ranger_img    : Surface = None
        self.poacher_img   : Surface = None

        # Load all images once
        self._load_assets()

    def _load_assets(self) -> None:
        base = os.path.dirname(__file__)
        imgs = os.path.join(base, "images")

        def load(name: str, alpha: bool=True) -> Surface:
            for ext in ("png","jpeg","jpg"):
                path = os.path.join(imgs, f"{name}.{ext}")
                if os.path.exists(path):
                    img = pygame.image.load(path)
                    return img.convert_alpha() if alpha else img.convert()
            # fallback single‐tile placeholder
            surf = pygame.Surface(
                (self.tileW, self.tileH),
                flags=pygame.SRCALPHA if alpha else 0
            )
            surf.fill((200,200,200,180) if alpha else (200,200,200))
            return surf

        self.desert_img    = load("desert",  alpha=False)
        self.plant_img     = load("plant",   alpha=True)
        self.pond_img      = load("pond",    alpha=True)
        self.jeep_img      = load("jeep",    alpha=True)
        self.ranger_img    = load("ranger",  alpha=True)
        self.poacher_img   = load("poacher", alpha=True)

    def render(self, screen: Surface, board_rect: pygame.Rect) -> None:
        """
        Draw everything into board_rect = (x0,y0,width,height).
        """
        x0,y0,w,h = board_rect
        cols, rows = self.board.width, self.board.height

        # Recompute per‐cell size
        side = min(w//cols, h//rows)
        if side < 4:
            return
        self.tileW = self.tileH = side

        # 1) Desert background
        if self.desert_img:
            bg = pygame.transform.scale(self.desert_img, (cols*side, rows*side))
            screen.blit(bg, (x0, y0))
        else:
            pygame.draw.rect(screen, (255,255,153), (x0,y0,cols*side,rows*side))

        # 2) Border & grid
        pygame.draw.rect(screen, (128,128,128), (x0,y0,cols*side,rows*side), 2)
        for i in range(cols+1):
            xx = x0 + i*side
            pygame.draw.line(screen, (0,0,0), (xx,y0), (xx,y0+rows*side), 1)
        for j in range(rows+1):
            yy = y0 + j*side
            pygame.draw.line(screen, (0,0,0), (x0,yy), (x0+cols*side,yy), 1)

        # 3) Ponds (1.5×W ×1.2×H)
        pw, ph = int(side*1.5), int(side*1.2)
        for pond in self.board.ponds:
            loc = getattr(pond, "location", Vector2(0,0))
            surf = pygame.transform.scale(self.pond_img, (pw, ph))
            screen.blit(surf, (x0+int(loc.x*side), y0+int(loc.y*side)))

        # 4) Plants (1×W ×1.2×H, bottom‐aligned)
        gw, gh = side, int(side*1.2)
        for plant in self.board.plants:
            loc = getattr(plant, "location", Vector2(0,0))
            surf = pygame.transform.scale(self.plant_img, (gw, gh))
            px = x0 + int(loc.x*side)
            py = y0 + int(loc.y*side - (gh-side))
            screen.blit(surf, (px, py))

        # 5) Jeeps (1×W ×0.5×H)
        jw, jh = side, side//2
        for jeep in self.board.jeeps:
            loc = getattr(jeep, "location", Vector2(0,0))
            surf = pygame.transform.scale(self.jeep_img, (jw, jh))
            screen.blit(surf, (x0+int(loc.x*side), y0+int(loc.y*side)))

        # 6) Rangers & Poachers (1×W ×1×H)
        rw, rh = side, side
        for ranger in self.board.rangers:
            loc = getattr(ranger, "position",   Vector2(0,0))
            surf = pygame.transform.scale(self.ranger_img, (rw, rh))
            screen.blit(surf, (x0+int(loc.x*side), y0+int(loc.y*side)))
        for poacher in self.board.poachers:
            loc = getattr(poacher, "position", Vector2(0,0))
            surf = pygame.transform.scale(self.poacher_img, (rw, rh))
            screen.blit(surf, (x0+int(loc.x*side), y0+int(loc.y*side)))

        # 7) Roads
        for road in self.board.roads:
            pts = []
            for p in getattr(road, "points", []):
                pts.append((x0+int(p.x*side+side//2), y0+int(p.y*side+side//2)))
            if len(pts) >= 2:
                pygame.draw.lines(screen, (105,105,105), False, pts, 4)

        # 8) Day/night overlay
        if self._day_night_enabled and self.dayNightOpacity > 0.0:
            dayc   = (255,255,255,0)
            nightc = (0,0,70,160)
            tint   = BoardGUI._lerp_color(dayc, nightc, self.dayNightOpacity)
            overlay = pygame.Surface((cols*side, rows*side), pygame.SRCALPHA)
            overlay.fill(tint)
            screen.blit(overlay, (x0,y0))


    def update_day_night(self, dt: float) -> None:
        if not self._day_night_enabled:
            return
        self._day_night_timer += dt
        if self._day_night_timer > self._total_cycle_time:
            self._day_night_timer -= self._total_cycle_time

        t = self._day_night_timer
        if   t < 270: self.dayNightOpacity = 0.0
        elif t < 300: self.dayNightOpacity = (t-270)/30.0
        elif t < 450: self.dayNightOpacity = 1.0
        else:          self.dayNightOpacity = 1.0 - ((t-450)/30.0)
