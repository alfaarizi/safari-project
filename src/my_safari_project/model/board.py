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

            if prev_road:
                prev_road.add_neighbor(new_road.pos)
                new_road.add_neighbor(prev_road.pos)
            prev_road = new_road

        return True

        return True

    # ── path helper ───────────────────────────────────────────────────────
    def _build_path(self, start: Vector2, goal: Vector2) -> list[Vector2]:
        road_map = {tuple(r.pos): r for r in self.roads}
        nearest_start = min(road_map.keys(),
                            key=lambda pos: Vector2(pos).distance_to(start))

        start = Vector2(nearest_start)
        Q = deque([start])
        prev = {tuple(start): None}

        # Find all possible paths
        while Q:
            cur = Q.popleft()
            cur_tuple = tuple(cur)
            current_road = road_map[cur_tuple]

            # Check neighboring roads from current road's connections
            for neighbor_pos in current_road.neighbors:
                next_tuple = tuple(neighbor_pos)
                if next_tuple not in prev:
                    prev[next_tuple] = cur_tuple
                    Q.append(Vector2(neighbor_pos))

        # Find endpoints (road tiles with only one neighbor)
        endpoints = []
        for pos, road in road_map.items():
            if pos in prev and len(road.neighbors) == 1 and pos != tuple(start):
                endpoints.append(pos)

        # Find the longest path
        longest_path = []
        for end in endpoints:
            path = []
            cur = end
            while cur is not None:
                path.append(Vector2(cur[0], cur[1]))
                cur = prev.get(cur)
            path.reverse()

            if len(path) > len(longest_path):
                longest_path = path

        return longest_path if longest_path else [start]

    def _spawn_jeeps(self, n_jeeps: int = 5):
        """Place jeeps at different entrances and find their longest paths."""
        if not self.roads:
            return

        entrances = sorted(self.entrances, key=lambda p: p.y)[:n_jeeps]

        for i, start in enumerate(entrances):
            # Find path to nearest exit
            path = self._build_path(start, Vector2(0, 0))  # Goal is dummy, we'll find longest path
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

    # ---------------------------------------------------------------------
    def __repr__(self):
        return f"<Board {self.width}×{self.height} roads={len(self.roads)} jeeps={len(self.jeeps)}>"
