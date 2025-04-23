from __future__ import annotations

from my_safari_project.model.capital import Capital

import math



from enum import Enum
from typing import List
from pygame.math import Vector2


class RoadType(Enum):
    STRAIGHT_H = "straight_h"
    STRAIGHT_V = "straight_v"
    CURVE_NE   = "curve_ne"
    CURVE_NW   = "curve_nw"
    CURVE_SE   = "curve_se"
    CURVE_SW   = "curve_sw"


class Road:

    def __init__(self, pos: Vector2, road_type: RoadType):
        self.pos: Vector2       = Vector2(pos)
        self.road_type: RoadType = road_type
        self.neighbors: List[Vector2] = []

    def add_neighbor(self, neighbor: Vector2):
        if neighbor not in self.neighbors:
            self.neighbors.append(Vector2(neighbor))

    def length_to(self, other: "Road") -> float:
        return self.pos.distance_to(other.pos)

    # ------------------------------------------------------------- debugging
    def __repr__(self) -> str:
        x, y = int(self.pos.x), int(self.pos.y)
        return f"<Road ({x},{y}) {self.road_type.name}>"


    def build(self, capital: "Capital") -> bool:
        if capital.deductFunds(self.cost_to_build):
            self.is_navigable = True
            return True
        return False

    def remove(self) -> None:
        self.is_navigable = False

    def connect_to(self, other_road: "Road") -> None:
        if other_road not in self.connected_roads:
            self.connected_roads.append(other_road)
        if self not in other_road.connected_roads:
            other_road.connected_roads.append(self)

    def get_length(self) -> float:
        return math.dist(self.start_point, self.end_point)

    def set_navigable(self, status: bool) -> None:
        self.is_navigable = status

    def __repr__(self) -> str:
        return (
            f"Road(road_id={self.road_id}, "
            f"start={self.start_point}, end={self.end_point}, "
            f"navigable={self.is_navigable})"
        )
