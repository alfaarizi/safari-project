# my_safari_project/control/game_controller.py

import random
from enum import Enum

from my_safari_project.audio import play_jeep_start
from my_safari_project.model.jeep import Jeep
from pygame.math import Vector2

# Model
from my_safari_project.model.timer   import Timer, TIME_SCALE
from my_safari_project.model.board   import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger  import Ranger
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
            DifficultyLevel.EASY:   (10, 10, 10,  500.0),
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
    PAUSED  = "Paused"


class DayPhase:
    DAY   = "Day"
    NIGHT = "Night"


# -----------------------------------------------------------
# Costs
# -----------------------------------------------------------
RANGER_COST   = 150
PLANT_COST    = 20
POND_COST     = 100
HYENA_COST    = 60
LION_COST     = 150
TIGER_COST    = 180
BUFFALO_COST  = 100
ELEPHANT_COST = 300
GIRAFFE_COST  = 150
HIPPO_COST    = 175
ZEBRA_COST    = 130
CHIP_COST = 50


# -----------------------------------------------------------
# Main GameController
# -----------------------------------------------------------
class GameController:
    def __init__(self, difficulty: DifficultyLevel):
        # ─── bookkeeping for difficulty ───────────────────────────
        self.difficulty = difficulty
        init_balance, self._poacher_ivl, self._max_poachers = [
            (1500.0, 30.0, 4),
            (1000.0, 20.0, 6),
            (500.0, 10.0, 8),
        ][difficulty.value]

        (self.visits_req,
         self.herb_req,
         self.carn_req,
         self.cap_req) = difficulty.thresholds
        self.months_needed = difficulty.required_months
        self.consec_success = 0
        self.won = self.lost = False

        # ─── MODEL ────────────────────────────────────────────────
        self.board: Board = Board(45, 40, n_roads=5, n_jeeps=10)
        self.capital: Capital = Capital(init_balance)
        self.timer: Timer = Timer()
        self.running = True

        # ─── VIEW ────────────────────────────────────────────────
        # Note: all camera/zoom setup now lives in GameGUI, not here
        from my_safari_project.view.gamegui import GameGUI
        self.game_gui = GameGUI(self)

        # ─── AI / helpers ────────────────────────────────────────
        self.wildlife_ai = WildlifeAI(self.board, self.capital, feedback_callback=self.game_gui._feedback)
        self._poacher_timer = 0.0

        #new timespeed
        self.time_multiplier: float = 1.0 

        self.visible_animals_night = set()
        self.board.visible_animals_night = self.visible_animals_night
        self.chip_placement_mode = False


    def run(self):
        """Main loop."""
        while self.running:
            dt = self.timer.tick(self.time_multiplier)  # scaled dt from Timer
            dt = min(dt, 0.02 * max(self.time_multiplier, 1.0))
            self._update_sim(dt)
            self.game_gui.update(dt)
        self.game_gui.exit()

    def handle_chip_click(self, world_pos: Vector2) -> bool:
        animal_clicked = self.game_gui.board_gui.get_animal_at(world_pos)
        if animal_clicked:
            self.visible_animals_night.add(animal_clicked.animal_id)
            self.chip_placement_mode = False
            self.game_gui._feedback(f"Animal #{animal_clicked.animal_id} tagged!")
            return True
        else:
            self.game_gui._feedback("No animal at clicked location.")
            return False


    # ───────────────────────── Simulation Update ──────────────────────────
    def _update_sim(self, dt: float):
        now = self.timer.elapsed_seconds

        # 1) advance jeeps (and their yield logic) + Wildlife AI
        self.board.update(dt, now)
        self.wildlife_ai.update(dt)

        # 2) spawn & move poachers, animals
        if len(self.board.poachers) < self._max_poachers:
            self._poacher_timer += dt
            if self._poacher_timer >= self._poacher_ivl:
                self._poacher_timer = 0.0
                self.spawn_poacher()

        for p in self.board.poachers:
            p.update(dt, self.board)
        for a in self.board.animals:
            a.update(dt, self.board)

        # 3) rangers
        for r in self.board.rangers:
            result = r.update(dt, self.board)
            if result == "poacher_eliminated":
                self.capital.addFunds(50)
                self.game_gui._feedback("Poacher eliminated! +$50")


    # ───────────────────────── Spawning Helpers ──────────────────────────
    def _random_tile(self):
        return Vector2(
            random.randint(0, self.board.width - 1),
            random.randint(0, self.board.height - 1)
        )

    def spawn_ranger(self, position: Vector2 | None = None):
        rid = len(self.board.rangers) + 1
        pos = position if position is not None else self._random_tile()
        tx, ty = int(pos.x), int(pos.y)
        ranger = Ranger(rid, f"R{rid}", 50, pos)
        self.board.fields[ty][tx].add_object(ranger)
        self.board.rangers.append(ranger)
    

    def spawn_plant(self, position : Vector2 | None = None):
        from my_safari_project.model.plant import Plant
        pid = len(self.board.plants) + 1
        pos = position if position is not None else self._random_tile()
        tx, ty = int(pos.x), int(pos.y)

        plant = Plant(pid, pos)
        self.board.fields[ty][tx].add_object(plant)
        self.board.plants.append(plant)


    def spawn_pond(self, position : Vector2 | None = None ):
        from my_safari_project.model.pond import Pond
        pid = len(self.board.ponds) + 1
        pos = position if position is not None else self._random_tile()
        tx, ty = int(pos.x), int(pos.y)

        pond = Pond(pid, pos)
        self.board.fields[ty][tx].add_object(pond)
        self.board.ponds.append(pond)


    def spawn_animal(self, species_name: str, position: Vector2 | None = None):
        import random
        from my_safari_project.model.animal    import AnimalSpecies
        from my_safari_project.model.carnivore import Carnivore
        from my_safari_project.model.herbivore import Herbivore

        props = {
            AnimalSpecies.HYENA:    (Carnivore, 1.5,  60, random.randint(5,  8)),
            AnimalSpecies.LION:     (Carnivore, 1.8, 150, random.randint(10, 15)),
            AnimalSpecies.TIGER:    (Carnivore, 2.0, 180, random.randint(8, 12)),
            AnimalSpecies.BUFFALO:  (Herbivore, 1.2, 100, random.randint(7, 10)),
            AnimalSpecies.ELEPHANT: (Herbivore, 0.8, 300, random.randint(18,25)),
            AnimalSpecies.GIRAFFE:  (Herbivore, 1.4, 150, random.randint(13,18)),
            AnimalSpecies.HIPPO:    (Herbivore, 0.9, 175, random.randint(15,22)),
            AnimalSpecies.ZEBRA:    (Herbivore, 1.7, 130, random.randint(6, 9))
        }
        try:
            species = getattr(AnimalSpecies, species_name.upper())
            cls, spd, val, life = props[species]
            pos = position if position is not None else self._random_tile()
            tx, ty = int(pos.x), int(pos.y)

            animal = cls(
            animal_id = len(self.board.animals)+1,
            species   = species,
            position  = pos,
            speed     = spd,
            value     = val,
            lifespan  = life
            )
            
            self.board.animals.append(animal)
            self.board.fields[ty][tx].add_object(animal)
        except AttributeError:
            print("please fix me – drag and drop functionality issue")

    def spawn_poacher(self):
        pid = len(self.board.poachers) + 1
        p   = Poacher(pid, f"P{pid}", position=self._random_tile())
        p.choose_random_target(self.board.width, self.board.height)
        self.board.poachers.append(p)
        # tx, ty = int(p.position.x), int(p.position.y)
        # self.board.fields[ty][tx].add_object(p)

    # ─────────────────────── Game State Logic ─────────────────────────
    def start_game(self):
        if not hasattr(self, "game_state"):
            self.game_state = GameState.RUNNING

    def pause_game(self):
        if getattr(self, "game_state", None) == GameState.RUNNING:
            self.game_state = GameState.PAUSED

    def resume_game(self):
        if getattr(self, "game_state", None) == GameState.PAUSED:
            self.game_state = GameState.RUNNING

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

        visitors   = len([
            j for j in self.board.jeeps
            if not j.is_available and j.current_passengers == 0
        ])
        herbivores = len([
            a for a in self.board.animals
            if a.__class__.__name__ == "Herbivore" and a.is_alive
        ])
        carnivores = len([
            a for a in self.board.animals
            if a.__class__.__name__ == "Carnivore" and a.is_alive
        ])
        capital    = self.capital.getBalance()

        if (visitors   >= self.visits_req and
            herbivores >= self.herb_req    and
            carnivores >= self.carn_req    and
            capital    >= self.cap_req):
            self.consec_success += 1
        else:
            self.consec_success = 0

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
    
    def enter_chip_mode(self):
        self.chip_placement_mode = True
        self.game_gui._feedback("Click an animal to tag with chip")

    # ────────────────────────── jeep shop helper ─────────────────────────
    def try_spawn_jeep(self, world_click: Vector2) -> bool:
        if not self.capital.deductFunds(50):
            return False                                  # not enough money

        click_tile = Vector2(int(world_click.x), int(world_click.y))
        # find exact road tile at that integer position
        roads_here = [r for r in self.board.roads if r.pos == click_tile]
        if not roads_here:
            self.capital.addFunds(50)                     # refund
            return False                                  # not on a road

        # let the board figure out the longest path starting FROM THAT TILE
        path = self.board._longest_path(click_tile)
        if len(path) < 2:
            self.capital.addFunds(50)                     # refund, unusable
            return False

        jeep = Jeep(len(self.board.jeeps) + 1, Vector2(path[0]))
        jeep.board = self.board
        jeep.set_path(path)
        self.board.jeeps.append(jeep)
        play_jeep_start()
        return True


