from __future__ import annotations
import random
from typing import List
from collections import deque

from pygame.math import Vector2

from my_safari_project.model.field   import Field
from my_safari_project.model.road    import Road, RoadType
from my_safari_project.model.jeep    import Jeep
from my_safari_project.model.pond    import Pond
from my_safari_project.model.plant   import Plant
from my_safari_project.model.animal  import Animal
from my_safari_project.model.ranger  import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.tourist import Tourist


class Board:


    def __init__(self, width: int, height: int):
        self.width  = width
        self.height = height

        # entrance (left edge, second row)  / exit (right edge, second-last row)
        self.entrance = Vector2(0, 1)
        self.exit     = Vector2(width - 1, height - 2)

        # fields grid
        self.fields: List[List[Field]] = [
            [Field(Vector2(x, y)) for x in range(width)]
            for y in range(height)
        ]

        # entity lists
        self.roads    : List[Road]    = []
        self.jeeps    : List[Jeep]    = []
        self.ponds    : List[Pond]    = []
        self.plants   : List[Plant]   = []
        self.animals  : List[Animal]  = []
        self.rangers  : List[Ranger]  = []
        self.poachers : List[Poacher] = []
        self.tourists : List[Tourist] = []

        # build initial road and spawn first jeep
        self._build_initial_road()
        self.add_jeep()

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

        for a, b in zip(pts, pts[1:]):
            self._lay_road_segment(a, b)

    def _lay_road_segment(self, a: Vector2, b: Vector2):
        x, y = int(a.x), int(a.y)
        dx = 1 if b.x > a.x else -1
        dy = 1 if b.y > a.y else -1

        # horizontal
        while x != int(b.x):
            self._add_road_tile(Vector2(x, y), Vector2(x+dx, y))
            x += dx

        # vertical
        while y != int(b.y):
            self._add_road_tile(Vector2(x, y), Vector2(x, y+dy))
            y += dy



    def _add_road_tile(self, cur: Vector2, nxt: Vector2):
        """Ensure both tiles exist, link them, and set correct curve/straight."""
        def get_or_create(pos: Vector2) -> Road:
            for r in self.roads:
                if r.pos == pos:
                    return r
            # default type; will adjust for curves below
            rt = RoadType.STRAIGHT_H if pos.y == nxt.y else RoadType.STRAIGHT_V
            road = Road(pos, rt)
            self.roads.append(road)
            return road

        t1 = get_or_create(cur)
        t2 = get_or_create(nxt)

        # link neighbors
        t1.add_neighbor(t2.pos)
        t2.add_neighbor(t1.pos)

        # if both x and y changed, assign curve on t1
        if cur.x != nxt.x and cur.y != nxt.y:
            if nxt.x > cur.x and nxt.y > cur.y:
                t1.road_type = RoadType.CURVE_SE
            elif nxt.x > cur.x and nxt.y < cur.y:
                t1.road_type = RoadType.CURVE_NE
            elif nxt.x < cur.x and nxt.y > cur.y:
                t1.road_type = RoadType.CURVE_SW
            else:
                t1.road_type = RoadType.CURVE_NW

    # ----------------------------------------------------- path & jeep spawning
    def _build_path(self, start: Vector2, goal: Vector2) -> List[Vector2]:
        """BFS on road tiles to get a list of grid-centre waypoints."""
        start = Vector2(int(start.x), int(start.y))
        goal  = Vector2(int(goal.x),  int(goal.y))

        queue = deque([start])
        came  = {tuple(start): None}
        road_map = {tuple(r.pos): r for r in self.roads}

        while queue:
            pos = queue.popleft()
            if pos == goal:
                break
            for n in road_map[tuple(pos)].neighbors:
                key = tuple(n)
                if key not in came:
                    came[key] = pos
                    queue.append(n)

        # reconstruct
        path: List[Vector2] = []
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = came.get(tuple(cur))
        path.reverse()
        return path

    def add_jeep(self):
        """Spawn a jeep at entrance, give it a path to exit."""
        j = Jeep(len(self.jeeps) + 1, self.entrance + Vector2(0.5, 0.5))
        j.set_path(self._build_path(self.entrance, self.exit))
        self.jeeps.append(j)

    # --------------------------------------------------------------- update
    def update(self, dt: float):
        """
        Called each frame; moves jeeps, expands board if they near an edge,
        and flips direction when they reach entrance/exit.
        """
        for jeep in self.jeeps:
            jeep.update(dt)

            ix, iy = int(jeep.position.x), int(jeep.position.y)
            if ix >= self.width - 2:
                self._expand_right()
            if iy >= self.height - 2:
                self._expand_down()

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
