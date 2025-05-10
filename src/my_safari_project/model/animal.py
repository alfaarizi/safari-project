import random

from pygame.math import Vector2
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Union, Optional, TYPE_CHECKING
from enum import Enum
from pygame import Color

if TYPE_CHECKING:
    from my_safari_project.model.plant import Plant
    from my_safari_project.model.herbivore import Herbivore
    from my_safari_project.model.pond import Pond
    from my_safari_project.model.board import Board
    from my_safari_project.model.field import Field

class AnimalSpecies(Enum):
    HYENA = 0
    LION = 1
    TIGER = 2
    BUFFALO = 3
    ELEPHANT = 4
    GIRAFFE = 5
    HIPPO = 6
    ZEBRA = 7

    @property
    def color(self) -> Color:
        color_map = {
            AnimalSpecies.HYENA: Color(200, 100, 50, 128),      # Brownish
            AnimalSpecies.LION: Color(255, 215, 0, 128),        # Gold
            AnimalSpecies.TIGER: Color(255, 140, 0, 128),       # Orange
            AnimalSpecies.BUFFALO: Color(139, 69, 19, 128),     # Brown
            AnimalSpecies.ELEPHANT: Color(128, 128, 128, 128),  # Gray
            AnimalSpecies.GIRAFFE: Color(255, 255, 153, 128),   # Light yellow
            AnimalSpecies.HIPPO: Color(180, 180, 230, 128),     # Light purple
            AnimalSpecies.ZEBRA: Color(0, 0, 0, 128),           # Black
        }
        return color_map.get(self, Color(0, 100, 255, 128))     # Fallback color (blue)

T = TypeVar('T', bound=Union["Plant", "Herbivore"])

HUNGER_RATE = 0.05
THIRST_RATE = 0.08 
AGE_RATE = 0.01
# DEBUG
# HUNGER_RATE = 0.01
# THIRST_RATE = 0.01
# AGE_RATE = 1.0

class Animal(ABC, Generic[T]):
    """Generic class for Animal that consumes T"""
    def __init__(
        self, 
        animal_id: int,
        species: AnimalSpecies, 
        position: Vector2, 
        speed: float,
        value: int, 
        lifespan: int
    ):
        self.animal_id: int         = animal_id
        self.species: AnimalSpecies = species
        self.position: Vector2      = position
        self.speed: float           = speed
        self.value: int             = value
        self.lifespan: int          = lifespan
        # Animal Stats
        self.age: float             = 0.0
        self.hunger: float          = 0.0   # 0.0 .. 10.0
        self.thirst: float          = 0.0   # 0.0 .. 10.0
        self.is_alive: bool         = True
        self.target: Vector2 | None = None
    
    def update(self, dt: float, board: "Board") -> None:
        self.is_alive = self.is_alive and self.age < self.lifespan and (self.hunger < 10.0 or self.thirst < 10.0)
        if self.is_alive:
            if not self.target or self.position.distance_to(self.target) < 0.2:
                self.target = Vector2(
                    random.uniform(0, board.width - 1),
                    random.uniform(0, board.height - 1)
                )
            self.move(self.target, dt)
        elif self in board.animals:
            board.animals.remove(self)

    def move(self, target: Vector2, dt: float):
        direction = target - self.position
        dist = direction.length()
        if dist == 0: return
        # normalize and step
        step = min(dist, self.speed * dt)
        self.position += direction.normalize() * step
    
    def add_age(self, dt: float):
        self.age = min(self.age + AGE_RATE*dt, self.lifespan)
    
    def add_hunger(self, dt: float):
        self.hunger = min(self.hunger + HUNGER_RATE*dt, 10.0)

    def add_thirst(self, dt: float):
        self.thirst = min(self.thirst + THIRST_RATE*dt, 10.0)

    def drink(self, source: "Pond") -> bool:
        if source.drink_from():
            self.thirst = max(self.thirst - 5.0, 0.0)
            return True
        return False

    @abstractmethod
    def consume(self, food: T) -> bool:
        pass
    
    def reproduce(self, target: "Animal", animal_id: int) -> Optional["Animal"]:
        if isinstance(target, self.__class__) and self.is_adult() and target.is_adult():
            offspring_pos = (self.position + target.position)/2
            offspring_lifespan = (self.lifespan + target.lifespan)//2
            return self.__class__(
                animal_id,
                self.species,
                offspring_pos,
                self.speed,
                self.value,
                offspring_lifespan
            )
        return None

    def is_adult(self) -> bool:
        return self.age >= (self.lifespan/2.0)