import math
from typing import List, Tuple
from capital import Capital

class Road:
    def __init__(
        self,
        road_id: int,
        start_point: Tuple[float, float],
        end_point: Tuple[float, float],
        cost_to_build: float,
        is_navigable: bool = True
    ):
        self.road_id: int = road_id
        self.start_point: Tuple[float, float] = start_point
        self.end_point: Tuple[float, float] = end_point
        self.cost_to_build: float = cost_to_build
        self.is_navigable: bool = is_navigable
        self.connected_roads: List["Road"] = []

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
