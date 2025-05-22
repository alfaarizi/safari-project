from __future__ import annotations

import os
import pygame
from my_safari_project.model.field import TerrainType
from pygame import Surface, Rect
from pygame.math import Vector2
from typing import Tuple
from pygame import Rect
from my_safari_project.model.board import Board
from my_safari_project.model.road  import Road, RoadType
from my_safari_project.model.animal import Animal
from my_safari_project.model.timer import TIME_SCALE




class BoardGUI:
    MIN_TILE = 4
    MAX_TILE = 64

    def __init__(self, board: Board, default_tile: int = 32):
        self.board = board
        from my_safari_project.view.gamegui import BOARD_RECT

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
            board.width / 2,
            board.height / 2
        )

        self._dragging = False
        self._drag_start = Vector2(0, 0)
        self._cam_at_drag = Vector2(self.cam)

        # Day/night cycle
        self._dn_enabled = True
        self._dn_timer = 0.0
        self._dn_period = 8 * 60
        self.dn_opacity = 0.0

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
        self.desert  = self._load_img(root, "ground",  alpha=False)
        self.plant   = self._load_img(root, "plant")
        self.pond    = self._load_img(root, "pond")
        self.jeep    = self._load_img(root, "jeep")
        self.ranger  = self._load_img(root, "ranger")
        self.poacher = self._load_img(root, "poacher")
        self.tourist = self._load_img(root, "tourist")
        self.entrance = self._load_img(root, "entrance")
        self.exit     = self._load_img(root, "exit")


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
        if not self._dragging:
            return

        offset = Vector2(pos) - self._drag_start

        self.cam = self._cam_at_drag - offset / self.tile

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
    def update_day_night(self, dt: float, elapsed_seconds: float, mouse_pos):

        # Convert elapsed seconds to total game minutes
        game_minutes = elapsed_seconds / TIME_SCALE["minute"]  

        # Add 360 to shift time start from 0 to 6:00 AM
        total_minutes = (game_minutes + 360) % 1440  # wrap around 24h

        # Fade transitions
        fade_in_start = 360   # 6:00 AM
        fade_in_end   = 540   # 9:00 AM
        fade_out_start = 1080 # 6:00 PM
        fade_out_end   = 1260 # 9:00 PM


        if fade_in_start <= total_minutes < fade_in_end:
            t = (total_minutes - fade_in_start) / (fade_in_end - fade_in_start)
            target_opacity = 1 - t  # fade out (dark -> light)
        elif fade_out_start <= total_minutes < fade_out_end:
            t = (total_minutes - fade_out_start) / (fade_out_end - fade_out_start)
            target_opacity = t  # fade in (light  dark)
        elif total_minutes >= fade_out_end or total_minutes < fade_in_start:
            target_opacity = 1.0  # full dark
        else:
            target_opacity = 0.0  # full bright

        # Smooth interpolation
        speed = 0.3  # You can tweak this
        self.dn_opacity += (target_opacity - self.dn_opacity) * speed * dt * 60
        self.dn_opacity = max(0.0, min(1.0, self.dn_opacity))

        self._night_active = target_opacity == 1.0
        self._cursor_pos = mouse_pos



    # ─── rendering ─────────────────────────────────────────────────────
    @staticmethod
    def _lerp(c1: Tuple[int,int,int,int],
              c2: Tuple[int,int,int,int], t: float) -> Tuple[int,int,int,int]:
        return tuple(int(a + (b - a)*t) for a,b in zip(c1, c2))



    @staticmethod
    def _smoothstep(t: float) -> float:
        return t * t * (3 - 2 * t)

    def render(self,screen: Surface,rect: Rect,*,hover_tile: Vector2 | None = None, hover_valid: bool = False ) -> None:
        if self.board.width == 0 or self.board.height == 0:
            return

        side = self.tile
        self.tile = max(self.MIN_TILE, min(self.tile, self.MAX_TILE))

        half_w = rect.width // (2 * side)
        half_h = rect.height // (2 * side)

        min_x = int(self.cam.x - half_w - 1)
        min_y = int(self.cam.y - half_h - 1)
        max_x = int(self.cam.x + half_w + 2)
        max_y = int(self.cam.y + half_h + 2)

        ox = rect.centerx - int((self.cam.x - min_x) * side)
        oy = rect.centery - int((self.cam.y - min_y) * side)

        vis_w = int(max_x - min_x)
        vis_h = int(max_y - min_y)

        visible_map = None
        world_x = world_y = 0
        if self._night_active:
            radius = 5
            mx, my = self._cursor_pos
            world_x = self.cam.x + (mx - rect.centerx) / side
            world_y = self.cam.y + (my - rect.centery) / side
            visible_map = lambda x, y: (x - world_x) ** 2 + (y - world_y) ** 2 <= radius ** 2

        # LAYER 1: Background
        bg = pygame.transform.scale(self.desert, ((max_x - min_x) * side, (max_y - min_y) * side))
        screen.blit(bg, (ox, oy))

        # LAYER 2: Terrain
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if 0 <= x < self.board.width and 0 <= y < self.board.height:
                    field = self.board.fields[y][x]
                    px = ox + int((x - min_x) * side)
                    py = oy + int((y - min_y) * side)

                    terrain_value = (field.terrain_type.value
                                     if hasattr(field.terrain_type, 'value')
                                     else field.terrain_type)

                    # Draw terrain based on type
                    if terrain_value != TerrainType.GRASS.value:
                        pygame.draw.rect(screen, field.get_color(terrain_value), (px, py, side, side))

        # Roads
        def draw_single_road(rd):
            px, py = int(ox + (rd.pos.x - min_x) * side), int(oy + (rd.pos.y - min_y) * side)
            margin = int(side // 2.5)
            yellow, lw = (200, 200, 0), max(1, int(side // 30))  # Darker yellow
            pygame.draw.rect(screen, (0, 0, 0), (px, py, int(side), int(side))) # Black road surface
            match rd.type:
                case RoadType.STRAIGHT_H:
                    pygame.draw.line(screen, yellow, (px + margin, py + int(side)//2), (px + int(side) - margin, py + int(side)//2), lw)
                case RoadType.STRAIGHT_V:
                    pygame.draw.line(screen, yellow, (px + int(side)//2, py + margin), (px + int(side)//2, py + int(side) - margin), lw)
        for rd in self.board.roads:
            if min_x <= rd.pos.x < max_x and min_y <= rd.pos.y < max_y:
                draw_single_road(rd)

        # LAYER 4: Entrances and Exits
        for doors, is_entrance in [(self.board.entrances, True), (self.board.exits, False)]:
            for e in doors[:]:
                if min_x <= e.x < max_x and min_y <= e.y < max_y:
                    road = next((r for r in self.board.roads if r.pos == e), None)
                    if road:
                        match road.type:
                            case RoadType.STRAIGHT_H:
                                door_x, door_y = (e.x + 2, e.y) if any(r.pos == Vector2(e.x - 1, e.y) for r in self.board.roads) else (e.x - 2, e.y)
                            case RoadType.STRAIGHT_V:
                                door_x, door_y = (e.x, e.y - 2) if any(r.pos == Vector2(e.x, e.y + 1) for r in self.board.roads) else (e.x, e.y + 2)
                    else:
                        door_x, door_y = e.x, e.y
                    
                    if min_x <= door_x < max_x and min_y <= door_y < max_y:
                        door_size = int(side * 1.5)
                        px = ox + int((door_x - min_x) * side) - (door_size - side) // 2
                        py = oy + int((door_y - min_y) * side) - (door_size - side)  # Bottom-aligned
                        img = self.entrance if is_entrance else self.exit
                        screen.blit(pygame.transform.scale(img, (door_size, door_size)), (px, py))

        # LAYER 5: Static entities (Ponds and Plants)
        # Ponds
        for p in self.board.ponds:
            x, y = p.position
            if min_x <= x < max_x and min_y <= y < max_y:
                px = ox + int((x - min_x) * side)
                py = oy + int((y - min_y) * side)
                screen.blit(pygame.transform.scale(self.pond, (side, side)), (px, py))
        # Plants
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

        # LAYER 6: Animal debug overlays (if enabled)
        if getattr(self.board.wildlife_ai.animal_ai, "debug_mode"):
            self.board.wildlife_ai.animal_ai.render(screen, ox, oy, side, min_x, min_y)

        # LAYER 7: Moving entities (Animals, Jeeps, Rangers, etc.)
        # Animals
        aw, ah = side, side
        for animal in self.board.animals:
            loc = getattr(animal, "position", Vector2(0, 0))

            if self._night_active:
                is_tagged = animal.animal_id in self.board.visible_animals_night
                near_ranger = any(r.position.distance_to(loc) <= 5 for r in self.board.rangers)
                near_tourist = any(t.position.distance_to(loc) <= 5 for t in self.board.tourists)
                if not (is_tagged or near_ranger or near_tourist):
                    continue

            px = ox + int((loc.x - min_x) * side)
            py = oy + int((loc.y - min_y) * side)
            screen.blit(pygame.transform.scale(self.animals[animal.species.value], (aw, ah)), (px, py))
        # Jeeps
        jw = jh = side * 2
        for j in self.board.jeeps:
            cx, cy = j.position
            if (min_x - 2) <= cx < (max_x + 2) and (min_y - 2) <= cy < (max_y + 2):
                img = pygame.transform.scale(self.jeep, (jw, jh))
                img = pygame.transform.rotate(img, -j.heading)
                r = img.get_rect(center=(0, 0))
                px = ox + int((cx - min_x) * side - r.width / 2)
                py = oy + int((cy - min_y) * side - r.height / 2)
                screen.blit(img, (px, py))
        # Rangers
        for r in self.board.rangers:
            rx, ry = r.position
            if min_x <= rx < max_x and min_y <= ry < max_y:
                px = ox + int((rx - min_x) * side)
                py = oy + int((ry - min_y) * side)
                screen.blit(pygame.transform.scale(self.ranger, (side, side)), (px, py))
        # Poachers
        for p in self.board.poachers:        
            px = ox + int((p.position.x - min_x) * side)
            py = oy + int((p.position.y - min_y) * side)
            screen.blit(pygame.transform.scale(self.poacher, (side, side)), (px, py))
        # Tourists (only if not inside a jeep)
        tourist_size = int(side * 1.5)
        radius = max(3, int(side * 0.2))
        for t in self.board.tourists + self.board.waiting_tourists:
            if hasattr(t, 'in_jeep') and t.in_jeep is not None: continue
            tx, ty = t.position
            if min_x <= tx < max_x and min_y <= ty < max_y:
                px = ox + int((tx - min_x) * side)
                py = oy + int((ty - min_y) * side)
                if t in self.board.waiting_tourists:
                    pygame.draw.circle(screen, (255, 215, 0), (px + side // 2, py + side // 2), radius)
                else:
                    screen.blit(pygame.transform.scale(self.tourist, (tourist_size, tourist_size)), (px, py))

        # LAYER 8: Hover highlight
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

        # LAYER 10: Day/night overlay
        if self.dn_opacity > 0:
            smoothed = self._smoothstep(self.dn_opacity)
            tint = self._lerp((255, 255, 255, 0), (0, 0, 70, 160), smoothed)
            ov = pygame.Surface((vis_w * side, vis_h * side), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (ox, oy))

    def screen_to_board(self, screen_pos, rect):
        rel_x = screen_pos[0] - rect.centerx
        rel_y = screen_pos[1] - rect.centery

        # Convert to board coordinates using camera position and zoom
        board_x = self.cam.x + (rel_x / self.tile)
        board_y = self.cam.y + (rel_y / self.tile)

        return Vector2(board_x, board_y)

    def board_to_screen(self, board_pos, rect):
        rel_x = (board_pos.x - self.cam.x) * self.tile
        rel_y = (board_pos.y - self.cam.y) * self.tile

        # Convert to screen coordinates
        screen_x = rect.centerx + rel_x
        screen_y = rect.centery + rel_y

        return Vector2(screen_x, screen_y)

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

    def screen_to_world(self, screen_pos: tuple[int, int]) -> Vector2:
        """Convert screen (pixel) coordinates to world (tile) coordinates."""
        from my_safari_project.view.gamegui import BOARD_RECT
        mx, my = screen_pos
        if not BOARD_RECT.collidepoint(mx, my):
            return None  # Outside the board area

        # Convert from screen to world based on camera and tile size
        offset_x = BOARD_RECT.centerx
        offset_y = BOARD_RECT.centery
        rel_x = (mx - offset_x) / self.tile
        rel_y = (my - offset_y) / self.tile
        world_x = self.cam.x + rel_x
        world_y = self.cam.y + rel_y
        return Vector2(world_x, world_y)