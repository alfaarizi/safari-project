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


    # ---------------------------------------------------------------- road
    def _build_initial_road(self):
        # key points: entrance → random bends → exit
        pts: List[Vector2] = [self.entrance]
        for _ in range(random.randint(2, 3)):
            pts.append(Vector2(
                random.randint(2, self.width - 3),
                random.randint(2, self.height - 3),
            ))
        pts.append(self.exit)

        # ------------------------------------------------------------------
        self._build_roads(n_roads)
        self._spawn_jeeps(n_jeeps)

    # ── road building ─────────────────────────────────────────────────────
    def _build_roads(self, n: int):
        """
        Create `n` separate roads, roughly evenly spaced vertically.
        Each road runs left→right across the entire world with a couple of
        random vertical offsets so they are not perfectly straight.
        """
        gap = self.height // (n + 1)
        for i in range(n):
            y = (i + 1) * gap
            start = Vector2(0, y)
            end   = Vector2(self.width - 1, y)

            # remember real entrances/exits for jeep paths
            self.entrances.append(start)
            self.exits.append(end)

            # optional random bend every ~20 tiles
            pts: list[Vector2] = [start]
            x = 0
            while x < self.width - 1:
                x += random.randint(15, 25)
                if x >= self.width - 1: break
                bend_y = max(1, min(self.height - 2,
                                    y + random.choice([-3, -2, -1, 1, 2, 3])))
                pts.append(Vector2(x, bend_y))
            pts.append(end)

            # lay segments
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

    # ── path helper ───────────────────────────────────────────────────────
    def _build_path(self, start: Vector2, goal: Vector2) -> list[Vector2]:
        """Simple BFS along road tiles."""
        start, goal = Vector2(start), Vector2(goal)
        Q = deque([start])
        prev = {tuple(start): None}
        road_map = {tuple(r.pos): r for r in self.roads}

        while Q:
            pos = Q.popleft()
            if pos == goal:
                break
            for n in road_map[tuple(pos)].neighbors:
                k = tuple(n)
                if k not in prev:
                    prev[k] = pos
                    Q.append(n)

        # reconstruct
        path: list[Vector2] = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = prev.get(tuple(cur))
        path.reverse()
        return path

    # ── jeep spawning ────────────────────────────────────────────────────
    def _spawn_jeeps(self, n_jeeps: int):
        """Distribute jeeps round-robin over available roads."""
        for j_id in range(1, n_jeeps + 1):
            road_idx = (j_id - 1) % len(self.entrances)
            start, end = self.entrances[road_idx], self.exits[road_idx]
            path = self._build_path(start, end)

            jeep = Jeep(j_id, start + Vector2(.5, .5))
            jeep.set_path(path)
            self.jeeps.append(jeep)

    # ── update (called from GameController) ───────────────────────────────
    def update(self, dt: float, now: float):
        for j in self.jeeps:
            j.update(dt, now, self.jeeps)

            # check if reached target
            target = self.exit if not jeep.returning else self.entrance
            centre = target + Vector2(0.5, 0.5)
            if (jeep.position - centre).length() < 0.1:
                jeep.returning = not jeep.returning
                # rebuild path in opposite direction
                new_start = self.exit if jeep.returning else self.entrance
                new_goal  = self.entrance if jeep.returning else self.exit
                jeep.set_path(self._build_path(new_start, new_goal))

    # --------------------------------------------------------- board growth
    def _expand_right(self):
        """Add one column on the right."""
        for y, row in enumerate(self.fields):
            row.append(Field(Vector2(len(row), y)))
        self.width += 1
        self.exit.x = self.width - 1

    def _expand_down(self):
        """Add one row at the bottom."""
        y = self.height
        self.fields.append([Field(Vector2(x, y)) for x in range(self.width)])
        self.height += 1

    # ---------------------------------------------------------- debugging
    def __repr__(self) -> str:
        return (
            f"<Board {self.width}×{self.height} "
            f"roads={len(self.roads)} jeeps={len(self.jeeps)}>"
        )

    #---helpers--
    def is_road(self, tile: Vector2) -> bool:
        return any(r.pos == tile for r in self.roads)

    def is_blocked(self, tile: Vector2) -> bool:
        tile = Vector2(int(tile.x), int(tile.y))
        return (
            self.is_road(tile)
            or any(Vector2(int(p.position.x), int(p.position.y)) == tile for p in self.plants)
            or any(Vector2(int(p.position.x), int(p.position.y)) == tile for p in self.ponds)
            or any(Vector2(int(a.position.x), int(a.position.y)) == tile for a in self.animals)
            or any(Vector2(int(r.position.x), int(r.position.y)) == tile for r in self.rangers)
            or any(Vector2(int(po.position.x), int(po.position.y)) == tile for po in self.poachers)
        )

    def is_placeable(self, tile: Vector2) -> bool:
        tile = Vector2(int(tile.x), int(tile.y))
        return (
            0 <= tile.x < self.width
            and 0 <= tile.y < self.height
            and not self.is_blocked(tile)
        )
