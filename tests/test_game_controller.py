import pytest
from pygame.math import Vector2
from my_safari_project.control.game_controller import GameController, DifficultyLevel

@pytest.fixture
def controller():
    return GameController(DifficultyLevel.NORMAL)


def test_enter_and_exit_chip_mode(controller):
    controller.enter_chip_mode()
    assert controller.chip_placement_mode is True

def test_spawn_ranger(controller):
    initial_count = len(controller.board.rangers)
    controller.spawn_ranger(Vector2(1, 1))
    assert len(controller.board.rangers) == initial_count + 1

def test_spawn_plant(controller):
    initial_count = len(controller.board.plants)
    controller.spawn_plant(Vector2(2, 2))
    assert len(controller.board.plants) == initial_count + 1

def test_spawn_pond(controller):
    initial_count = len(controller.board.ponds)
    controller.spawn_pond(Vector2(3, 3))
    assert len(controller.board.ponds) == initial_count + 1

def test_spawn_animal_valid_species(controller):
    controller.spawn_animal("zebra", Vector2(4, 4))
    assert any(a.species.name == "ZEBRA" for a in controller.board.animals)

def test_spawn_poacher(controller):
    initial = len(controller.board.poachers)
    controller.spawn_poacher()
    assert len(controller.board.poachers) == initial + 1
