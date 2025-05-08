# my_safari_project/view/boardgui.py
from __future__ import annotations
import os
import pygame
from pygame import Surface, Rect
from pygame.math import Vector2
from typing import Tuple

from my_safari_project.model.board import Board
from my_safari_project.model.road  import Road

class BoardGUI:
    """Renders a portion of the Board, with support for zoom and drag."""

    def __init__(self, board: Board, default_tile: int = 32):
        self.board = board
        self.tile  = default_tile           # pixel size of one cell

        # camera centre (world‐coordinate of tile‐centre)
        self.cam = Vector2(board.entrance) + Vector2(0.5, 0.5)

        # load assets
        self._load_assets()

        # day/night
        self._dn_enabled = True
        self._dn_timer   = 0.0
        self._dn_period  = 8 * 60    # 8 min real‐time
        self.dn_opacity  = 0.0

        # dragging state
        self._dragging    = False
        self._drag_start  = Vector2(0, 0)
        self._cam_at_drag = Vector2(self.cam)

    # ─── asset loading ──────────────────────────────────────────────────────
    def _load_img(self, root: str, name: str, alpha=True) -> Surface:
        for ext in ("png", "jpg", "jpeg"):
            path = os.path.join(root, f"{name}.{ext}")
            if os.path.exists(path):
                img = pygame.image.load(path)
                return img.convert_alpha() if alpha else img.convert()
        surf = pygame.Surface((1, 1),
                              pygame.SRCALPHA if alpha else 0)
        surf.fill((200,200,200,180) if alpha else (200,200,200))
        return surf

    def _load_assets(self):
        base = os.path.dirname(__file__)
        imgs = os.path.join(base, "images")
        self.desert  = self._load_img(imgs, "desert", alpha=False)
        self.plant   = self._load_img(imgs, "plant")
        self.pond    = self._load_img(imgs, "pond")
        self.jeep    = self._load_img(imgs, "jeep")
        self.ranger  = self._load_img(imgs, "ranger")
        self.poacher = self._load_img(imgs, "poacher")
        self.animals = {
        "hyena"   : self._load_img(imgs, "carnivores/hyena"),
        "lion"    : self._load_img(imgs, "carnivores/lion"),
        "tiger"   : self._load_img(imgs, "carnivores/tiger"),
        "buffalo" : self._load_img(imgs, "herbivores/buffalo"),
        "elephant": self._load_img(imgs, "herbivores/elephant"),
        "giraffe" : self._load_img(imgs, "herbivores/giraffe"),
        "hippo"   : self._load_img(imgs, "herbivores/hippo"),
        "zebra"   : self._load_img(imgs, "herbivores/zebra"),}

    # ─── camera controls (panning & zooming) ────────────────────────────────
    def follow(self, world_pos: Vector2):
        """Centre the camera on the given world‐coordinate."""
        self.cam = Vector2(world_pos)

    def start_drag(self, mouse_pos: Vector2):
        """Begin click‐and‐drag panning."""
        self._dragging    = True
        self._drag_start  = Vector2(mouse_pos)
        self._cam_at_drag = Vector2(self.cam)

    def drag(self, mouse_pos: Vector2, board_rect: Rect):
        """Continue panning; convert mouse‐delta into world‐units."""
        if not self._dragging:
            return
        delta_px = Vector2(mouse_pos) - self._drag_start
        # each pixel = 1/tile world‐unit
        world_delta = delta_px / self.tile
        # invert so dragging moves world in same direction as cursor
        self.cam = self._cam_at_drag - world_delta

    def stop_drag(self):
        """End panning."""
        self._dragging = False

    def zoom(self, direction: int, mouse_pos: Vector2, board_rect: Rect):
        """
        Zoom in (+1) or out (–1).  Zooms relative to mouse_pos.
        """
        old_tile = self.tile
        # adjust tile size
        self.tile = max(4, min(64, self.tile + direction * 4))
        # to keep the point under the cursor stationary, adjust cam:
        mx, my = mouse_pos
        if not board_rect.collidepoint(mouse_pos):
            return

        # compute world‐coords under mouse before and after zoom:
        cols = board_rect.width  // old_tile
        rows = board_rect.height // old_tile
        half_w = cols/2; half_h = rows/2

        # world‐pos of mouse under old zoom:
        wx_old = self.cam.x + (mx - board_rect.centerx) / old_tile
        wy_old = self.cam.y + (my - board_rect.centery) / old_tile
        # same under new zoom:
        wx_new = self.cam.x + (mx - board_rect.centerx) / self.tile
        wy_new = self.cam.y + (my - board_rect.centery) / self.tile

        # shift cam so the world‐point stays fixed:
        self.cam.x += wx_old - wx_new
        self.cam.y += wy_old - wy_new

    # ─── day/night ─────────────────────────────────────────────────────────
    def update_day_night(self, dt: float):
        if not self._dn_enabled:
            return
        self._dn_timer = (self._dn_timer + dt) % self._dn_period
        t = self._dn_timer
        if   t < 270:            self.dn_opacity = 0.0
        elif t < 300:            self.dn_opacity = (t-270)/30
        elif t < 450:            self.dn_opacity = 1.0
        else:                    self.dn_opacity = 1 - ((t-450)/30)

    # ─── rendering ─────────────────────────────────────────────────────────
    @staticmethod
    def _lerp(c1: Tuple[int,int,int,int],
              c2: Tuple[int,int,int,int], t: float) -> Tuple[int,int,int,int]:
        return tuple(int(a + (b-a)*t) for a,b in zip(c1, c2))

    # def render(self, screen: Surface, rect: Rect):
    #     if self.board.width == 0 or self.board.height == 0:
    #         return
    def render(
        self,
        screen: Surface,
        rect: Rect,
        hover_tile: Vector2 | None = None,
        hover_valid: bool = False,
        ):
        if self.board.width == 0 or self.board.height == 0:
            return

        # keep tile size within reasonable bounds to fit the viewport
        cols = max(1, rect.width  // self.tile)
        rows = max(1, rect.height // self.tile)
        self.tile = max(4, min(self.tile,
                              rect.width  // cols,
                              rect.height // rows))
        side = self.tile

        # how many tiles to each side of the camera
        half_w = rect.width  // (2*side)
        half_h = rect.height // (2*side)

        # world‐bounds shown
        min_x = int(self.cam.x) - half_w - 1
        min_y = int(self.cam.y) - half_h - 1
        max_x = int(self.cam.x) + half_w + 2
        max_y = int(self.cam.y) + half_h + 2

        # origin pixel for (min_x,min_y)
        ox = rect.x + rect.width//2  - int((self.cam.x - min_x)*side)
        oy = rect.y + rect.height//2 - int((self.cam.y - min_y)*side)

        # background desert
        vis_w = max_x - min_x
        vis_h = max_y - min_y
        bg = pygame.transform.scale(self.desert, (vis_w*side, vis_h*side))
        screen.blit(bg, (ox, oy))

        # roads
        road_col, th = (105,105,105), side
        for r in self.board.roads:
            if not (min_x <= r.pos.x < max_x and min_y <= r.pos.y < max_y):
                continue
            px = ox + int((r.pos.x - min_x)*side)
            py = oy + int((r.pos.y - min_y)*side)
            pygame.draw.rect(screen, road_col, (px, py, side, side))

        # ponds
        for p in self.board.ponds:
            x, y = p.location
            if not (min_x <= x < max_x and min_y <= y < max_y): continue
            px = ox + int((x - min_x)*side)
            py = oy + int((y - min_y)*side)
            screen.blit(pygame.transform.scale(self.pond, (side, side)), (px, py))

        # plants
        gw, gh = side, int(side*1.2)
        for p in self.board.plants:
            x, y = p.location
            if not (min_x <= x < max_x and min_y <= y < max_y): continue
            px = ox + int((x - min_x)*side)
            py = oy + int((y - min_y)*side - (gh-side))
            screen.blit(pygame.transform.scale(self.plant, (gw, gh)), (px, py))

        # ---------- jeeps (2×2) --------------------------------
        jw = jh = side * 2
        for j in self.board.jeeps:
            cx, cy = j.position
            if not (min_x - 2 <= cx < max_x + 2 and min_y - 2 <= cy < max_y + 2):
                continue

            px = ox + int((cx - min_x) * side)
            py = oy + int((cy - min_y) * side)

            angle = getattr(j, "heading", 0.0)

            rotated = pygame.transform.rotate(self.jeep,  angle)
            scaled = pygame.transform.scale(rotated, (jw, jh))

            rect = scaled.get_rect(center=(px, py))
            screen.blit(scaled, rect.topleft)

        # rangers
        for r in self.board.rangers:
            rx, ry = r.position
            if not (min_x <= rx < max_x and min_y <= ry < max_y):
                continue
            px = ox + int((rx - min_x)*side)
            py = oy + int((ry - min_y)*side)
            screen.blit(pygame.transform.scale(self.ranger, (side, side)), (px, py))

        # poachers (only visible if any ranger can see them)
        for p in self.board.poachers:
            if any(p.is_visible_to(r) for r in self.board.rangers):
                px = ox + int((p.position.x - min_x)*side)
                py = oy + int((p.position.y - min_y)*side)
                screen.blit(pygame.transform.scale(self.poacher, (side, side)), (px, py))
                # ---------- animals -------------------------------------------------
        aw = ah = side
        for a in self.board.animals:
            pos = getattr(a, "position", Vector2(0, 0))
            if not (min_x <= pos.x < max_x and min_y <= pos.y < max_y):
                continue
            sprite = self.animals.get(a.species.name.lower())      # enum → "lion", "giraffe", …
            if sprite is None:
                continue
            px = ox + int((pos.x - min_x) * side)
            py = oy + int((pos.y - min_y) * side)
            screen.blit(pygame.transform.scale(sprite, (aw, ah)), (px, py))


        # grid
        grid_col = (80,80,80)
        for c in range(vis_w+1):
            x = ox + c*side
            pygame.draw.line(screen, grid_col, (x,oy), (x,oy+vis_h*side), 1)
        for r in range(vis_h+1):
            y = oy + r*side
            pygame.draw.line(screen, grid_col, (ox,y), (ox+vis_w*side,y), 1)

        if hover_tile is not None:
            hx, hy = int(hover_tile.x), int(hover_tile.y)
            if min_x <= hx < max_x and min_y <= hy < max_y:
                px = ox + int((hx - min_x) * side)
                py = oy + int((hy - min_y) * side)
                colour = (0, 180, 0, 120) if hover_valid else (180, 0, 0, 120)
                overlay = pygame.Surface((side, side), pygame.SRCALPHA)
                overlay.fill(colour)
                screen.blit(overlay, (px, py))
        # day/night tint
        if self.dn_opacity > 0.0:
            tint = self._lerp((255,255,255,0), (0,0,70,160), self.dn_opacity)
            ov   = pygame.Surface((vis_w*side, vis_h*side), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))



            #----converting pixel to tile 
    def screen_to_tile(self, screen_pos: tuple[int,int], board_rect: Rect) -> Vector2|None:
                """the integer tile under a screen pixel will be returned, or None if off‑board area."""
                sx, sy = screen_pos
                if not board_rect.collidepoint(sx, sy):
                    return None
                side = self.tile
                cols = board_rect.width  // side
                rows = board_rect.height // side
                half_w = cols//2; half_h = rows//2
                min_x = int(self.cam.x) - half_w - 1
                min_y = int(self.cam.y) - half_h - 1
                wx = min_x + (sx - board_rect.x) // side
                wy = min_y + (sy - board_rect.y) // side
                return Vector2(int(wx), int(wy))