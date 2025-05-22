import pytest
from pygame.math import Vector2
from my_safari_project.model.jeep import Jeep
from my_safari_project.model.board import Board
from my_safari_project.model.tourist import Tourist


@pytest.fixture
def board():
    b = Board(10, 10)
    b.waiting_tourists.clear()
    return b

@pytest.fixture
def jeep(board):
    j = Jeep(1, Vector2(0, 0))
    j.board = board
    j.set_path([Vector2(0, 0), Vector2(1, 0), Vector2(2, 0)])
    return j


def test_jeep_set_path_heading():
    j = Jeep(1, Vector2(0, 0))
    j.set_path([Vector2(0, 0), Vector2(3, 0)])
    assert j.heading == 0



def test_jeep_pickup_tourist(board):
    jeep = board.jeeps[0]
    jeep.position = board.entrances[0]
    t = Tourist(1, Vector2(jeep.position), board)
    board.waiting_tourists.append(t)
    jeep.update(0.1, 0.0, [j for j in board.jeeps if j != jeep])
    assert len(jeep.tourists) == 1
    assert t not in board.waiting_tourists




def test_jeep_path_end_detected():
    j = Jeep(1, Vector2(0, 0))
    j.set_path([Vector2(0, 0), Vector2(2, 0)])
    j._path_index = len(j._path) - 1
    assert j.at_path_end()
