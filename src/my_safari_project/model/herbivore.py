from pygame.math import Vector2
from typing import TYPE_CHECKING
from my_safari_project.model.animal import Animal
from my_safari_project.model.animal import AnimalSpecies

if TYPE_CHECKING:
    from my_safari_project.model.plant import Plant

class Herbivore(Animal["Plant"]):
    """Animal that consumes Plant"""
    def __init__(
        self, 
        animal_id: int,
        species: AnimalSpecies, 
        position: Vector2, 
        speed: float,
        value: int, 
        lifespan: int
    ):
        super().__init__(animal_id, species, position, speed, value, lifespan)
    
    def consume(self, food: "Plant") -> bool:
        if food.consume_from():
            self.hunger = max(self.hunger - 5.0, 0.0)
            return True
        return False