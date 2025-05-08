# ─── Jeep ───────────────────────────────────────────────────────────────────
from __future__ import annotations
import math, time
from typing import List
from pygame.math import Vector2


SAFE_RADIUS = .8          # tiles – how close is “too close”
YIELD_TIME  = 1.0         # seconds to wait when yielding


class Jeep:
    """
    Drives along a pre-computed list of tile-centres.
    When the next waypoint is occupied by another jeep the
    jeep will pause for YIELD_TIME seconds and then try again.
    """

    def __init__(self, jeep_id: int, start_pos: Vector2):
        self.id          = jeep_id
        self.position    = Vector2(start_pos)
        self.speed       = 2.0          # tiles / second
        self._path: List[Vector2] = []
        self._idx        = 0
        self.heading     = 0.0          # degrees
        self._resume_at  = 0.0          # world-time until which we are yielding

    # ── public API ─────────────────────────────────────────────────────────
    def set_path(self, waypoints: List[Vector2]):
        """Waypoints are in integer tile coordinates (no +0.5 yet)."""
        self._path = [wp + Vector2(.5, .5) for wp in waypoints]
        self._idx  = 0
        if len(self._path) >= 2:
            self._update_heading(self._path[1])

    def update(self, dt: float, now: float, other: list["Jeep"]):
        """Move, but yield if the next tile is busy."""
        if self._idx >= len(self._path):
            return                                    # finished

        if now < self._resume_at:
            return                                    # currently yielding

        tgt = self._path[self._idx]

        # check for collision: is any other jeep *already* inside target tile?
        for j in other:
            if j is self: continue
            if (j.position - tgt).length() < SAFE_RADIUS:
                self._resume_at = now + YIELD_TIME    # pause then retry
                return

        # --- travel towards tgt ------------------------------------------------
        delta = tgt - self.position
        dist  = delta.length()
        step  = self.speed * dt

        if dist <= step:
            self.position = Vector2(tgt)
            self._idx    += 1
            if self._idx < len(self._path):
                self._update_heading(self._path[self._idx])
        else:
            self.position += delta.normalize() * step
            self._update_heading(tgt)

    # ── helpers ────────────────────────────────────────────────────────────
    def _update_heading(self, look_at: Vector2):
        v = look_at - self.position
        if v.length_squared() == 0: return
        # negate y because pygame Y-axis is downward
        self.heading = math.degrees(math.atan2(-v.y, v.x))

    # ── debug ──────────────────────────────────────────────────────────────
    def __repr__(self):
        return f"<Jeep #{self.id} {self.position} hdg={self.heading:.1f}°>"
