# my_safari_project/control/game_controller.py

import random
from enum import Enum
import json
import os

from my_safari_project.audio import play_jeep_start
from my_safari_project.model.jeep import Jeep
from pygame.math import Vector2



# Model
from my_safari_project.model.timer   import Timer, TIME_SCALE
from my_safari_project.model.board   import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.ranger  import Ranger
from my_safari_project.model.tourist import Tourist
from my_safari_project.model.road import Road, RoadType
from my_safari_project.model.plant import Plant
from my_safari_project.model.pond import Pond


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
        self.board: Board = Board(100, 100, n_roads=5, n_jeeps=10)
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

    def save_game(self, file_path: str):
        data = {
            "difficulty": self.difficulty.name,
            "time": self.timer.elapsed_seconds,
            "capital": self.capital.getBalance(),
            "animals": [
                {
                    "id": a.animal_id,
                    "species": a.species.name,
                    "x": a.position.x,
                    "y": a.position.y,
                    "speed": a.speed,
                    "value": a.value,
                    "lifespan": a.lifespan,
                    "age": a.age,
                    "hunger": a.hunger,
                    "thirst": a.thirst,
                } for a in self.board.animals
            ],
            "rangers": [
                {
                    "id": r.id,
                    "name": r.name,
                    "salary": r.salary,
                    "x": r.position.x,
                    "y": r.position.y,
                } for r in self.board.rangers
            ],
            "jeep_count": len(self.board.jeeps)
            ,
            "tourists": [
                {
                    "id": t.id,
                    "x": t.position.x,
                    "y": t.position.y,
                    "seen_animals": list(t.seen_animals),
                    "movement_state": t.movement_state,
                    "timer": t.timer,
                    "wander_timer": t.wander_timer,
                    "wander_duration": t.wander_duration,
                    "target": [t.target.x, t.target.y] if t.target else None
                } for t in self.board.tourists
],
            "plants": [
                {
                    "id": p.plant_id,
                    "x": p.position.x,
                    "y": p.position.y,
                    "nutrition": p.nutrition_level
                } for p in self.board.plants
            ],
            "ponds": [
                {
                    "id": p.pond_id,
                    "x": p.position.x,
                    "y": p.position.y,
                    "water": p.water_level
                } for p in self.board.ponds
            ],
            "roads": [
                {
                    "x": r.pos.x,
                    "y": r.pos.y,
                    "type": r.type.name
                } for r in self.board.roads
    ]

        }
        os.makedirs("saves", exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_game(self, file_path: str):
        with open(file_path, "r") as f:
            data = json.load(f)

         # Load difficulty
        self.difficulty = DifficultyLevel[data.get("difficulty", "NORMAL")]
        (self.visits_req,
        self.herb_req,
        self.carn_req,
        self.cap_req) = self.difficulty.thresholds
        self.months_needed = self.difficulty.required_months
        
        self.timer.elapsed_seconds = data["time"]
        self.capital = Capital(data["capital"])

        self.board.animals.clear()
        for ad in data["animals"]:
            self.spawn_animal(
                species_name=ad["species"],
                position=Vector2(ad["x"], ad["y"])
            )
            a = self.board.animals[-1]
            a.age, a.hunger, a.thirst = ad["age"], ad["hunger"], ad["thirst"]

        self.board.rangers.clear()
        for rd in data["rangers"]:
            self.spawn_ranger(position=Vector2(rd["x"], rd["y"]))


        self.board.tourists.clear()
        for td in data["tourists"]:
            tourist = Tourist(td["id"], Vector2(td["x"], td["y"]), board=self.board)
            tourist.seen_animals = set(td.get("seen_animals", []))
            tourist.movement_state = td.get("movement_state", "waiting")
            tourist.timer = td.get("timer", 0.0)
            tourist.wander_timer = td.get("wander_timer", 0.0)
            tourist.wander_duration = td.get("wander_duration", 15.0)
            target = td.get("target")
            if target:
                tourist.target = Vector2(target[0], target[1])
            self.board.tourists.append(tourist)

        # Clear existing
        self.board.plants.clear()
        self.board.ponds.clear()
        # 1. Load all roads
        self.board.roads.clear()
        for rd in data["roads"]:
            pos = Vector2(rd["x"], rd["y"])
            road = Road(pos, RoadType[rd["type"]])
            self.board.roads.append(road)
            fx, fy = int(pos.x), int(pos.y)
            self.board.fields[fy][fx].terrain_type = "ROAD"
            self.board.fields[fy][fx].set_obstacle(True)

        # 2. STITCH ROAD NETWORK properly
        for road in self.board.roads:
            self.board._stitch_into_network(road)

        self.board.jeeps.clear()
        jeep_count = data.get("jeep_count", 0)
        self.board._spawn_jeeps(n_jeeps=jeep_count)


        # Restore Plants
        for pd in data.get("plants", []):
            pos = Vector2(pd["x"], pd["y"])
            plant = Plant(pd["id"], pos)
            plant.nutrition_level = pd["nutrition"]
            self.board.plants.append(plant)
            tx, ty = int(pos.x), int(pos.y)
            self.board.fields[ty][tx].add_object(plant)

        # Restore Ponds
        for pd in data.get("ponds", []):
            pos = Vector2(pd["x"], pd["y"])
            pond = Pond(pd["id"], pos)
            pond.water_level = pd["water"]
            self.board.ponds.append(pond)
            tx, ty = int(pos.x), int(pos.y)
            self.board.fields[ty][tx].add_object(pond)

        # Reassign tourists to jeeps after all are created
        for tourist in self.board.tourists:
            if tourist.movement_state == "in_jeep":
                nearest_jeep = min(
                    self.board.jeeps,
                    key=lambda j: j.position.distance_to(tourist.position),
                    default=None
                )
                if nearest_jeep and len(nearest_jeep.tourists) < 4:
                    tourist.in_jeep = nearest_jeep
                    nearest_jeep.tourists.append(tourist)
                else:
                    # fallback: treat as waiting tourist if no jeep is available
                    tourist.movement_state = "waiting"
                    self.board.waiting_tourists.append(tourist)





