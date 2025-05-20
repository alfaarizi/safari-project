from my_safari_project.control.wildlife_ai import WildlifeAI
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger import Ranger
from pygame.math import Vector2


def test_ranger_exists():
    board = Board(10, 10)
    ranger = Ranger(id=1, name="Ranger1", salary=1000, position=Vector2(5, 5))
    board.rangers.append(ranger)
    assert len(board.rangers) == 1

def test_poacher_exists():
    board = Board(10, 10)
    poacher = Poacher(id=1, name="Poacher1", position=Vector2(5, 5))
    board.poachers.append(poacher)
    assert len(board.poachers) == 1

def test_multiple_poachers_exist():
    board = Board(10, 10)
    board.poachers.append(Poacher(id=1, name="Poacher1", position=Vector2(1, 1)))
    board.poachers.append(Poacher(id=2, name="Poacher2", position=Vector2(2, 2)))
    assert len(board.poachers) == 2

def test_multiple_rangers_exist():
    board = Board(10, 10)
    board.rangers.append(Ranger(id=1, name="Ranger1", salary=1000, position=Vector2(1, 1)))
    board.rangers.append(Ranger(id=2, name="Ranger2", salary=1000, position=Vector2(2, 2)))
    assert len(board.rangers) == 2

def test_ranger_poacher_interaction():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    board.rangers.append(Ranger(id=1, name="Ranger1", salary=1000, position=Vector2(5, 5)))
    board.poachers.append(Poacher(id=1, name="Poacher1", position=Vector2(5, 6)))
    ai.update(0.1)
    assert len(board.poachers) < 2

def test_capital_initial_amount():
    capital = Capital(1000)
    assert capital.currentBalance == 1000

def test_wildlife_ai_exists():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    assert isinstance(ai.board, Board)
    assert isinstance(ai.capital, Capital)