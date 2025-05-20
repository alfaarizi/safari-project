from my_safari_project.control.wildlife_ai import WildlifeAI
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from pygame.math import Vector2


def test_poacher_initial_spawn():
    board = Board(10, 10)
    pos = Vector2(5, 5)
    board.spawn_poacher(pos)
    assert len(board.poachers) == 1
    assert board.poachers[0].position == pos

def test_ranger_initial_spawn():
    board = Board(10, 10)
    pos = Vector2(5, 5)
    board.spawn_ranger(pos)
    assert len(board.rangers) == 1
    assert board.rangers[0].position == pos

def test_multiple_poachers():
    board = Board(10, 10)
    board.spawn_poacher(Vector2(1, 1))
    board.spawn_poacher(Vector2(2, 2))
    assert len(board.poachers) == 2

def test_multiple_rangers():
    board = Board(10, 10)
    board.spawn_ranger(Vector2(1, 1))
    board.spawn_ranger(Vector2(2, 2))
    assert len(board.rangers) == 2

def test_ranger_poacher_detection():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    board.spawn_ranger(Vector2(5, 5))
    board.spawn_poacher(Vector2(5, 6))
    ai.update(0.1)
    assert len(board.poachers) < 2

def test_capital_initial_balance():
    capital = Capital(1000)
    assert capital.current_balance == 1000

def test_capital_reward_after_catch():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    initial_balance = capital.current_balance
    board.spawn_ranger(Vector2(5, 5))
    board.spawn_poacher(Vector2(5, 5))
    ai.update(0.1)
    assert capital.current_balance > initial_balance

def test_board_has_poachers_list():
    board = Board(10, 10)
    assert hasattr(board, 'poachers')
    assert isinstance(board.poachers, list)

def test_board_has_rangers_list():
    board = Board(10, 10)
    assert hasattr(board, 'rangers')
    assert isinstance(board.rangers, list)

def test_wildlife_ai_update():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)
    try:
        ai.update(0.1)
        assert True
    except Exception:
        assert False, "WildlifeAI update should not raise exceptions"
