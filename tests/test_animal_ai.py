import pytest
from pygame.math import Vector2
from my_safari_project.model.board import Board
from my_safari_project.model.herbivore import Herbivore
from my_safari_project.model.pond import Pond
from my_safari_project.model.plant import Plant
from my_safari_project.control.animal_ai import AnimalAI, AnimalState


@pytest.fixture
def board():
    b = Board(10, 10)
    b.animals.clear()
    return b

@pytest.fixture
def animal(board):
    herb = Herbivore(1, species=herb_species(), position=Vector2(2, 2), speed=1.0, value=100, lifespan=50)
    board.animals.append(herb)
    return herb

@pytest.fixture
def ai(board):
    return AnimalAI(board)

def herb_species():
    from my_safari_project.model.animal import AnimalSpecies
    return AnimalSpecies.ZEBRA




def test_add_hunger_thirst_and_age(ai, animal):
    prev_hunger = animal.hunger
    prev_thirst = animal.thirst
    prev_age = animal.age
    ai.update(1.0)
    assert animal.hunger > prev_hunger
    assert animal.thirst > prev_thirst
    assert animal.age > prev_age


def test_water_memory_and_state_change(ai, board, animal):
    pond = Pond(1, Vector2(2, 3))
    board.ponds.append(pond)
    animal.thirst = 10
    ai.update(1.0)
    status = ai.animal_states[animal.animal_id]
    assert status.state in (AnimalState.SEEKING_WATER, AnimalState.DRINKING)


def test_food_memory_and_state_change(ai, board, animal):
    plant = Plant(1, Vector2(2, 3))
    board.plants.append(plant)
    animal.hunger = 10
    ai.update(1.0)
    status = ai.animal_states[animal.animal_id]
    assert status.state in (AnimalState.SEEKING_FOOD, AnimalState.EATING)




