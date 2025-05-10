from pygame.math import Vector2

class Pond:
    def __init__(
        self,
        pond_id: int,
        position: Vector2,
    ):
        self.pond_id: int = pond_id
        self.position: Vector2 = position 
        self.water_level: int = 5
    
    @property
    def is_empty(self) -> bool:
        return self.water_level <= 0

    def drink_from(self) -> bool:
        if self.is_empty: return False
        self.water_level -= 1
        return True