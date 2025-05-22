# ─── Board ──────────────────────────────────────────────────────────────────
from __future__ import annotations
import random, time
from collections import deque
from typing import List
from pygame.math import Vector2


from my_safari_project.model.animal import Animal
from my_safari_project.model.field import Field, TerrainType
from my_safari_project.model.road  import Road, RoadType
from my_safari_project.model.jeep  import Jeep
from my_safari_project.model.tourist  import Tourist



class Board:
    """
    Large world that can host many roads & jeeps.
    Default size is 100×100 but you can change the ctor args.
    """

    # ----------------------------------------------------------------------
    def __init__(self, width: int = 100, height: int = 100,
                 n_roads: int = 3, n_jeeps: int = 10):
        self.width, self.height = width, height

        self.fields: list[list[Field]] = [
            [Field(Vector2(x, y)) for x in range(width)]
            for y in range(height)
        ]
        #added to Make sure the freshly-created grid is coherent
        # for row in self.fields:
        #     for field in row:
        #         field.recalculate_walkable()

        # centre-left / centre-right entrances for every road
        self.entrances: list[Vector2] = []
        self.exits     : list[Vector2] = []

        # entity containers
        self.roads = []  # you probably already have this
        self.jeeps = []
        self.poachers = []
        self.rangers = []
        self.plants = []
        self.ponds = []
        self.animals = []
        self.tourists:List[Tourist] = []
        self.waiting_tourists = []
        self._generate_terrain()


        # ------------------------------------------------------------------
        self._build_roads(n_roads)
        self._spawn_jeeps(n_jeeps)

    # ── road building ─────────────────────────────────────────────────────
    def _build_roads(self, n: int):
        """In Board class - Modified to remember the longest road"""
        gap = self.height // (n + 1)
        longest_road_length = 0
        longest_road_path = None

        for i in range(n):
            y = (i + 1) * gap
            start = Vector2(0, y)
            end = Vector2(self.width - 1, y)

            # Build the road path
            pts: list[Vector2] = [start]
            x = 0
            while x < self.width - 1:
                x += random.randint(15, 25)
                if x >= self.width - 1: break
                bend_y = max(1, min(self.height - 2,
                                    y + random.choice([-3, -2, -1, 1, 2, 3])))
                pts.append(Vector2(x, bend_y))
            pts.append(end)

            # Calculate road length
            road_length = sum(a.distance_to(b) for a, b in zip(pts, pts[1:]))
            if road_length > longest_road_length:
                longest_road_length = road_length
                longest_road_path = pts
                self.longest_road_start = start
                self.longest_road_end = end

            # Remember entrances/exits
            self.entrances.append(start)
            self.exits.append(end)

            # Lay road segments
            for a, b in zip(pts, pts[1:]):
                self._lay_segment(a, b)
        
        self._update_road_types()

    def _lay_segment(self, a: Vector2, b: Vector2):
        x, y = int(a.x), int(a.y)
        dx = 1 if b.x > a.x else -1 if b.x < a.x else 0
        dy = 1 if b.y > a.y else -1 if b.y < a.y else 0

        # horizontal
        while x != int(b.x):
            self._add_road_tile(Vector2(x, y), Vector2(x + dx, y))
            x += dx
        # vertical
        while y != int(b.y):
            self._add_road_tile(Vector2(x, y), Vector2(x, y + dy))
            y += dy

    def _add_road_tile(self, cur: Vector2, nxt: Vector2):
        def get_or_create(pos: Vector2) -> Road:
            for r in self.roads:
                if r.pos == pos:
                    return r
            rt = (RoadType.STRAIGHT_H if pos.y == nxt.y
                  else RoadType.STRAIGHT_V)
            road = Road(pos, rt)
            self.roads.append(road)
            return road

        t1, t2 = get_or_create(cur), get_or_create(nxt)
        t1.add_neighbor(t2.pos)
        t2.add_neighbor(t1.pos)

        # Make road tiles walkable
        fx, fy = int(cur.x), int(cur.y)
        fld = self.fields[fy][fx]
        fld.set_terrain(TerrainType.ROAD)  # Use set_terrain to ensure proper setup
        fld.is_obstacle = False
        fld.walkable = True
    
    def _determine_road_type(self, pos: Vector2):
        x, y = int(pos.x), int(pos.y)
        h_neighbors = sum(1 for dx in [-1,1] if any(r.pos == Vector2(x+dx, y) for r in self.roads))
        v_neighbors = sum(1 for dy in [-1,1] if any(r.pos == Vector2(x, y+dy) for r in self.roads))
        return RoadType.STRAIGHT_H if h_neighbors >= v_neighbors else RoadType.STRAIGHT_V

    def _update_road_types(self):
        from my_safari_project.model.road import RoadType
        for road in self.roads:
            road.type = self._determine_road_type(road.pos)

    def add_road(self, x: int, y: int, road_type: str) -> bool:
        """Add a road from the shop at the specified position."""
        # Map shop road types to RoadType enum
        road_type_map = {
            "h_road": RoadType.STRAIGHT_H,
            "v_road": RoadType.STRAIGHT_V,
            "l_road": RoadType.TURN_L,
            "rl_road": RoadType.TURN_RL,
            "il_road": RoadType.TURN_IL,
            "irl_road": RoadType.TURN_IRL
        }

        # Check bounds
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        # Check if position is already occupied
        for road in self.roads:
            if road.pos == Vector2(x, y):
                return False

        # Create and add new road
        if road_type in road_type_map:
            road = Road(Vector2(x, y), road_type_map[road_type])
            self.roads.append(road)
            self._stitch_into_network(road)
            return True

        return False

    def add_road_segment(self, x: int, y: int, road_type: str) -> bool:
        road_type_map = {
            "h_road": RoadType.STRAIGHT_H,
            "v_road": RoadType.STRAIGHT_V
        }

        if road_type not in road_type_map:
            return False

        cells_to_check = []
        if road_type == "h_road":
            max_cells = min(10, self.width - x)
            for i in range(max_cells):
                cur_x = x + i
                # Stop if we hit another road
                if any(r.pos == Vector2(cur_x, y) for r in self.roads):
                    break
                cells_to_check.append((cur_x, y))
        else:  # v_road
            max_cells = min(10, self.height - y)
            for i in range(max_cells):
                cur_y = y + i
                # Stop if we hit another road
                if any(r.pos == Vector2(x, cur_y) for r in self.roads):
                    break
                cells_to_check.append((x, cur_y))

        if not cells_to_check:
            return False

        prev_road = None
        for cell_x, cell_y in cells_to_check:
            new_road = Road(Vector2(cell_x, cell_y), road_type_map[road_type])
            self.roads.append(new_road)
            self._stitch_into_network(new_road)

            if prev_road:
                prev_road.add_neighbor(new_road.pos)
                new_road.add_neighbor(prev_road.pos)
            prev_road = new_road

        return True

        return True

    # ── path helper ───────────────────────────────────────────────────────
    def _longest_path(self, start: Vector2) -> list[Vector2]:
        """
        Return the longest simple (no repeated tiles) path that starts at the
        *road tile nearest `start`* and finishes on **any road end-point**
        (a tile that has exactly one neighbour).
        """
        if not self.roads:
                return [start]

        road_map = {tuple(r.pos): r for r in self.roads}

        # snap ‘start’ to the nearest road-tile centre
        snap = min(road_map.keys(),
                        key=lambda p: Vector2(p).distance_to(start))
        snap_v = Vector2(snap)

        # breadth-first search that stores whole paths so we can compare
        Q = deque([[snap_v]])
        longest = [snap_v]

        while Q:
                path = Q.popleft()
                head = path[-1]
                head_road = road_map[tuple(head)]

                # if we’re at an end-point AND longer than what we have, keep it
                if len(head_road.neighbors) == 1 and len(path) > len(longest):
                        longest = path

                for nbr in head_road.neighbors:
                        if nbr not in path:                        # no cycles / repeats
                                Q.append(path + [Vector2(nbr)])

        return longest


    def _spawn_jeeps(self, n_jeeps: int = 5):
        """Place jeeps at different entrances and find their longest paths."""
        if not self.roads:
            return

        entrances = sorted(self.entrances, key=lambda p: p.y)[:n_jeeps]

        for i, start in enumerate(entrances):
            # Find path to nearest exit
            path = self._longest_path(start)
            if not path:
                continue

            jeep = Jeep(i + 1, Vector2(start))
            jeep.board = self  # Set board reference
            jeep.set_path(path)
            jeep.speed = 2.0
            self.jeeps.append(jeep)

    # ── update (called from GameController) ───────────────────────────────
    def update(self, dt: float, now: float):
        for jeep in self.jeeps:
            other_jeeps = [j for j in self.jeeps if j != jeep]
            jeep.update(dt, now, other_jeeps)

    # ------------------------------------------------------------------
    def _stitch_into_network(self, road: Road):
        """Link <road> to any existing road that touches it orthogonally."""
        for other in self.roads:
            if other is road:                # ignore self
                continue
            dx = int(other.pos.x - road.pos.x)
            dy = int(other.pos.y - road.pos.y)
            touching = (abs(dx) == 1 and dy == 0) or (abs(dy) == 1 and dx == 0)
            if touching:
                road.add_neighbor(other.pos)
                other.add_neighbor(road.pos)


    # ---------------------------------------------------------------------
    def __repr__(self):
        return f"<Board {self.width}×{self.height} roads={len(self.roads)} jeeps={len(self.jeeps)}>"
     
    def is_blocked(self, tile: Vector2) -> bool:
        """True if any road or item already occupies this tile."""
        tx, ty = int(tile.x), int(tile.y)
        field = self.fields[ty][tx]

        if field.is_obstacle or not field.walkable:
            return True
        
        return field.is_occupied()

    def is_placeable(self, tile: Vector2) -> bool:
        """Only on‐board, walkable (grass) tiles with no road or other object."""
        tx, ty = int(tile.x), int(tile.y)
        # must be on‐board
        # if not (0 <= tx < self.width and 0 <= ty < self.height):
        #     print(f"[is_placeable] {tx,ty} → OFF BOARD")
        #     return False                 # off the world
        # Get the field at this position
        field = self.fields[ty][tx]
        # print(f"[is_placeable] {tx,ty} → walkable={field.walkable} occupied={field.is_occupied()}")
        
        if not field.walkable:
            return False                 # water / obstacle
        if self.is_blocked(tile):
            return False                 # road or existing entity
        return True                     # empty grass

    def _generate_terrain(self):
        # Generate hills in clusters
        for _ in range(int(self.width * self.height * 0.05)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.fields[y][x].terrain_type == TerrainType.GRASS:
                self._create_hill_cluster(x, y, random.randint(1, 3))

        # Generate winding rivers
        for _ in range(2):
            self._create_river()

        # Add dense grass patches
        for _ in range(int(self.width * self.height * 0.1)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.fields[y][x].terrain_type == TerrainType.GRASS:
                self.fields[y][x].set_terrain(TerrainType.DENSE_GRASS)

    def _create_hill_cluster(self, x: int, y: int, height: int):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        field = self.fields[y][x]
        if field.terrain_type != TerrainType.GRASS:
            return

        field.set_terrain(TerrainType.HILL)
        field.elevation = height

        if height > 1:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if random.random() < 0.6:
                    self._create_hill_cluster(x + dx, y + dy, height - 1)

    def _create_river(self):
        """Create a winding river across the map"""
        # Start from a random edge
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        match edge:
            case 'top':
                start_x = random.randint(0, self.width - 1)
                start_y = 0
                direction = Vector2(0, 1)
            case 'bottom':
                start_x = random.randint(0, self.width - 1)
                start_y = self.height - 1
                direction = Vector2(0, -1)
            case 'left':
                start_x = 0
                start_y = random.randint(0, self.height - 1)
                direction = Vector2(1, 0)
            case 'right':
                start_x = self.width - 1
                start_y = random.randint(0, self.height - 1)
                direction = Vector2(-1, 0)

        current = Vector2(start_x, start_y)
        river_tiles = []

        while (0 <= current.x < self.width and
               0 <= current.y < self.height):
            x, y = int(current.x), int(current.y)

            # Add current tile to river
            if self.fields[y][x].terrain_type != TerrainType.ROAD:
                self.fields[y][x].set_terrain(TerrainType.RIVER)
                river_tiles.append((x, y))

            # Random direction change
            if random.random() < 0.2:
                # Change direction slightly
                if direction.x != 0:  # Moving horizontally
                    direction.y = random.choice([-0.5, 0, 0.5])
                else:  # Moving vertically
                    direction.x = random.choice([-0.5, 0, 0.5])

                # Normalize direction
                if direction.length() > 0:
                    direction = direction.normalize()

            # Move to next position
            current += direction

        # Add water effect to neighbors
        for x, y in river_tiles:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and
                        0 <= ny < self.height and
                        self.fields[ny][nx].terrain_type == TerrainType.GRASS):
                    self.fields[ny][nx].set_terrain(TerrainType.DENSE_GRASS)