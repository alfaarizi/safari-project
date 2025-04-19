from __future__ import annotations
from pygame.math import Vector2
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_safari_project.model.poacher import Poacher
    from my_safari_project.model.animal import Animal
    from my_safari_project.model.capital import Capital

class Position:
    """
    Simple integer‐based tile position for compatibility with GameController.
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def getX(self) -> int:
        return self.x

    def getY(self) -> int:
        return self.y

class Ranger:
    """
    A park ranger who can patrol, chase poachers, eliminate poachers or animals,
    and must be paid a monthly salary.
    """

    def __init__(
        self,
        id: int,
        name: str,
        salary: float,
        position: Vector2,
        vision: float = 5.0,
        speed = 2.0
    ):
        # identity & pay
        self.id: int = id
        self.name: str = name
        self.salary: float = salary

        # position & movement
        self.position: Vector2 = position
        self.speed: float = speed       # tiles per second
        self.vision: float = vision     # detection radius

        # state
        self.is_on_duty: bool = True
        self.poachers_caught: int = 0
        self.animals_eliminated: int = 0

        # runtime target (either a patrol point or a chase target)
        self._target: Vector2 | None = None

    class Ranger:
        def __init__(self, position: Vector2):
            self.position = position
            self.target = None
            self.is_on_duty = True
            self.speed = 2.0  # Reduced from higher value (adjust this number to get desired speed)

        def update(self, dt: float):
            """Move toward self.target if any."""
            if not self.is_on_duty or self.target is None:
                return

            direction = (self.target - self.position).normalize()
            # Add speed clamping to prevent excessive movement
            movement = direction * self.speed * dt
            # Optional: Add maximum movement clamping
            max_movement = 2.0 * dt  # Maximum distance to move per frame
            if movement.length() > max_movement:
                movement.scale_to_length(max_movement)

            self.position += movement

    def patrol(self, board_width: int, board_height: int) -> None:
        """
        If not currently chasing, pick a random patrol waypoint and move toward it.
        """
        if self._target is None or self.position.distance_to(self._target) < 0.1:
            self._target = Vector2(
                random.uniform(0, board_width),
                random.uniform(0, board_height)
            )
        self._move_toward_target()

    def chase_poacher(self, poacher: Poacher) -> None:
        """
        Start chasing the given poacher.
        """
        self._target = poacher.position.copy()
        self._move_toward_target()

    def _move_toward_target(self) -> None:
        """
        Move a step towards self._target according to self.speed.
        """
        if not self._target:
            return

        direction = self._target - self.position
        dist = direction.length()
        if dist == 0:
            return

        # normalize and step
        step = min(dist, self.speed)
        self.position += direction.normalize() * step

        # clear target if reached
        if dist <= step:
            self._target = None

    def eliminate_poacher(self, poacher: Poacher) -> bool:
        """
        If within melee range, eliminate the poacher.
        Returns True if successful.
        """
        if self.position.distance_to(poacher.position) < 0.5 and poacher.is_hunting:
            poacher.is_hunting = False
            self.poachers_caught += 1
            return True
        return False

    def eliminate_animal(self, animal: Animal) -> bool:
        """
        If within melee range, eliminate the animal.
        Returns True if successful.
        """
        if self.position.distance_to(animal.position) < 0.5 and animal.is_alive():
            animal.kill()   # assume Animal.kill() sets alive=False
            self.animals_eliminated += 1
            return True
        return False

    def pay_salary(self, capital: Capital) -> bool:
        """
        Deduct this ranger's salary from capital. If insufficient funds, returns False.
        """
        if capital.deductFunds(self.salary):
            return True
        self.is_on_duty = False  # automatically go off‑duty if you can't pay
        return False
