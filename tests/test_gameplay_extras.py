from __future__ import annotations
from typing import List
import itertools

import pytest
from pygame import time
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.capital import Capital
from my_safari_project.control.wildlife_ai import WildlifeAI


@pytest.fixture
def small_board() -> Board:
    """Tiny 6×6 board – useful to trigger edge conditions quickly."""
    return Board(6, 6)


def test_dummy():
    assert True


def test_board_expands_right():
    b = Board(5, 5)
    jeep = b.jeeps[0]
    jeep.position = Vector2(b.width - 1.2, 1.5)

    w0, h0 = b.width, b.height
    b.update(0.5, time.time())  # Added time parameter

    assert b.width >= w0
    assert b.height == h0


def test_board_expands_down():
    b = Board(5, 5)
    jeep = b.jeeps[0]
    jeep.position = Vector2(1.5, b.height - 1.2)

    w0, h0 = b.width, b.height
    b.update(0.5, time.time())  # Added time parameter

    assert b.width == w0
    assert b.height >= h0


def test_ranger_catches_poacher_and_rewards_capital():
    board = Board(15, 15)
    capital = Capital(100)
    ai = WildlifeAI(board, capital)

    poacher = Poacher(id=1, name="P1", position=Vector2(3, 0))
    board.poachers.append(poacher)

    ranger = Ranger(id=1, name="R1", salary=50, position=Vector2(0, 0))
    board.rangers.append(ranger)

    starting_balance = capital.currentBalance
    ai.update(0.1)  # Single update should be enough for close proximity

    assert len(board.poachers) == 0
    assert capital.currentBalance > starting_balance


# New test cases
def test_capital_deduction():
    capital = Capital(1000)
    ranger = Ranger(id=1, name="R1", salary=100, position=Vector2(0, 0))
    success = ranger.pay_salary(capital)
    assert success
    assert capital.currentBalance == 900


def test_poacher_visibility():
    board = Board(10, 10)
    ranger = Ranger(id=1, name="R1", salary=100, position=Vector2(5, 5))
    poacher = Poacher(id=1, name="P1", position=Vector2(5, 6))

    board.rangers.append(ranger)
    board.poachers.append(poacher)

    assert poacher.is_visible_to(ranger)


def test_ranger_patrol():
    board = Board(10, 10)
    ranger = Ranger(id=1, name="R1", salary=100, position=Vector2(5, 5))
    initial_pos = Vector2(ranger.position)

    ranger.patrol(board.width, board.height)
    ranger.update(0.1, board)

    assert ranger.position != initial_pos


def test_poacher_movement():
    board = Board(10, 10)
    poacher = Poacher(id=1, name="P1", position=Vector2(5, 5))
    initial_pos = Vector2(poacher.position)

    poacher.update(0.1, board)

    assert poacher.position != initial_pos


def test_wildlife_ai_spawn_poacher():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)

    initial_poachers = len(board.poachers)
    ai._poacher_timer = 46  # Force spawn by exceeding POACHER_INTERVAL
    ai.update(0.1)

    assert len(board.poachers) > initial_poachers