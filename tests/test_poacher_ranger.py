from my_safari_project.control.wildlife_ai import WildlifeAI
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger import Ranger
from pygame.math import Vector2


def test_ranger_exists():
    board = Board(10, 10)
    ranger = Ranger(position=Vector2(5, 5), name="Ranger1", salary=1000)
    board.rangers.append(ranger)
    assert len(board.rangers) == 1

def test_poacher_exists():
    board = Board(10, 10)
    poacher = Poacher(name="Poacher1", position=Vector2(5, 5))
    board.poachers.append(poacher)
    assert len(board.poachers) == 1

def test_multiple_poachers_exist():
    board = Board(10, 10)
    board.poachers.append(Poacher(name="Poacher1", position=Vector2(1, 1)))
    board.poachers.append(Poacher(name="Poacher2", position=Vector2(2, 2)))
    assert len(board.poachers) == 2

def test_multiple_rangers_exist():
    board = Board(10, 10)
    board.rangers.append(Ranger(name="Ranger1", salary=1000, position=Vector2(1, 1)))
    board.rangers.append(Ranger(name="Ranger2", salary=1000, position=Vector2(2, 2)))
    assert len(board.rangers) == 2

def test_ranger_poacher_interaction():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    board.rangers.append(Ranger(name="Ranger1", salary=1000, position=Vector2(5, 5)))
    board.poachers.append(Poacher(name="Poacher1", position=Vector2(5, 6)))
    ai.update(0.1)
    assert len(board.poachers) < 2

def test_capital_initial_amount():
    capital = Capital(1000)
    assert capital.currentBalance == 1000

def test_capital_reward():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    initial_balance = capital.currentBalance
    board.rangers.append(Ranger(name="Ranger1", salary=1000, position=Vector2(5, 5)))
    board.poachers.append(Poacher(name="Poacher1", position=Vector2(5, 5)))
    ai.update(0.1)
    assert capital.currentBalance > initial_balance

def test_poacher_movement():
    poacher = Poacher(name="Poacher1", position=Vector2(5, 5))
    initial_pos = Vector2(poacher.position)
    poacher.move(0.1)
    assert poacher.position != initial_pos

def test_ranger_movement():
    ranger = Ranger(name="Ranger1", salary=1000, position=Vector2(5, 5))
    initial_pos = Vector2(ranger.position)
    ranger.move(0.1)
    assert ranger.position != initial_pos

def test_wildlife_ai_exists():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    assert isinstance(ai.board, Board)
    assert isinstance(ai.capital, Capital)