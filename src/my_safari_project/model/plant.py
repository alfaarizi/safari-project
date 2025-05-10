from pygame.math import Vector2

class Plant:
    def __init__(
        self,
        plant_id: int,
        position: Vector2,
    ):
        self.plant_id: int = plant_id
        self.position: Vector2 = position
        self.nutrition_level: int = 5
    
    @property
    def is_empty(self) -> bool:
        return self.nutrition_level <= 0

    def consume_from(self) -> bool:
        if self.is_empty: return False
        self.nutrition_level -= 1
        return True