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
    initial_pos = Vector2(5, 5)

    # Force movement by setting target and updating multiple times
    poacher._target = Vector2(8, 8)  # Set a target away from initial position
    for _ in range(5):  # Update multiple times to ensure movement
        poacher.update(0.1, board)

    assert poacher.position.x != initial_pos.x or poacher.position.y != initial_pos.y


def test_wildlife_ai_spawn_poacher():
    board = Board(10, 10)
    capital = Capital(1000)
    ai = WildlifeAI(board, capital)

    initial_poachers = len(board.poachers)
    ai._poacher_timer = 46  # Force spawn by exceeding POACHER_INTERVAL
    ai.update(0.1)

    assert len(board.poachers) > initial_poachers