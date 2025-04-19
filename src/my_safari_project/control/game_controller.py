import random
from my_safari_project.model.timer import Timer 
from my_safari_project.model.timespeed import TimeSpeed
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger import Position, Ranger  # Adjusted module path
from my_safari_project.control.wildlife_ai import WildlifeAI

# -----------------------------------------------------------
# Enums / Simple Classes to Mimic UML or Basic Features
# -----------------------------------------------------------

class DifficultyLevel:
    """Simple utility for cycling difficulties."""
    LEVELS = ["Easy", "Medium", "Hard"]

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
    def __init__(self, board_width: int, board_height: int, init_balance: float, difficulty: DifficultyLevel):
        self.board = Board(board_width, board_height)
        self.board.initializeBoard()
        self.timer = Timer()  # Initialize the Timer
        self.capital = Capital(init_balance)
        self.wildlife_ai = WildlifeAI(self.board, self.capital)
        self.difficulty_level = difficulty
        self.number_of_visitors = 0
        self.game_state = GameState.PAUSED
        self.autosave_enabled = False
        self.day_night_cycle_enabled = False
        self.isometric_view_enabled = False
        self.last_autosave_time = 0.0
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
        if self.game_state == GameState.RUNNING:
            self.timer.updateTime(delta_time)
            self.board.updateAll(delta_time)
            self.wildlife_ai.update(delta_time)
            self.calculate_visitor_flow()
            self.handle_poacher_encounters()
            self.monthly_update

    def set_speed(self, speed: TimeSpeed):
        self.timer.setSpeedLevel(speed)

    def check_win_condition(self) -> bool:
        return False

    def check_lose_condition(self) -> bool:
        return self.capital.checkBankruptcy()

    def set_difficulty(self, level: DifficultyLevel):
        self.difficulty_level = level

    def toggle_day_night_cycle(self):
        self.day_night_cycle_enabled = not self.day_night_cycle_enabled

    def toggle_isometric_view(self):
        self.isometric_view_enabled = not self.isometric_view_enabled

    def spawn_poachers(self, num_poachers: int):
        for i in range(num_poachers):
            position = self.board.getField(random.randint(0, self.board.width-1), random.randint(0, self.board.height-1))
            poacher = Poacher(id=i, name=f"Poacher_{random.randint(i)}", position=position) 
            self.board.addPoacher(poacher)

    def deploy_rangers(self, num_rangers: int):
        for _ in range(num_rangers):
            position = Position(
                random.randint(0, self.board.width-1), 
                random.randint(0, self.board.height-1)
                )
            ranger = Ranger(
                id=random.randint(1000, 9999), 
                name=f"Ranger_{random.randint(100, 999)}", 
                salary=1000.0, 
                position=position
                )
            self.board.addRanger(ranger)

    def handle_poacher_encounters(self):
        for ranger in self.board.rangers:
            if not ranger.getisOnDuty(): continue
            for poacher in self.board.poachers:
                if poacher.isVisibleTo(ranger.position):
                    if ranger.eliminatePoacher(poacher):
                        self.board.removePoacher(poacher)

    def monthly_update(self):
        self.capital.updateMonthlyBudget()
        self.wildlife_ai.monthly_tick()

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
