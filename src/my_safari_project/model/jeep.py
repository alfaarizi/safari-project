import math
from typing import List
from pygame.math import Vector2


class Jeep:
    """Drives along a precomputed list of tile-centre waypoints and updates its heading."""

    def __init__(self, jeep_id: int, start_position: Vector2):
        self.jeep_id = jeep_id
        # world-space position (1.0 = one tile)
        self.position: Vector2 = Vector2(start_position)
        self.speed: float      = 2.0  # tiles per second

        # path state
        self.path: List[Vector2] = []
        self._waypoint_index: int = 0
        self.returning: bool      = False

        # visual
        self.heading: float      = 0.0  # degrees, 0 → east

        # logic
        self.is_available = True
        self.current_passengers = 0

    def set_path(self, waypoints: List[Vector2]):
        """
        waypoints: list of integer tile coords (Vector2(x,y)) WITHOUT the 0.5 offset.
        We'll apply the +0.5 here to centre on each tile.
        """
        # convert tile coords → world centres
        self.path = [wp + Vector2(0.5, 0.5) for wp in waypoints]
        self._waypoint_index = 0
        self.is_available = True

        # immediately face toward the first leg (if any)
        if len(self.path) >= 2:
            self._update_heading(self.path[1])

    def update(self, dt: float):
        """Move along the current path, updating position and heading."""
        if not self.path or self._waypoint_index >= len(self.path):
            # once done, mark jeep as available for new hires
            self.is_available = True
            return

        target = self.path[self._waypoint_index]
        delta  = target - self.position
        dist   = delta.length()
        step   = self.speed * dt

        if dist <= step:
            self.position = Vector2(target)
            self._waypoint_index += 1

            if self._waypoint_index < len(self.path):
                self._update_heading(self.path[self._waypoint_index])
        else:
            self.position += delta.normalize() * step
            self._update_heading(target)

    def _update_heading(self, look_at: Vector2):
        """Rotate to face the provided world-space point."""
        v = look_at - self.position
        if v.length_squared() == 0:
            return
        # math.atan2 takes (y, x); negate y because pygame’s y-axis is flipped
        angle_rad = math.atan2(-v.y, v.x)
        self.heading = math.degrees(angle_rad)

    def __repr__(self):
        return (
            f"<Jeep #{self.jeep_id} "
            f"pos=({self.position.x:.2f},{self.position.y:.2f}) "
            f"wp={self._waypoint_index}/{len(self.path)} "
            f"hdg={self.heading:.1f}°>"
        )
