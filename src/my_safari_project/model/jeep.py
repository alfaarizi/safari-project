import math
from typing import List
from pygame.math import Vector2


class Jeep:
    """Drives along a precomputed list of tile-centre waypoints and updates its heading."""

    def __init__(self, jeep_id: int, start_position: Vector2):
        self.jeep_id        = jeep_id
        self.position: Vector2 = Vector2(start_position)
        self.speed: float      = 2.0  # tiles per second

        # path state
        self._path: List[Vector2] = []
        self._idx: int            = 0
        self.returning: bool      = False

        # visual
        self.heading: float       = 0.0  # degrees, 0 → east

    def set_path(self, waypoints: List[Vector2]):
        """
        waypoints: list of integer tile coords (e.g. Vector2(x,y)),
        WITHOUT the 0.5 offset.  We'll apply the +0.5 here.
        """
        # convert tile coords → world centres
        self._path = [wp + Vector2(0.5, 0.5) for wp in waypoints]
        self._idx  = 0

        # immediately face toward the first leg (if any)
        if len(self._path) >= 2:
            self._update_heading(self._path[1])

    def update(self, dt: float):
        """Move along the current path, updating position _and_ heading."""
        if not self._path or self._idx >= len(self._path):
            return

        target = self._path[self._idx]
        delta  = target - self.position
        dist   = delta.length()
        step   = self.speed * dt

        if dist <= step:
            # snap exactly
            self.position = Vector2(target)
            self._idx   += 1

            # if there’s another waypoint, turn to face it instantly
            if self._idx < len(self._path):
                self._update_heading(self._path[self._idx])
        else:
            # move fractionally, then continuously update heading
            self.position += delta.normalize() * step
            self._update_heading(target)

    def _update_heading(self, look_at: Vector2):
        """Rotate to face the provided world-space point."""
        v = look_at - self.position
        if v.length_squared() == 0:
            return
        # math.atan2 takes (y, x); negate y because pygame’s rotation is clockwise
        angle_rad = math.atan2(-v.y, v.x)
        self.heading = math.degrees(angle_rad)

    def __repr__(self):
        return (
            f"<Jeep #{self.jeep_id} pos={self.position!r} "
            f"wp={self._idx}/{len(self._path)} hdg={self.heading:.1f}°>"
        )
