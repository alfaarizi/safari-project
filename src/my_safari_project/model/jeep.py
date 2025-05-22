# ─── Jeep ───────────────────────────────────────────────────────────────────
from __future__ import annotations
import math, time
from typing import List, Optional
from pygame.math import Vector2
import random



SAFE_RADIUS = .8          # tiles – how close is “too close”
YIELD_TIME  = 1.0         # seconds to wait when yielding


class Jeep:
    def __init__(self, jeep_id: int, position: Vector2):
        self.jeep_id = jeep_id
        self.position = Vector2(position)
        self.heading = 0
        self.speed = 2.0
        self.reverse_timer = 0
        self.is_reversing = False
        self.board = None
        self._path: List[Vector2] = []
        self._path_index = 0
        self.last_point = None
        self.tourists = []


    def set_path(self, waypoints: list[Vector2]):
        self._path = [Vector2(wp.x + 0.5, wp.y + 0.5) for wp in waypoints]
        self._path_index = 0
        if len(self._path) >= 2:
            direction = self._path[1] - self._path[0]
            self.heading = math.degrees(math.atan2(direction.y, direction.x))

    def update(self, dt: float, now: float, other_jeeps: List["Jeep"]):
        if self not in self.board.jeeps:
            return

        for other in other_jeeps:
            if other != self and other in self.board.jeeps:
                separation = self.position.distance_to(other.position)
                if separation < 0.8:  # crash threshold
                    # Remove both jeeps
                    if self in self.board.jeeps:
                        for t in self.tourists[:]:
                            t.exit_jeep()
                        self.board.jeeps.remove(self)
                    if other in self.board.jeeps:
                        for t in other.tourists[:]:
                            t.exit_jeep()
                        self.board.jeeps.remove(other)
                    from my_safari_project.audio import play_jeep_crash
                    play_jeep_crash()
                    if hasattr(self.board, "game_gui"):
                        self.board.game_gui._feedback("Jeep crash! Passengers are now on foot.")
                    return  # Stop further processing for this jeep

        # Path continuation
        if not self._path or self._path_index >= len(self._path) - 1:
            if self.board:
                current_pos = self.position
                end_points = []
                for road in self.board.roads:
                    if len(road.neighbors) == 1:
                        road_pos = Vector2(road.pos)
                        if road_pos.distance_to(current_pos) > 5:
                            end_points.append(road_pos)

                if end_points:
                    new_end = random.choice(end_points)
                    new_path = self.board._longest_path(current_pos)
                    if new_path and len(new_path) > 1:
                        self.set_path(new_path)
                        return
            return

        if self.at_path_end() and self.tourists:
            for exit_pos in self.board.exits:
                if self.position.distance_to(exit_pos) < 5.0:
                    for t in self.tourists[:]:
                        t.exit_jeep()
                    break

        next_point = self._path[self._path_index + 1]
        direction = next_point - self.position
        distance = direction.length()
        self.heading = math.degrees(math.atan2(direction.y, direction.x))

        move_speed = self.speed * dt
        if self.is_reversing:
            if self.reverse_timer > 0:
                self.reverse_timer -= dt
                if self.last_point:
                    retreat_dir = self.last_point - self.position
                    if retreat_dir.length() > 0:
                        retreat_dir.scale_to_length(move_speed)
                        self.position += retreat_dir
            else:
                self.is_reversing = False
        elif distance > 0:
            move_dir = direction.normalize() * move_speed
            if move_dir.length() > distance:
                move_dir.scale_to_length(distance)
            self.position += move_dir
            self.last_point = Vector2(self.position)

        # Pickup tourists
        for entrance in self.board.entrances:
            if self.position.distance_to(entrance) < 1:
                for tourist in self.board.waiting_tourists[:]:
                    if len(self.tourists) < 4 and self.position.distance_to(tourist.position) < 1.0:
                        if tourist.enter_jeep(self):
                            self.board.waiting_tourists.remove(tourist)

        if distance < 0.05 and not self.is_reversing:
            self.position = Vector2(next_point)
            self._path_index += 1

        if distance < 0.1 and not self.is_reversing:
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

    def at_path_end(self):
        return self._path_index >= len(self._path) - 1
