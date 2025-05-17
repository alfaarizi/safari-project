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
            speed: float = 1.0  # tiles / second (≈ jeep speed)
    ):
        self.id = id
        self.name = name
        self.salary = salary
        self.position = Vector2(position)
        self.vision = vision
        self.speed = speed
        self.assigned_poacher = None  # type: Optional[Poacher]


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

        # --- Manual pursuit if assigned ---
        if self.assigned_poacher and self.assigned_poacher in board.poachers:
            self.chase_poacher(self.assigned_poacher)
        else:
            # --- Auto-chase nearest poacher in vision ---
            visible_poachers = [
                p for p in board.poachers
                if not p.captured and self.position.distance_to(p.position) <= self.vision
            ]

            if visible_poachers:
                nearest = min(visible_poachers, key=lambda p: self.position.distance_to(p.position))
                self._target = nearest.position
            else:
                # --- Patrol if no target ---
                if self._target is None or self.position.distance_to(self._target) < 0.2:
                    self._target = Vector2(
                        random.uniform(0, board.width),
                        random.uniform(0, board.height)
                    )

        # --- Move toward target ---
        if self._target:
            direction = self._target - self.position
            if direction.length() > 0:
                self.position += direction.normalize() * min(self.speed * dt, direction.length())

        # --- Eliminate poacher if close enough ---
        # Manual target
        if self.assigned_poacher and self.assigned_poacher in board.poachers:
            if self.position.distance_to(self.assigned_poacher.position) < 0.5:
                board.poachers.remove(self.assigned_poacher)
                self.poachers_caught += 1
                self.assigned_poacher = None
                # Call to GameController externally for bounty and feedback
                return "poacher_eliminated"

        # Auto-detected
        for p in board.poachers[:]:
            if self.position.distance_to(p.position) < 0.5:
                board.poachers.remove(p)
                self.poachers_caught += 1
                return "poacher_eliminated"



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
