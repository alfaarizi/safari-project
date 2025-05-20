from __future__ import annotations
import pytest
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.capital import Capital
from my_safari_project.control.wildlife_ai import WildlifeAI


class TestGameplayBasic:
    def test_board_creation(self):
        board = Board(10, 10)
        assert board.width == 10
        assert board.height == 10

    def test_board_has_roads(self):
        board = Board(10, 10)
        assert len(board.roads) > 0

    def test_board_has_jeeps(self):
        board = Board(10, 10, n_jeeps=3)
        assert len(board.jeeps) == 3

    def test_capital_initial_balance(self):
        capital = Capital(1000)
        assert capital.currentBalance == 1000

    def test_capital_add_funds(self):
        capital = Capital(1000)
        capital.addFunds(500)
        assert capital.currentBalance == 1500

    def test_capital_deduct_funds(self):
        capital = Capital(1000)
        success = capital.deductFunds(300)
        assert success
        assert capital.currentBalance == 700

    def test_ranger_creation(self):
        ranger = Ranger(id=1, name="Test", salary=100, position=Vector2(5, 5))
        assert ranger.name == "Test"
        assert ranger.salary == 100

    def test_poacher_creation(self):
        poacher = Poacher(id=1, name="Bad", position=Vector2(3, 3))
        assert poacher.name == "Bad"
        assert not poacher.captured

    def test_ranger_speed(self):
        ranger = Ranger(id=1, name="Fast", salary=100, position=Vector2(0, 0), speed=2.0)
        assert ranger.speed == 2.0

    def test_poacher_visibility_radius(self):
        ranger = Ranger(id=1, name="R1", salary=100, position=Vector2(0, 0), vision=5.0)
        poacher = Poacher(id=1, name="P1", position=Vector2(4, 0))
        assert poacher.is_visible_to(ranger)

    def test_capital_bankruptcy(self):
        capital = Capital(100)
        capital.deductFunds(100)
        assert capital.checkBankruptcy()

    def test_wildlife_ai_creation(self):
        board = Board(10, 10)
        capital = Capital(1000)
        ai = WildlifeAI(board, capital)
        assert ai.board == board
        assert ai.capital == capital

    def test_ranger_initial_stats(self):
        ranger = Ranger(id=1, name="R1", salary=100, position=Vector2(0, 0))
        assert ranger.poachers_caught == 0
        assert ranger.assigned_poacher is None

    def test_poacher_initial_stats(self):
        poacher = Poacher(id=1, name="P1", position=Vector2(0, 0))
        assert poacher.animals_caught == 0
        assert poacher.is_hunting

    def test_board_boundaries(self):
        board = Board(5, 5)
        assert 0 <= board.entrances[0].x < board.width
        assert 0 <= board.entrances[0].y < board.height