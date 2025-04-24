from pygame.math import Vector2
from abc import ABC
from typing import List, TypeVar, Generic, Union, Optional, TYPE_CHECKING
from enum import Enum

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

T = TypeVar('T', bound=Union["Plant", "Herbivore"])

class Animal(ABC, Generic[T]):
    """Generic class for Animal that consumes T"""
    def __init__(
        self, 
        animal_id: int,
        species: AnimalSpecies, 
        position: Vector2, 
        speed: float,
        value: int, 
        age: int, 
        lifespan: int
    ):
        self.animal_id: int = animal_id
        self.species: AnimalSpecies = species
        self.position: Vector2 = position
        self.speed: float = speed
        self.value: int = value
        self.age: int = age
        self.lifespan: int = lifespan
        self.alive: bool = True
        self.hunger: int = 0 # {0..10}
        self.thirst: int = 0 # {0..10}

    def move(self, target: Vector2):
        direction = target - self.position
        dist = direction.length()
        if dist == 0:
            return
        # normalize and step
        step = min(dist, self.speed)
        self.position += direction.normalize() * step

    def get_surroundings(self, board: "Board") -> List["Field"]:
        """Returns the nearby fields on the board."""
        return board.get_neighbors(Field(self.position.x, self.position.y))

    def add_hunger(self):
        self.hunger = min(self.hunger + 1, 10)

    def add_thirst(self):
        self.thirst = min(self.thirst + 1, 10)
    
    def search_food(self, foods: List[T]) ->  List[T]:
        """Search for nearby food (within distance 10)"""
        return [f for f in foods if self.position.distance_to(f.position) < 10.0]

    def consume(self, food: T) -> bool:
        """Consume food if within range (distance 5)"""
        if self.position.distance_to(food.position) < 5:
            self.hunger = max(self.hunger - 1, 0)
            return True
        return False

    def drink(self, source: "Pond"):
        """Drink water if within range (distance 5)"""
        if self.position.distance_to(source.position) < 5:
            self.thirst = max(self.thirst - 1, 0)
            return True
        return False
    
    def reproduce(self, target: "Animal") -> Optional["Animal"]:
        """Reproduce if target is the same species and both are adults"""
        if isinstance(target, self.__class__) and self.is_adult() and target.is_adult():
            return self.__class__(
                self.animal_id,
                self.species, 
                self.position, 
                self.speed, 
                self.value, 
                0,
                self.lifespan
            )
        return None
    
    def migrate(self, group: List["Animal"]):
        """Move self based on the average position of the group"""
        if group:
            self.move(sum((animal.position for animal in group), Vector2()) / len(group))

    def is_alive(self) -> bool:
        """Check if the animal is still alive"""
        return self.alive and (self.age < self.lifespan and self.hunger > 0 and self.thirst > 0)

    def is_adult(self) -> bool:
        """Check if the animal is an adult (lived more than half of lifespan)"""
        return self.age >= (self.lifespan // 2)
