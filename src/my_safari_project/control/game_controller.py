import random
from enum import Enum

from pygame import Vector2

from my_safari_project.model.timer import Timer
from my_safari_project.model.timespeed import TimeSpeed
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger import Ranger  # Adjusted module path
from my_safari_project.control.wildlife_ai import WildlifeAI

# -----------------------------------------------------------
# Enums / Simple Classes to Mimic UML or Basic Features
# -----------------------------------------------------------


class DifficultyLevel(Enum):
    EASY   = "Easy"
    NORMAL = "Normal"
    HARD   = "Hard"

    @property
    def thresholds(self):
        # visitors, herbivores, carnivores, capital
        return {
            DifficultyLevel.EASY:   ( 10, 10, 10,  500.0),
            DifficultyLevel.NORMAL: (20, 20, 20, 1000.0),
            DifficultyLevel.HARD:   (30, 30, 30, 2000.0),
        }[self]

    @property
    def required_months(self):
        return {
            DifficultyLevel.EASY:   3,
            DifficultyLevel.NORMAL: 6,
            DifficultyLevel.HARD:   12,
        }[self]

class GameState:
    RUNNING = "Running"
    PAUSED = "Paused"

class DayPhase:
    DAY = "Day"
    NIGHT = "Night"

# -----------------------------------------------------------
# Main GameController
# -----------------------------------------------------------

class GameController:
    def __init__(
        self,
        board_width: int,
        board_height: int,
        init_balance: float,
        difficulty: DifficultyLevel
    ):
        self.board = Board(board_width, board_height)
        self.board.initializeBoard()
        self.timer = Timer() 
        self.capital = Capital(init_balance)
        self.wildlife_ai = WildlifeAI(self.board, self.capital)
        # difficulty setup
        self.difficulty_level = difficulty
        self.visits_req, self.herb_req, self.carn_req, self.cap_req = difficulty.thresholds
        self.months_needed    = difficulty.required_months
        self.consec_success   = 0

        self.number_of_visitors = 0
        self.game_state = GameState.PAUSED
        self.won                = False
        self.lost               = False

        self.start_game()
    
    def start_game(self):
        self.game_state = GameState.RUNNING

    def pause_game(self):
        self.game_state = GameState.PAUSED

    def resume_game(self):
        if self.game_state == GameState.PAUSED:
            self.game_state = GameState.RUNNING

    def end_game(self):
        self.game_state = GameState.PAUSED

    def update(self, delta_time: float):
        if self.game_state != GameState.RUNNING:
            return

        self.timer.updateTime(delta_time)
        self.board.updateAll(delta_time)
        self.wildlife_ai.update(delta_time)
        self.calculate_visitor_flow()
        self.handle_poacher_encounters()
        # monthly update every 30*24 hours
        if self.timer.getCurrentTime() >= 30 * 24:
            self._monthly_update()
            self.timer.currentTime -= 30 * 24

        # check lose: bankruptcy or no animals left
        if self.capital.checkBankruptcy():
            self.lost = True
            self.game_state = GameState.PAUSED
        if not any(a for a in self.board.animals if a.is_alive()):
            self.lost = True
            self.game_state = GameState.PAUSED

    def set_speed(self, speed: TimeSpeed):
        self.timer.setSpeedLevel(speed)

    def check_win_condition(self) -> bool:
        return self.won

    def check_lose_condition(self) -> bool:
        return self.lost

    
    def applyDifficulty(self):
        """Map your difficulty to day/night lengths (seconds)."""
        if self.difficulty_level == DifficultyLevel.LEVELS[0]:  # Easy
            self.timer.dayLength   = 8 * 60
            self.timer.nightLength = 4 * 60
        elif self.difficulty_level == DifficultyLevel.LEVELS[1]:  # Medium
            self.timer.dayLength   = 6 * 60
            self.timer.nightLength = 3 * 60
        else:  # Hard
            self.timer.dayLength   = 4 * 60
            self.timer.nightLength = 2 * 60

    def set_difficulty(self, level: DifficultyLevel):
        self.difficulty = level

    def toggle_day_night_cycle(self):
        self.day_night_cycle_enabled = not self.day_night_cycle_enabled

    def toggle_isometric_view(self):
        self.isometric_view_enabled = not self.isometric_view_enabled

    def spawn_poachers(self, num_poachers: int):
        for i in range(num_poachers):
            position = self.board.getField(
                random.randint(0, self.board.width-1),
                random.randint(0, self.board.height-1)
            )
            poacher = Poacher(
                id=i,
                name=f"Poacher_{random.randint(i,999)}",
                position=position
            )
            self.board.addPoacher(poacher)

    def deploy_rangers(self, num_rangers: int):
        """
        Spawn `num_rangers` new Rangers at random tiles on the board.
        """
        for _ in range(num_rangers):
            # pick a random tile‐center
            pos = Vector2(
                random.randint(0, self.board.width - 1) + 0.5,
                random.randint(0, self.board.height - 1) + 0.5,
            )

            # give them a consecutive ID and a name
            rid   = len(self.board.rangers) + 1
            name  = f"R{rid}"
            salary = 100.0  # or whatever your default is

            ranger = Ranger(
                id       = rid,
                name     = name,
                salary   = salary,
                position = pos,
                vision   = 5.0,   # optional override
                speed    = 2.0,   # optional override
            )

            # add to the board
            self.board.addRanger(ranger)

    def handle_poacher_encounters(self):
        for ranger in self.board.rangers:
            if not ranger.is_on_duty:
                continue
            for poacher in list(self.board.poachers):
                if poacher.is_visible_to(ranger):
                    if ranger.eliminate_poacher(poacher):
                        self.board.removePoacher(poacher)

    def month_tick(self):
        pass

    def _monthly_update(self):
        # pay salaries, update budget, wildlife monthly
        self.capital.monthlyExpenses = sum(r.salary for r in self.board.rangers)
        self.capital.monthlyIncome   = 0
        self.capital.updateMonthlyBudget()
        self.wildlife_ai.monthly_tick()

        # couting things to check win condition
        visitors   = len([j for j in self.board.jeeps if not j.is_available and j.current_passengers == 0])
        herbivores = len([a for a in self.board.animals if a.__class__.__name__=="Herbivore" and a.is_alive()])
        carnivores = len([a for a in self.board.animals if a.__class__.__name__=="Carnivore" and a.is_alive()])
        capital    = self.capital.getBalance()

        if (visitors >= self.visits_req and
            herbivores >= self.herb_req and
            carnivores >= self.carn_req and
            capital >= self.cap_req):
            self.consec_success += 1
        else:
            self.consec_success = 0

        if self.consec_success >= self.months_needed:
            self.won = True
            self.game_state = GameState.PAUSED

    def calculate_visitor_flow(self):
        pass

    def save_game(self, file_path: str):
        pass

    def load_game(self, file_path: str):
        pass

    def get_board(self) -> Board:
        return self.board

    def get_timer(self) -> Timer:
        return self.timer

    def get_capital(self) -> Capital:
        return self.capital
    
    def add_funds_to_capital(self, amount: float):
        self.capital.addFunds(amount)

    def deduct_funds_from_capital(self, amount: float) -> bool:
        return self.capital.deductFunds(amount)

    def is_game_over(self) -> bool:
        return self.won or self.lost
