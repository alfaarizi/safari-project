from pygame.math import Vector2
from typing import TYPE_CHECKING
from my_safari_project.model.animal import Animal

'''if TYPE_CHECKING:
    from my_safari_project.model.herbivore import Herbivore'''

class Carnivore(Animal["Herbivore"]):
    """Animal that consumes Herbivore"""
    def __init__(
        self,
        animal_id: int,
        group_id: int, 
        position: Vector2, 
        speed: float,
        value: int, 
        age: int, 
        lifespan: int
    ):
        super().__init__(animal_id, group_id, position, speed, value, age, lifespan)