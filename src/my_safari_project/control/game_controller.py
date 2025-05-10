import random
from enum import Enum
from pygame.math import Vector2

# Model
from my_safari_project.model.timer import Timer, TIME_SCALE
from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger import Ranger
# View
# inside __init__ since it causes circular imports
# Control
from my_safari_project.control.wildlife_ai import WildlifeAI

# -----------------------------------------------------------
# Enums / Simple Classes to Mimic UML or Basic Features
# -----------------------------------------------------------

class DifficultyLevel(Enum):
    EASY   = 0
    NORMAL = 1
    HARD   = 2

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

RANGER_COST = 150
PLANT_COST = 20
POND_COST = 200
# Carnivores
HYENA_COST = 60
LION_COST = 150
TIGER_COST = 180
# Herbivores
BUFFALO_COST = 100
ELEPHANT_COST = 300
GIRAFFE_COST = 150
HIPPO_COST = 175
ZEBRA_COST = 130

# -----------------------------------------------------------
# Main GameController
# -----------------------------------------------------------

class GameController:
    def __init__(self, difficulty: DifficultyLevel):
        # Difficulty-based parameters
        self.difficulty = difficulty
        init_balance, self._poacher_lvl, self._max_poachers = ([
            (1500.0, 30.0, 4),
            (1000.0, 20.0, 6),
            (500.0, 10.0, 8)
        ][difficulty.value])
        self.visits_req, self.herb_req, self.carn_req, self.cap_req = difficulty.thresholds
        self.months_needed      = difficulty.required_months
        self.num_visitors       = 0
        self.consec_success     = 0
        self.won                = False
        self.lost               = False
        
        # MODEL
        self.board      : Board             = Board(45, 40)
        self.capital    : Capital           = Capital(init_balance)
        self.timer      : Timer             = Timer()    # global timer
        self.game_state : GameState | None  = None
        self.running    : bool              = True

        # VIEW
        from my_safari_project.view.gamegui import GameGUI
        self.game_gui = GameGUI(self)

        # Control
        self.wildlife_ai = WildlifeAI(self.board, self.capital)

        # HELPER TIMERS
        self._poacher_timer = 0.0
        self._last_month_time = 0.0

    def run(self):
        while self.running:
            raw_dt      = self.timer.tick() # tick() returns real‐dt and internally advances game‐time
            dt          = min(raw_dt, 0.02) # clamp to avoid large jumps
            self._update_sim(dt)
            self.game_gui.update(dt)
        self.game_gui.exit()

    # -- Simulation Update  -------------------------------------------
    
    def _update_sim(self, dt: float):
        # check lose: bankruptcy or no animals left
        if self.capital.checkBankruptcy():
            self.lost = True
            self.game_state = GameState.PAUSED
        if not any(a for a in self.board.animals if a.is_alive):
            self.lost = True
            self.game_state = GameState.PAUSED

        # check for monthly update
        if self.timer.elapsed_seconds - self._last_month_time >= TIME_SCALE["month"]:
            self._monthly_update()
            self._last_month_time += TIME_SCALE["month"]

        # board entities (jeeps grow / move)
        self.board.update(dt)
        self.wildlife_ai.update(dt)

        self.calculate_visitor_flow()
        

        # auto-spawn poachers
        if len(self.board.poachers) < self._max_poachers:
            self._poacher_timer += dt
            if self._poacher_timer >= self._poacher_lvl:
                self._poacher_timer = 0.0
                self.spawn_poacher()

        # move poachers & rangers & animals
        for p in self.board.poachers:
            p.update(dt, self.board)
        for r in self.board.rangers:
            r.update(dt, self.board)
        for a in self.board.animals:
            a.update(dt, self.board)

    # -- Spawning  -------------------------------------------
    
    def _random_tile(self) -> Vector2:
        return Vector2(
            random.randint(0, self.board.width  - 1),
            random.randint(0, self.board.height - 1)
        )
    
    def spawn_ranger(self):
        rid = len(self.board.rangers) + 1
        r = Ranger(
            rid,
            f"R{rid}",
            salary=50,
            position=self._random_tile()
        )
        self.board.rangers.append(r)

    def spawn_plant(self):
        from my_safari_project.model.plant import Plant
        pid = len(self.board.plants) + 1
        self.board.plants.append(Plant(
            pid,
            self._random_tile(),
        ))

    def spawn_pond(self):
        from my_safari_project.model.pond import Pond
        pid = len(self.board.ponds) + 1
        self.board.ponds.append(Pond(
            pid,
            self._random_tile(),
        ))
    
    def spawn_animal(self, species_name):
        import random
        from my_safari_project.model.animal import AnimalSpecies
        from my_safari_project.model.carnivore import Carnivore
        from my_safari_project.model.herbivore import Herbivore
        properties = {
            # species: (class, speed, value, lifespan)
            AnimalSpecies.HYENA:    (Carnivore, 1.5, 60,  random.randint(5, 8)),
            AnimalSpecies.LION:     (Carnivore, 1.8, 150, random.randint(10, 15)),
            AnimalSpecies.TIGER:    (Carnivore, 2.0, 180, random.randint(8, 12)),
            AnimalSpecies.BUFFALO:  (Herbivore, 1.2, 100, random.randint(7, 10)),
            AnimalSpecies.ELEPHANT: (Herbivore, 0.8, 300, random.randint(18,25)),
            AnimalSpecies.GIRAFFE:  (Herbivore, 1.4, 150, random.randint(13, 18)),
            AnimalSpecies.HIPPO:    (Herbivore, 0.9, 175, random.randint(15, 22)),
            AnimalSpecies.ZEBRA:    (Herbivore, 1.7, 130, random.randint(6, 9))
        }
        species = getattr(AnimalSpecies, species_name.upper())
        animal_class, speed, value, lifespan = properties[species]
        self.board.animals.append(animal_class(
            animal_id=len(self.board.animals) + 1,
            species=species,
            position=self._random_tile(),
            speed=speed,
            value=value,
            lifespan=lifespan
        ))

    def spawn_poacher(self):
        pid = len(self.board.poachers) + 1
        p = Poacher(pid, f"P{pid}", position=self._random_tile())
        self.board.poachers.append(p)

    # -- GAME States Logic -------------------------------------------

    def start_game(self):
        match self.game_state:
            case None:
                self.game_State = GameState.RUNNING
    
    def pause_game(self):
        match self.game_state:
            case GameState.RUNNING:
                self.game_State = GameState.PAUSED

    def resume_game(self):
         match self.game_state:
            case GameState.PAUSED:
                self.game_State = GameState.RUNNING

    def save_game(self, file_path: str):
        pass

    def load_game(self, file_path: str):
        pass

    def _monthly_update(self):
        # pay salaries, update budget, wildlife monthly
        self.capital.monthlyExpenses = sum(r.salary for r in self.board.rangers)
        self.capital.monthlyIncome   = 0
        self.capital.updateMonthlyBudget()
        self.wildlife_ai.monthly_tick()

        # counting things to check win condition
        visitors   = len([j for j in self.board.jeeps if not j.is_available and j.current_passengers == 0])
        herbivores = len([a for a in self.board.animals if a.__class__.__name__=="Herbivore" and a.is_alive])
        carnivores = len([a for a in self.board.animals if a.__class__.__name__=="Carnivore" and a.is_alive])
        capital    = self.capital.getBalance()

        if (visitors >= self.visits_req and
            herbivores >= self.herb_req and
            carnivores >= self.carn_req and
            capital >= self.cap_req):
            self.consec_success += 1
        else: self.consec_success = 0

        if self.consec_success >= self.months_needed:
            self.won = True
            self.pause_game()

    def calculate_visitor_flow(self):
        pass
    
    def add_funds(self, amount: float):
        self.capital.addFunds(amount)

    def deduct_funds(self, amount: float) -> bool:
        return self.capital.deductFunds(amount)

    def is_game_over(self) -> bool:
        return self.won or self.lost
