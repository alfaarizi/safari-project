from __future__ import annotations
import random
from typing import Optional
from pygame.math import Vector2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_safari_project.model.board   import Board
    from my_safari_project.model.poacher import Poacher


class Ranger:
    """
    A park ranger who patrols randomly or chases poachers at a steady speed.
    """

    def __init__(
            self,
            id: int,
            name: str,
            salary: float,
            position: Vector2,
            vision: float = 5.0,
            speed: float = 2.0  # tiles / second (≈ jeep speed)
    ):
        self.id = id
        self.name = name
        self.salary = salary
        self.position = Vector2(position)
        self.vision = vision
        self.speed = speed

        self._target: Vector2 | None = None
        self.poachers_caught = 0

    def set_target(self, tgt: Vector2) -> None:
        """Directly assign a world‐space target to move toward."""
        self._target = Vector2(tgt)

    def patrol(self, board_width: int, board_height: int) -> None:
        """
        If not currently chasing, pick a random patrol waypoint
        (uniform over the whole board) and move toward it.
        """
        # if we’ve reached (or never had) a patrol point, pick a new one
        if self._target is None or self.position.distance_to(self._target) < 0.1:
            self._target = Vector2(
                random.uniform(0, board_width),
                random.uniform(0, board_height)
            )

    def chase_poacher(self, poacher: object) -> None:
        """
        Lock onto a poacher’s current position as the move‐to target.
        (We’ll reevaluate each frame in case they move.)
        """
        self._target = poacher.position.copy()

    def update(self, dt: float, board: "Board"):
        """
        Called once per frame from GameGUI; handles patrol, chase & capture.
        """
        #  — find the nearest poacher within vision
        visible = [
            p for p in board.poachers
            if not p.captured and self.position.distance_to(p.position) <= self.vision
        ]
        if visible:
            # chase nearest
            self._target = Vector2(min(
                visible, key=lambda p: self.position.distance_to(p.position)
            ).position)
        else:
            # pick / keep a random patrol point
            if self._target is None or self.position.distance_to(self._target) < 0.2:
                self._target = Vector2(
                    random.uniform(0, board.width),
                    random.uniform(0, board.height)
                )

        #  move toward target by at most `speed * dt`
        if self._target:
            d   = self._target - self.position
            dst = d.length()
            if dst > 0:
                self.position += d.normalize() * min(self.speed * dt, dst)

        #  if touching a poacher, capture
        for p in visible:
            if self.position.distance_to(p.position) < 0.5:
                p.captured = True
                board.poachers.remove(p)
                # board.capital.addFunds(50)    # board has no capital
                self.poachers_caught += 1
                break

    def eliminate_poacher(self, poacher: object) -> bool:
        """
        If close enough to the poacher, “catch” them.
        """
        if self.position.distance_to(poacher.position) < 0.5 and getattr(poacher, 'is_hunting', True):
            poacher.is_hunting = False
            self.poachers_caught += 1
            return True
        return False

    def eliminate_animal(self, animal: object) -> bool:
        """
        If close enough to the animal, “kill” it.
        """
        if self.position.distance_to(animal.position) < 0.5 and getattr(animal, 'is_alive', lambda: False)():
            animal.kill()
            self.animals_eliminated += 1
            return True
        return False

    def pay_salary(self, capital: object) -> bool:
        """
        Deduct this ranger's salary; if funds are insufficient, go off‐duty.
        """
        if capital.deductFunds(self.salary):
            return True
        self.is_on_duty = False
        return False

    def __repr__(self):
        return (
            f"<Ranger#{self.id} pos={self.position!r} "
            f"target={self._target!r} caught={self.poachers_caught}>"
        )
