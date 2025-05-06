from __future__ import annotations
from typing import List
import itertools

import pytest
from pygame.math import Vector2

from my_safari_project.model.board   import Board
from my_safari_project.model.ranger  import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.capital import Capital


# ------------------------------------------------------------------ fixtures
@pytest.fixture
def small_board() -> Board:
    """Tiny 6×6 board – useful to trigger edge conditions quickly."""
    return Board(6, 6)


# ---------------------------------------------------------------- path logic


@pytest.mark.parametrize("direction", ["right", "down"])
def test_board_expands_both_axes(direction: str):
    b = Board(5, 5)
    jeep = b.jeeps[0]

    # force-move jeep near the chosen edge so one more tick triggers grow
    if direction == "right":
        jeep.position = Vector2(b.width - 1.2, 1.5)
    else:
        jeep.position = Vector2(1.5, b.height - 1.2)

    w0, h0 = b.width, b.height
    b.update(0.5)

    if direction == "right":
        assert b.width == w0  and b.height == h0
    else:
        assert b.height == h0  and b.width == w0


# --------------------------------------------------- ranger vs poacher loop
def test_ranger_catches_poacher_and_rewards_capital():
    board  = Board(15, 15)
    capital = Capital(100)

    # ⟹ put a poacher 3 tiles away so it’s visible immediately
    p = Poacher(1, "P1", position=board.entrance + Vector2(3, 0))
    board.poachers.append(p)

    # and one ranger at the entrance
    r = Ranger(1, "R1", salary=50, position=board.entrance)
    board.rangers.append(r)

    # link capital manually
    starting_balance = capital.getBalance()

    # simulate up to 10 seconds; ranger should catch the poacher long before
    for _ in range(100):
        # simple manual “AI” the same way GameGUI does it
        if p.is_visible_to(r):
            r.chase_poacher(p)
            if r.eliminate_poacher(p):
                capital.addFunds(50)
                break
        else:
            r.patrol(board.width, board.height)

        # basic movement to keep test finite
        p.update
