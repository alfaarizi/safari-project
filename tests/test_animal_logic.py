import pytest
from pygame.math import Vector2
from my_safari_project.model.animal import AnimalSpecies
from my_safari_project.model.herbivore import Herbivore
from my_safari_project.model.plant import Plant
from my_safari_project.model.pond import Pond
from my_safari_project.model.board import Board

@pytest.fixture
def board():
    return Board(10, 10)

def test_animal_creation_and_stats():
    animal = Herbivore(1, AnimalSpecies.ZEBRA, Vector2(2, 3), speed=1.0, value=100, lifespan=50)
    assert animal.is_alive
    assert animal.hunger == 0.0
    assert animal.thirst == 0.0
    assert animal.age == 0.0


def test_animal_hunger_and_thirst_limits():
    animal = Herbivore(2, AnimalSpecies.ELEPHANT, Vector2(1, 1), speed=1.0, value=100, lifespan=50)
    for _ in range(100):
        animal.add_hunger(1.0)
        animal.add_thirst(1.0)
    assert animal.hunger <= 10.0
    assert animal.thirst <= 10.0

def test_animal_drinks_successfully():
    animal = Herbivore(3, AnimalSpecies.BUFFALO, Vector2(1, 1), speed=1.0, value=100, lifespan=50)
    pond = Pond(1, Vector2(1, 1))
    assert animal.drink(pond)
    assert pond.water_level == 4

def test_animal_fails_to_drink_empty_pond():
    animal = Herbivore(3, AnimalSpecies.HIPPO, Vector2(1, 1), speed=1.0, value=100, lifespan=50)
    pond = Pond(1, Vector2(1, 1))
    pond.water_level = 0
    assert not animal.drink(pond)

def test_animal_consumes_plant():
    animal = Herbivore(4, AnimalSpecies.ZEBRA, Vector2(1, 1), speed=1.0, value=100, lifespan=50)
    plant = Plant(1, Vector2(1, 1))
    animal.hunger = 5.0
    success = animal.consume(plant)
    assert success
    assert plant.nutrition_level == 4
    assert animal.hunger < 5.0

def test_animal_reproduce_successfully():
    a1 = Herbivore(5, AnimalSpecies.ELEPHANT, Vector2(1, 1), 1.0, 100, 20)
    a2 = Herbivore(6, AnimalSpecies.ELEPHANT, Vector2(2, 1), 1.0, 100, 20)
    a1.age = a2.age = 10  # make both adults
    offspring = a1.reproduce(a2, 10)
    assert offspring is not None
    assert isinstance(offspring, Herbivore)
    assert offspring.position != a1.position
