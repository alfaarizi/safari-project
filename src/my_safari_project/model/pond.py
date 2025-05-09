from pygame.math import Vector2

class Pond:
    def __init__(
        self,
        pond_id: int,
        position: tuple,
    ):
        self.pond_id: int = pond_id
        self.position: Vector2 = position 