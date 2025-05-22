
from my_safari_project.model.board import Board

def test_board_fields_correct():
    board = Board(10, 10)
    assert len(board.fields) == 10
    assert len(board.fields[0]) == 10

def test_board_longest_path_returns_valid_path():
    board = Board(10, 10)
    path = board._longest_path(board.entrances[0])
    assert isinstance(path, list)
    assert len(path) > 1
