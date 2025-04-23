from typing import List
from pygame.math import Vector2


class Jeep:

    def __init__(self, jeep_id: int, start_position: Vector2):
        self.jeep_id = jeep_id
        # position in continuous tile‐units (1.0 = one tile width)
        self.position: Vector2 = Vector2(start_position)
        self.speed: float = 2.0  # tiles per second
        self.path: List[Vector2] = []
        self._waypoint_index: int = 0
        self.returning: bool = False

    def set_path(self, waypoints: List[Vector2]):

        # convert to true centers
        self.path = [wp + Vector2(0.5, 0.5) for wp in waypoints]
        self._waypoint_index = 0

    def update(self, dt: float):

        if not self.path or self._waypoint_index >= len(self.path):
            return

        target = self.path[self._waypoint_index]
        delta  = target - self.position
        dist   = delta.length()
        step   = self.speed * dt

        if dist <= step:
            # snap to waypoint
            self.position = Vector2(target)
            self._waypoint_index += 1
        else:
            self.position += delta.normalize() * step

    def __repr__(self):
        return (
            f"<Jeep #{self.jeep_id} at {self.position!r} "
            f"waypoint={self._waypoint_index}/{len(self.path)}>"
        )
