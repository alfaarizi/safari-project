# ─── Board ──────────────────────────────────────────────────────────────────
from __future__ import annotations
import random, time
from collections import deque
from typing import List
from pygame.math import Vector2


from my_safari_project.model.animal import Animal
from my_safari_project.model.field import Field
from my_safari_project.model.road  import Road, RoadType
from my_safari_project.model.jeep  import Jeep


class Board:
    """
    Large world that can host many roads & jeeps.
    Default size is 100×100 but you can change the ctor args.
    """

    # ----------------------------------------------------------------------
    def __init__(self, width: int = 100, height: int = 100,
                 n_roads: int = 5, n_jeeps: int = 10):
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
        self.tourists = []


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

    def _lay_segment(self, a: Vector2, b: Vector2):
        x, y = int(a.x), int(a.y)
        dx   = 1 if b.x > a.x else -1 if b.x < a.x else 0
        dy   = 1 if b.y > a.y else -1 if b.y < a.y else 0

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
        # added to mark the underlying field as road & non-walkable
        fx, fy = int(cur.x), int(cur.y)
        fld = self.fields[fy][fx]
        fld.terrain_type = "ROAD"
        fld.set_obstacle(True)

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