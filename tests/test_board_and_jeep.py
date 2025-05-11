from pygame.math import Vector2
import pytest

from my_safari_project.model.board import Board


@pytest.fixture
def board():
    """Fresh 10×10 board for every test."""
    return Board(10, 10)          # entrance=(0,1) exit=(9,8)


# ---------------------------------------------------------------------- roads
def test_initial_road_exists(board):
    # at least one road tile AND both entrance / exit are road tiles
    assert len(board.roads) > 0

    entrances = [r for r in board.roads if r.pos == board.entrance]
    exits     = [r for r in board.roads if r.pos == board.exit]
    assert entrances, "no road tile on entrance"
    assert exits,     "no road tile on exit"


# ---------------------------------------------------------------------- jeep
def test_jeep_spawned_at_entrance_center(board):
    assert len(board.jeeps) == 1
    jeep = board.jeeps[0]

    expected = board.entrance + Vector2(0.5, 0.5)
    assert jeep.position == expected


def test_jeep_stays_on_road(board):
    road_map = {tuple(r.pos) for r in board.roads}

    for _ in range(100):
        board.update(0.1)
        jeep = board.jeeps[0]
        cell = (int(jeep.position.x), int(jeep.position.y))
        assert cell in road_map, f"jeep left the road at {cell}"


def test_board_expands_when_jeep_reaches_edge():
    board = Board(6, 6)
    initial_w, initial_h = board.width, board.height

    for _ in range(200):
        board.update(0.2)         # 40 real seconds in total
        if board.width > initial_w or board.height > initial_h:
            break

    assert board.width  > initial_w or board.height > initial_h, \
           "board did not expand after jeep reached an edge"
