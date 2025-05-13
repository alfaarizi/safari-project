# my_safari_project/view/boardgui.py
from __future__ import annotations

import os
import pygame
from pygame import Surface, Rect
from pygame.math import Vector2
from typing import Tuple
from pygame import Rect
from my_safari_project.model.board import Board
from my_safari_project.model.road  import Road



class BoardGUI:
    """Draws a *scroll‐ and zoom‐able* viewport of a Board instance."""
    MIN_TILE = 4
    MAX_TILE = 64

    def __init__(self, board: Board, default_tile: int = 32):
        self.board = board
        from my_safari_project.view.gamegui import BOARD_RECT, SCREEN_W, SCREEN_H

        if default_tile is not None:
            self.tile = default_tile
        else:
            # fall back to the “fit‐to‐screen” logic
            self.tile = min(
                BOARD_RECT.width  // board.width,
                BOARD_RECT.height // board.height
            )
        self.tile = max(self.MIN_TILE, self.tile)

        # Position camera to show entire board
        self.cam = Vector2(
            (board.width - 1) / 2,  # Center X
            (board.height - 1) / 2  # Center Y
        )

        # Set viewport boundaries
        self.min_x = 0
        self.max_x = board.width - 1
        self.min_y = 0
        self.max_y = board.height - 1

        # --- day/night ---------------------------------------------------
        self._dn_enabled = True
        self._dn_timer = 0.0
        self._dn_period = 8 * 60
        self.dn_opacity = 0.0

        # --- dragging state ---------------------------------------------
        self._dragging = False
        self._drag_start = Vector2(0, 0)
        self._cam_at_drag = Vector2(self.cam)

        # --- load all images --------------------------------------------
        self._load_assets()
    

    # ─── asset loading ────────────────────────────────────────────────
    def _load_img(self, root: str, name: str, alpha=True) -> Surface:
        for ext in ("png", "jpg", "jpeg"):
            p = os.path.join(root, f"{name}.{ext}")
            if os.path.exists(p):
                img = pygame.image.load(p)
                return img.convert_alpha() if alpha else img.convert()
        surf = pygame.Surface((1,1),
                              pygame.SRCALPHA if alpha else 0)
        surf.fill((200,200,200,180) if alpha else (200,200,200))
        return surf

    def _load_assets(self):
        root = os.path.join(os.path.dirname(__file__), "images")
        self.desert  = self._load_img(root, "desert",  alpha=False)
        self.plant   = self._load_img(root, "plant")
        self.pond    = self._load_img(root, "pond")
        self.jeep    = self._load_img(root, "jeep")
        self.ranger  = self._load_img(root, "ranger")
        self.poacher = self._load_img(root, "poacher")
        self.animals = [
            self._load_img(root, "carnivores/hyena"),
            self._load_img(root, "carnivores/lion"),
            self._load_img(root, "carnivores/tiger"),
            self._load_img(root, "herbivores/buffalo"),
            self._load_img(root, "herbivores/elephant"),
            self._load_img(root, "herbivores/giraffe"),
            self._load_img(root, "herbivores/hippo"),
            self._load_img(root, "herbivores/zebra")
        ]


    # ─── camera controls (panning & zooming) ──────────────────────────
    def follow(self, world_pos: Vector2):
        """Centre the camera on the given world‐coordinate."""
        self.cam = Vector2(world_pos)

    def start_drag(self, mouse_pos: Vector2):
        """Begin click‐and‐drag panning."""
        self._dragging    = True
        self._drag_start  = Vector2(mouse_pos)
        self._cam_at_drag = Vector2(self.cam)

    def drag(self, pos: tuple[int, int], bounds: pygame.Rect) -> None:
        """Handle drag movement, keeping within board boundaries."""
        if not self._dragging:
            return

        offset = Vector2(pos) - self._drag_start
        new_cam = self._cam_at_drag - offset / self.tile

        # Clamp to board boundaries
        board_width = self.board.width
        board_height = self.board.height

        # Allow half-tile margin on each side
        new_cam.x = max(0.5, min(board_width - 0.5, new_cam.x))
        new_cam.y = max(0.5, min(board_height - 0.5, new_cam.y))

        self.cam = new_cam

    def stop_drag(self):
        """End panning without snapping back."""
        self._dragging = False

    def zoom(self, direction: int, mouse_pos: Vector2, board_rect: Rect):
        """
        Zoom in (+1) or out (–1), keeping the tile under the cursor fixed.
        """
        if not board_rect.collidepoint(mouse_pos):
            return
        old_tile = self.tile
        self.tile = max(self.MIN_TILE,   min(self.tile + direction * 4, self.MAX_TILE))
        if self.tile == old_tile:
            return

        mx, my = mouse_pos

        def world_at(px_per_tile: int) -> Vector2:
            return Vector2(
                self.cam.x + (mx - board_rect.centerx) / px_per_tile,
                self.cam.y + (my - board_rect.centery) / px_per_tile
            )

        w_old = world_at(old_tile)
        w_new = world_at(self.tile)
        # shift cam so that point stays put
        self.cam += w_old - w_new


    # ─── day / night tinting ──────────────────────────────────────────
    def update_day_night(self, dt: float):
        if not self._dn_enabled:
            return
        self._dn_timer = (self._dn_timer + dt) % self._dn_period
        t = self._dn_timer
        if   t < 270:   self.dn_opacity = 0.0
        elif t < 300:   self.dn_opacity = (t - 270) / 30
        elif t < 450:   self.dn_opacity = 1.0
        else:           self.dn_opacity = 1.0 - ((t - 450) / 30)


    # ─── rendering ─────────────────────────────────────────────────────
    @staticmethod
    def _lerp(c1: Tuple[int,int,int,int],
              c2: Tuple[int,int,int,int], t: float) -> Tuple[int,int,int,int]:
        return tuple(int(a + (b - a)*t) for a,b in zip(c1, c2))

    def render(self,screen: Surface,rect: Rect,*,hover_tile: Vector2 | None = None, 
        hover_valid: bool = False ) -> None:
        if self.board.width == 0 or self.board.height == 0:
            return

        # ensure at least 4×4 tiles fit in the view
        self.tile = max(4, min(self.tile,
                               rect.width  // 4,
                               rect.height // 4))
        side = self.tile

        # how many tiles in each direction from camera
        half_w = rect.width  // (2 * side)
        half_h = rect.height // (2 * side)

        # world‐bounds
        min_x = int(self.cam.x) - half_w - 1
        min_y = int(self.cam.y) - half_h - 1
        max_x = int(self.cam.x) + half_w + 2
        max_y = int(self.cam.y) + half_h + 2

        # pixel offset for (min_x, min_y)
        ox = rect.centerx - int((self.cam.x - min_x) * side)
        oy = rect.centery - int((self.cam.y - min_y) * side)

        vis_w = max_x - min_x
        vis_h = max_y - min_y

        # ---------- background desert ----------------------------
        bg = pygame.transform.scale(self.desert, (vis_w * side, vis_h * side))
        screen.blit(bg, (ox, oy))

        # ---------- roads ------------------------------------------
        road_col = (105, 105, 105)
        for rd in self.board.roads:  # type: Road
            if min_x <= rd.pos.x < max_x and min_y <= rd.pos.y < max_y:
                px = ox + int((rd.pos.x - min_x) * side)
                py = oy + int((rd.pos.y - min_y) * side)
                pygame.draw.rect(screen, road_col, (px, py, side, side))
        
        # Animal AI collision/detection
        if getattr(self.board.wildlife_ai.animal_ai, "debug_mode"):
            self.board.wildlife_ai.animal_ai.render(screen, ox, oy, side, min_x, min_y)

        # ---------- ponds ------------------------------------------
        for p in self.board.ponds:
            x, y = p.position
            if min_x <= x < max_x and min_y <= y < max_y:
                px = ox + int((x - min_x) * side)
                py = oy + int((y - min_y) * side)
                screen.blit(
                    pygame.transform.scale(self.pond, (side, side)),
                    (px, py)
                )

        # ---------- plants -----------------------------------------
        gw, gh = side, int(side * 1.2)
        for p in self.board.plants:
            x, y = p.position
            if min_x <= x < max_x and min_y <= y < max_y:
                px = ox + int((x - min_x) * side)
                py = oy + int((y - min_y) * side - (gh - side) ) 
                screen.blit(
                    pygame.transform.scale(self.plant, (gw, gh)),
                    (px, py)
                )
        
        # ---------- animals -----------------------------
        aw, ah = side, side
        for animal in self.board.animals:
            loc = getattr(animal, "position", Vector2(0,0))
            px = ox + int((loc.x - min_x) * side)
            py = oy + int((loc.y - min_y) * side)
            screen.blit(pygame.transform.scale(self.animals[animal.species.value], (aw, ah)), (px, py))

        # ---------- jeeps (2×2) ------------------------------------
        jw = jh = side * 2
        for j in self.board.jeeps:
            cx, cy = j.position
            if (min_x - 2) <= cx < (max_x + 2) and (min_y - 2) <= cy < (max_y + 2):
                # rotate & scale
                img = pygame.transform.scale(self.jeep, (jw, jh))
                # pygame.rotate is CCW; our heading is +° CCW
                img = pygame.transform.rotate(img, -j.heading)
                r = img.get_rect(center=(0,0))
                px = ox + int((cx - min_x)*side - r.width / 2)
                py = oy + int((cy - min_y)*side - r.height / 2)
                screen.blit(img, (px, py))

        # ---------- rangers ----------------------------------------
        for r in self.board.rangers:
            rx, ry = r.position
            if min_x <= rx < max_x and min_y <= ry < max_y:
                px = ox + int((rx - min_x)*side)
                py = oy + int((ry - min_y)*side)
                screen.blit(
                    pygame.transform.scale(self.ranger, (side, side)),
                    (px, py)
                )

        # ---------- poachers (only if visible) ---------------------
        for p in self.board.poachers:
            if any(p.is_visible_to(r) for r in self.board.rangers):
                px = ox + int((p.position.x - min_x)*side)
                py = oy + int((p.position.y - min_y)*side)
                screen.blit(
                    pygame.transform.scale(self.poacher, (side, side)),
                    (px, py)
                )

        # ---------- grid -------------------------------------------
        grid_col = (80, 80, 80)
        for c in range(vis_w + 1):
            x = ox + c * side
            pygame.draw.line(screen, grid_col, (x, oy), (x, oy + vis_h * side), 1)
        for r in range(vis_h + 1):
            y = oy + r * side
            pygame.draw.line(screen, grid_col, (ox, y), (ox + vis_w * side, y), 1)

        # ---------- hover highlight  -------------------------------
        if hover_tile is not None:
            tx, ty = int(hover_tile.x), int(hover_tile.y) # informs the renderer which board square the mouse is over
            # only draw if in our vis window:
            if min_x <= tx < max_x and min_y <= ty < max_y:
                px = ox + int((tx - min_x) * side)
                py = oy + int((ty - min_y) * side)
                # create a transparent surface
                overlay = pygame.Surface((side, side), pygame.SRCALPHA)
                color = (0,200,0,100) if hover_valid else (200,0,0,100) 
                overlay.fill(color)
                screen.blit(overlay, (px, py))

        # ---------- day / night overlay ----------------------------
        if self.dn_opacity > 0:
            tint = self._lerp((255,255,255,0), (0,0,70,160), self.dn_opacity)
            ov   = pygame.Surface((vis_w * side, vis_h * side), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))


    def screen_to_tile(
        self,
        screen_pos: Tuple[int, int],
        board_rect: Rect
    ) -> Vector2 | None:
        """Map a screen (px,py) inside board_rect to a board‐tile (x,y)."""
        mx, my = screen_pos
        if not board_rect.collidepoint(mx, my):
            return None
        # offset in tiles from center
        dx = (mx - board_rect.centerx) / self.tile
        dy = (my - board_rect.centery) / self.tile
        wx = self.cam.x + dx
        wy = self.cam.y + dy
        tx, ty = int(wx), int(wy)
        if 0 <= tx < self.board.width and 0 <= ty < self.board.height:
            return Vector2(tx, ty)
        return None