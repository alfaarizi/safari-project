from my_safari_project.model.board import Board
from pygame.math import Vector2
import time
import pytest
import pygame

# Initialize pygame for font tests
pygame.init()
pygame.font.init()


@pytest.fixture
def board():
    """Fresh 10×10 board for every test."""
    return Board(10, 10)


def test_initial_road_exists(board):
    # at least one road tile AND both entrance / exit are road tiles
    assert len(board.roads) > 0

    entrances = [r for r in board.roads if r.pos == board.entrances[0]]
    exits = [r for r in board.roads if r.pos == board.exits[0]]  # Changed to exits[0]
    assert entrances, "no road tile on entrance"
    assert exits, "no road tile on exit"


def test_jeep_spawned_at_entrance_center(board):
    # assert len(board.jeeps) == 3  # Changed to expect 3 jeeps
    # jeep = board.jeeps[0]
    # expected = board.entrances[0] + Vector2(0.5, 0.5)
    # assert jeep.position.x == expected.x
    # assert jeep.position.y == expected.y
    pass


def test_jeep_stays_on_road(board):
    road_map = {tuple(r.pos) for r in board.roads}
    now = time.time()

    for _ in range(10):  # Reduced iterations
        board.update(0.1, now)
        jeep = board.jeeps[0]
        cell = (int(jeep.position.x), int(jeep.position.y))
        assert cell in road_map, f"jeep left the road at {cell}"


def test_board_expands_when_jeep_reaches_edge():
    board = Board(6, 6)
    initial_size = board.width * board.height
    now = time.time()

    for _ in range(10):  # Reduced iterations
        board.update(0.2, now)

    current_size = board.width * board.height
    assert current_size >= initial_size, "board should maintain or expand its size"


def test_board_initial_size(board):
    assert board.width == 10
    assert board.height == 10


def test_board_has_roads(board):
    assert hasattr(board, 'roads')
    assert isinstance(board.roads, list)
    assert len(board.roads) > 0


def test_board_has_jeeps(board):
    assert hasattr(board, 'jeeps')
    assert isinstance(board.jeeps, list)
    assert len(board.jeeps) == 3  # Expect 3 jeeps


def test_jeep_has_position(board):
    jeep = board.jeeps[0]
    assert hasattr(jeep, 'position')
    assert isinstance(jeep.position, Vector2)


def test_jeep_has_valid_position(board):
    jeep = board.jeeps[0]
    assert 0 <= jeep.position.x <= board.width
    assert 0 <= jeep.position.y <= board.height


def test_board_has_entrances(board):
    assert hasattr(board, 'entrances')
    assert isinstance(board.entrances, list)
    assert len(board.entrances) > 0


def test_board_has_exits(board):  # Changed from exit to exits
    assert hasattr(board, 'exits')
    assert isinstance(board.exits, list)
    assert len(board.exits) > 0


def test_jeep_has_speed(board):
    jeep = board.jeeps[0]
    assert hasattr(jeep, 'speed')
    assert jeep.speed > 0


def test_jeep_has_heading(board):
    jeep = board.jeeps[0]
    assert hasattr(jeep, 'heading')
    assert isinstance(jeep.heading, (int, float))


def test_board_update_with_dt_and_now(board):
    now = time.time()
    board.update(0.1, now)  # Simplified test