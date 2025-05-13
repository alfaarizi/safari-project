# ─── Jeep ───────────────────────────────────────────────────────────────────
from __future__ import annotations
import math, time
from typing import List, Optional
from pygame.math import Vector2


SAFE_RADIUS = .8          # tiles – how close is “too close”
YIELD_TIME  = 1.0         # seconds to wait when yielding


class Jeep:
    def __init__(self, id: int, position: Vector2):
        self.id = id
        self.position = Vector2(position)
        self.heading = 0
        self.speed = 2.0
        self._path = []
        self._path_index = 0
        self.board = None
        self._reversing = False
        self._reverse_target = None
        self._original_index = 0

    def set_path(self, waypoints: List[Vector2]):
        self._path = [Vector2(wp.x + 0.5, wp.y + 0.5) for wp in waypoints]
        self._path_index = 0
        # Set initial heading based on first path segment
        if len(self._path) >= 2:
            direction = self._path[1] - self._path[0]
            self.heading = math.degrees(math.atan2(direction.y, direction.x))

    def update(self, dt: float, now: float, other_jeeps: List["Jeep"]):
        if not self._path or self._path_index >= len(self._path) - 1:
            if self.board:
                new_path = self.board._build_path(self.position, Vector2(0, 0))
                if new_path and len(new_path) > 1:
                    self._path = new_path
                    self._path_index = 0
                    return
            return

        if self._reversing:
            self._handle_reversing(dt, other_jeeps)
            return

        current = self._path[self._path_index]
        next_point = self._path[self._path_index + 1]

        direction = next_point - self.position
        distance = direction.length()

        for other in other_jeeps:
            if other != self and not other._reversing:
                future_dist = (other.position - (self.position + direction.normalize() * 3)).length()
                if future_dist < 3.0:  # Collision detection threshold
                    if self._should_reverse(other):
                        self._start_reversing()
                        return

        if distance > 0:
            direction.scale_to_length(self.speed * dt)
            new_pos = self.position + direction
            if not any(j != self and j.position.distance_to(new_pos) < 1.0
                       for j in other_jeeps):
                self.position = new_pos
                self.heading = math.degrees(math.atan2(direction.y, direction.x))

        if distance < 0.1:
            self._path_index += 1

    def _should_reverse(self, other: "Jeep") -> bool:
        my_progress = self._path_index / len(self._path)
        other_progress = other._path_index / len(other._path)
        return my_progress < other_progress

    def _start_reversing(self):
        self._reversing = True
        self._original_index = self._path_index
        self._path_index = max(0, self._path_index - 3)

    def _handle_reversing(self, dt: float, other_jeeps: List["Jeep"]):
        target = self._path[self._path_index]
        direction = target - self.position
        distance = direction.length()

        if distance < 0.1:
            if not any(j != self and j.position.distance_to(self.position) < 3.0
                      for j in other_jeeps):
                self._reversing = False
                self._path_index = self._original_index
                return
            self._path_index = max(0, self._path_index - 1)
            return

        direction.scale_to_length(self.speed * 0.5 * dt)  # Slower while reversing
        new_pos = self.position + direction
        if not any(j != self and j.position.distance_to(new_pos) < 1.0
                  for j in other_jeeps):
            self.position = new_pos

    def _find_nearest_road(self) -> Optional[Vector2]:
        min_dist = float('inf')
        nearest = None

        for road in self.board.roads:
            dist = self.position.distance_to(road.pos)
            if dist < min_dist:
                min_dist = dist
                nearest = road.pos

        return nearest if nearest else None
    def _is_at_turn(self) -> bool:
        if len(self._path) < 3 or self._path_index == 0:
            return False
        prev = self._path[self._path_index - 1]
        curr = self._path[self._path_index]
        next = self._path[self._path_index + 1] if self._path_index + 1 < len(self._path) else curr
        return abs((curr - prev).angle_to(next - curr)) > 30

    def _handle_collision_avoidance(self, nearby_jeeps: List["Jeep"]):
        # If this jeep is closer to the turn, make others wait
        my_progress = self._path_index / len(self._path)
        for other in nearby_jeeps:
            if other._path_index / len(other._path) < my_progress:
                self._reversing = True
                self._wait_time = 2.0
                break

    # ── helpers ────────────────────────────────────────────────────────────
    def _update_heading(self, look_at: Vector2):
        v = look_at - self.position
        if v.length_squared() == 0: return
        # negate y because pygame Y-axis is downward
        self.heading = math.degrees(math.atan2(-v.y, v.x))

    # ── debug ──────────────────────────────────────────────────────────────
    def __repr__(self):
        return f"<Jeep #{self.id} {self.position} hdg={self.heading:.1f}°>"
