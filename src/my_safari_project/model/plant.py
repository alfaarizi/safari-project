from pygame.math import Vector2

class Plant:
    def __init__(
        self,
        plant_id: int,
        position: tuple,
    ):
        self.plant_id: int = plant_id
        self.position: Vector2 = position 