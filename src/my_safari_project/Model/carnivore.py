from pygame.math import Vector2
from typing import TYPE_CHECKING
from animal import Animal

if TYPE_CHECKING:
    from herbivore import Herbivore

class Carnivore(Animal["Herbivore"]):
    """Animal that consumes Herbivore"""
    def __init__(
        self, 
        group_id: int, 
        position: Vector2, 
        speed: float,
        value: int, 
        age: int, 
        lifespan: int
    ):
        super().__init__(group_id, position, speed, value, age, lifespan)