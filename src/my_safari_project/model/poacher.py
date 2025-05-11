from __future__ import annotations
from pygame.math import Vector2
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_safari_project.model.ranger import Ranger
    from my_safari_project.model.animal import Animal
    from my_safari_project.model.animal import Board

class Poacher:
    """
    A poacher that wanders randomly, hunts animals, and tries to evade rangers.
    Only visible when within ranger vision.
    """

    def __init__(
        self,
        id: int,
        name: str,
        position: Vector2,
        speed: float = 1.6,
    ):
        self.id: int = id
        self.name: str = name
        self.position: Vector2 = position
        self.speed: float = speed

        self.is_hunting: bool = True
        self.visible: bool = False
        self.animals_caught: int = 0
        self._target: Vector2 | None = None
        self.captured = False

    def choose_random_target(self, board_width: int, board_height: int) -> None:
        """
        Pick a new random wander target somewhere on the map.
        """
        self._target = Vector2(
            random.uniform(0, board_width),
            random.uniform(0, board_height)
        )

    # ------------------------------------------------------------- frame-update
    def update(self, dt: float, board: "Board") -> None:
        """
        Wander toward a random target every frame.
        `board` is supplied so we can query its current width/height.
        """
        if self.captured:
            return  # already taken by a ranger

        # pick a new wander target if none or reached
        if (self._target is None or
                self.position.distance_to(self._target) < 0.2):
            self.choose_random_target(board.width, board.height)

        # move toward that target
        direction = (self._target - self.position).normalize()
        self.position += direction * self.speed * dt

    def hunt_animal(self, animal: Animal) -> bool:
        """
        If in range, kill the animal and count it.
        Returns True if successful.
        """
        if self.is_hunting and self.position.distance_to(animal.position) < 0.5:
            animal.kill()
            self.animals_caught += 1
            return True
        return False

    def evade_ranger(self, ranger: Ranger) -> bool:
        """
        If a ranger spots this poacher, try to run away.
        Returns True if evasion succeeded.
        """
        dist = self.position.distance_to(ranger.position)
        if dist <= ranger.vision:
            self.visible = True
            # run directly away
            direction = (self.position - ranger.position).normalize()
            self.position += direction * self.speed * 1.2  # a bit faster when fleeing
            return True
        self.visible = False
        return False

    def is_visible_to(self, ranger: Ranger) -> bool:
        """
        Poacher is visible only if within ranger.vision.
        """
        return self.position.distance_to(ranger.position) <= ranger.vision
