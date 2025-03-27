from pygame.math import Vector2
from Animal import Animal
from Plant import Plant

class Herbivore(Animal[Plant]):
    """Animal that consumes Plant"""
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