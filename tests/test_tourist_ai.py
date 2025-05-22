import pytest
from pygame.math import Vector2
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.control.tourist_ai import TouristAI
from my_safari_project.model.tourist import Tourist
from my_safari_project.model.herbivore import Herbivore
from my_safari_project.model.animal import AnimalSpecies


@pytest.fixture
def board():
    return Board(10, 10)

@pytest.fixture
def capital():
    return Capital(1000)

@pytest.fixture
def ai(board, capital):
    return TouristAI(board, capital)


def test_calculate_spawn_interval_no_animals(ai):
    assert ai._calculate_spawn_interval() == ai._base_tourist_interval


def test_calculate_spawn_interval_with_animals(ai, board):
    board.animals.append(Herbivore(1, AnimalSpecies.ZEBRA, Vector2(1, 1), 1.0, 100, 20))
    interval = ai._calculate_spawn_interval()
    assert interval < ai._base_tourist_interval


def test_calculate_spawn_batch_size_none(ai):
    assert ai._calculate_spawn_batch_size() == 1


def test_calculate_spawn_batch_size_high_diversity(ai, board):
    species = [AnimalSpecies.ZEBRA, AnimalSpecies.HIPPO, AnimalSpecies.GIRAFFE, AnimalSpecies.BUFFALO, AnimalSpecies.ELEPHANT, AnimalSpecies.LION]
    for i, sp in enumerate(species):
        board.animals.append(Herbivore(i, sp, Vector2(i, i), 1.0, 100, 20))
    size = ai._calculate_spawn_batch_size()
    assert size == 3


def test_spawn_tourist_adds_to_board(ai, board):
    ai._spawn_tourist()
    assert len(board.tourists) > 0





def test_update_moves_and_rewards_tourist(ai, board, capital):
    ai._spawn_tourist()
    t = board.tourists[0]
    t.movement_state = "exiting"
    t.timer = 0.0
    t.seen_animals.add(1)
    start_balance = capital.currentBalance

    ai.update(1.0)

    assert capital.currentBalance > start_balance
    assert t not in board.tourists
