from __future__ import annotations
from pygame.math import Vector2
from random import randint, random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_safari_project.model.board import Board
    from my_safari_project.model.capital import Capital


VISION = 4           # tiles
POACHER_INTERVAL = 45  # seconds between spawns


class WildlifeAI:
    """Keeps Rangers & Poachers moving + interactions."""

    def __init__(self, board: Board, capital: Capital):
        self.board = board
        self.capital = capital
        self._poacher_timer = 0.0

    # -------------------------------------------------
    def update(self, dt: float):
        self._poacher_timer += dt
        if self._poacher_timer > POACHER_INTERVAL:
            self._spawn_poacher()
            self._poacher_timer = 0.0

        # ---- Update Poachers ----
        for p in self.board.poachers:
            p.update(dt, (self.board.width, self.board.height))

        # ---- Update Rangers ----
        for r in self.board.rangers:
            r.update(dt)
            self._ranger_vision(r)

    # -------------------------------------------------
    def monthly_tick(self):
        """Call at the beginning of each in‑game month → pay salaries."""
        for r in self.board.rangers[:]:
            if not r.pay_salary(self.capital):
                # could not pay → fire ranger
                self.board.rangers.remove(r)

    # -------------------------------------------------
    #                helpers
    # -------------------------------------------------
    def _spawn_poacher(self):
        self.board.spawn_poacher(Vector2(randint(0, self.board.width - 1), 0))

    def _ranger_vision(self, ranger):
        """If a poacher within vision → chase / catch."""
        for p in self.board.poachers[:]:
            dist = ranger.position.distance_to(p.position)
            if dist <= ranger.vision:
                p.visible = True
                # simple chase: ranger sets target to poacher
                ranger.target = p.position
                if dist < 0.6:           # caught!
                    self.board.poachers.remove(p)
                    ranger.poachers_caught += 1
                    self.capital.addFunds(50)   # bounty
            else:
                p.visible = False
