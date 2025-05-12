from __future__ import annotations

from my_safari_project.model.capital import Capital

import math



from enum import Enum
from typing import List
from pygame.math import Vector2


from enum import Enum

class RoadType(Enum):
    STRAIGHT_H = "h_road"  # Horizontal straight road
    STRAIGHT_V = "v_road"  # Vertical straight road
    TURN_L = "l_road"      # L-shaped turn
    TURN_RL = "rl_road"    # Reversed L-shaped turn
    TURN_IL = "il_road"    # Inverted L-shaped turn
    TURN_IRL = "irl_road"  # Inverted reversed L-shaped turn


class Road:
    def __init__(self, pos: Vector2, road_type: RoadType):
        self.pos = Vector2(pos)
        self.type = road_type
        self.neighbors: List[Vector2] = []

    def add_neighbor(self, pos: Vector2):
        if pos not in self.neighbors:
            self.neighbors.append(pos)

    def length_to(self, other: "Road") -> float:
        return self.pos.distance_to(other.pos)


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
