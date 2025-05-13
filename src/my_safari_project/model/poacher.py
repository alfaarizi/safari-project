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
        speed: float = 1.0,
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

        self._timer = 0.0  # counts up to 1s before picking new target
        self._target = Vector2(position)  # current move‐toward point

    def choose_random_target(self, width: int, height: int):
        self._target = Vector2(
            random.randint(0, width - 1),
            random.randint(0, height - 1)
        )

    def update(self, dt: float, board: "Board")-> str|None:
        # Every 1s pick a new random tile
        self._timer += dt
        if self._timer >= 1.0:
            self._timer = 0.0
            self.choose_random_target(board.width, board.height)

        # Move toward _target
        direction = self._target - self.position
        if direction.length_squared() > 0:
            step = self.speed * dt
            if direction.length() <= step:
                self.position.update(self._target)
            else:
                self.position += direction.normalize() * step

        # ---- 🔍 Visibility Check ----
        self.visible = any(
            self.position.distance_to(r.position) <= r.vision for r in board.rangers
        ) or any(
            self.position.distance_to(a.position) <= 10 and a.is_alive for a in board.animals
        )

        # ---- 💥 Hunt Animal ----
        # --- Hunt and kill nearby animals ---
        for animal in board.animals[:]:  # safe copy
            if animal.is_alive and self.position.distance_to(animal.position) < 2:
                animal.kill()
                board.animals.remove(animal)
                self.animals_caught += 1
                return f"animal_killed:{animal.species.name}:{animal.animal_id}"

        return None

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
