from __future__ import annotations
from pygame.math import Vector2
from typing import Any, Dict, TYPE_CHECKING
import random

from my_safari_project.model.animal import Animal
from my_safari_project.model.herbivore import Herbivore
from my_safari_project.model.carnivore import Carnivore
from my_safari_project.model.poacher import Poacher

if TYPE_CHECKING:
    from my_safari_project.model.board import Board
    from my_safari_project.model.capital import Capital

VISION = 4           # tiles
POACHER_INTERVAL = 45  # seconds between spawns
HUNGER_THRESHOLD = 7 # when animal seeks food
THIRST_THRESHOLD = 7 # when animal seeks wate


class WildlifeAI:
    """Keeps Rangers & Poachers moving + interactions."""

    def __init__(self, board: Board, capital: Capital):
        self.board = board
        self.capital = capital
        self._poacher_timer = 0.0
        self._animals_rest_time: Dict[int, float] = {}         # animal_id: remaining rest time
        self._animals_reproduction_time: Dict[int, float] = {} # animal_id: remaining cooldown time
        self._animals_memory: Dict[int, Dict[str, Any]] = {}    # animal_id: known food, water, group, target

    # -------------------------------------------------
    def update(self, dt: float):
        self._poacher_timer += dt
        if self._poacher_timer > POACHER_INTERVAL:
            self._spawn_poacher()
            self._poacher_timer = 0.0

        # ---- Update Poachers ----
        for p in self.board.poachers:
            p.update(dt, self.board)

        # ---- Update Rangers ----
        for r in self.board.rangers:
            r.update(dt, self.board)
            self._ranger_vision(r)

        # ---- Update animals ----
        for animal in self.board.animals[:]:
            if not animal.alive: continue

            if animal.animal_id not in self._animals_memory: self._init_animal_ai(animal)
            # update age and check for death
            animal.age += dt / 24  # Convert dt to days
            if animal.age >= animal.lifespan:
                animal.alive = False
                continue
            # update hunger and thirst
            self._update_survival_needs(animal, dt)
            # check if animal should die from hunger/thirst
            if animal.hunger >= 10 or animal.thirst >= 10:
                animal.alive = False
                continue
            # handle reproduction cooldown
            if animal.animal_id in self._animals_reproduction_time:
                self._animals_reproduction_time[animal.animal_id] = ( 
                    max(0, self._animals_reproduction_time[animal.animal_id] - dt)
                )
            # Process animal behavior
            if animal.animal_id in self._animals_rest_time and self._animals_rest_time[animal.animal_id] > 0:
                self._animals_rest_time[animal.animal_id] -= dt # animal is resting
            else: self._process_animal_behaviour(animal, dt) # animal is active

    # -------------------------------------------------
    def monthly_tick(self):
        """Call at the beginning of each in‑game month → pay salaries."""
        for r in self.board.rangers[:]:
            if not r.pay_salary(self.capital):
                # could not pay → fire ranger
                self.board.rangers.remove(r)
        for animal_id in list(self._animals_memory.keys()): # Clean up memory for dead animals
            if not any(a.animal_id == animal_id and a.alive for a in self.board.animals):
                del self._animals_memory[animal_id]
                if animal_id in self._animals_rest_time:
                    del self._animals_rest_time[animal_id]
                if animal_id in self._animals_reproduction_time:
                    del self._animals_reproduction_time[animal_id]

    # -------------------------------------------------
    #                helpers
    # -------------------------------------------------
    def _spawn_poacher(self):
        # self.board.spawn_poacher(Vector2(randint(0, self.board.width - 1), 0))
        pid = len(self.board.poachers) + 1
        self.board.poachers.append(Poacher(pid, 
                                           "Poacher" + str(pid), 
                                           Vector2(random.randint(0, self.board.width - 1), 0)
                                           ))

    def _ranger_vision(self, ranger):
        """If a poacher within vision → chase / catch."""
        for p in self.board.poachers[:]:
            dist = ranger.position.distance_to(p.position)
            if dist <= ranger.vision:
                p.visible = True
                # simple chase: ranger sets target to poacher
                ranger.target = p.position
                if dist < 0.6:           # caught!
                    self.board.poachers.remove(p)
                    ranger.poachers_caught += 1
                    self.capital.addFunds(50)   # bounty
            else:
                p.visible = False

    # --------------- ANIMAL AI ----------------------------------
    def _init_animal_ai(self, animal: "Animal"):
        self._animals_memory[animal.animal_id] = {
            "known_food": [],       # positions of known food sources
            "known_water": [],      # positions of known water sources
            "group_members": [],    # same-species animals considered part of group
            "wander_target": None   # current random movement target
        }
        self._animals_rest_time[animal.animal_id] = 0
        self._animals_reproduction_time[animal.animal_id] = 0
    
    def _update_survival_needs(self, animal: "Animal", dt: float):
        # slower hunger and thirst over time
        hunger_rate = 0.2 * dt  
        thirst_rate = 0.3 * dt
        animal.hunger = min(10, animal.hunger + hunger_rate)
        animal.thirst = min(10, animal.thirst + thirst_rate)
    
    def _process_animal_behaviour(self, animal: "Animal", dt: float):
        # Priority 1: Drink if very thirsty
        if animal.thirst >= THIRST_THRESHOLD:
            if self._seek_water(animal, dt): return
        # Priority 2: Eat if very hungry
        if animal.hunger >= HUNGER_THRESHOLD:
            if self._seek_food(animal, dt): return
        # Priority 3: Try to reproduce if well-fed and not thisrty
        if animal.hunger < 3 and animal.thirst < 3 and animal.is_adult():
            if self._try_reproduce(animal, dt): return
        # Priorty 4: Stay with the group
        if self._stay_with_group(animal, dt): return
        # Priority 5: Random wander or rest
        if animal.hunger < 5 and animal.thirst < 5:
            if random.random() < 0.2:  # 20% chance to rest when comfortable
                self._animals_rest_time[animal.animal_id] = random.randint(1, 3)
            else:
                self._wander(animal, dt)
        else:
            self._wander(animal, dt)
        
    # --------------- ANIMAL BEHAVOURS ----------------------------------
    def _seek_water(self, animal: "Animal", dt: float) -> bool:
        # check memory for known water sources
        memory = self._animals_memory[animal.animal_id]
        if not memory["known_water"] or random.random() < 0.1: # no known water or time to discover
            nearby_ponds = [(p, Vector2(p.location)) for p in self.board.ponds
                            if animal.position.distance_to(Vector2(p.location)) < 15]
            if nearby_ponds:
                closest_pond, closest_pond_pos = min(nearby_ponds, 
                                                     key=lambda p: animal.position.distance_to(p[1]))
                # move towards pond
                animal.move(closest_pond_pos, dt)
                # add to memory if not already known
                if closest_pond_pos not in memory["known_water"]:
                    memory["known_water"].append(closest_pond_pos)
                # Drink if close enough
                if not closest_pond.isEmpty() and animal.position.distance_to(closest_pond_pos) < 2:
                    animal.thirst = max(0, animal.thirst - 3)
                    closest_pond.evaporate()
                    return True
        elif memory["known_water"]:
            closest_pond_pos = min(memory["known_water"],
                                   key=lambda p: animal.position.distance_to(p))
            closest_pond = None
            for p in self.board.ponds:
                if Vector2(p.location).distance_to(closest_pond_pos) < 1:
                    closest_pond = p
                    break
            if closest_pond:
                animal.move(closest_pond_pos, dt)
                # Drink if close enough
                if not closest_pond.isEmpty() and animal.position.distance_to(closest_pond_pos) < 2:
                    animal.thirst = max(0, animal.thirst - 3)
                    closest_pond.evaporate()
                    return True
                else:
                    memory["known_water"].remove(closest_pond_pos)
        return False
            

    def _seek_food(self, animal: "Animal", dt: float) -> bool:
        if isinstance(animal, Herbivore):
            return self._seek_plants(animal, dt)
        elif isinstance(animal, Carnivore):
            return self._seek_prey(animal, dt)
        return False
    
    def _seek_plants(self, herbivore: "Herbivore", dt: float) -> bool:
        memory = self._animals_memory[herbivore.animal_id]
        if not memory["known_food"] or random.random() < 0.1:
            nearby_plants = [(p, Vector2(p.location)) for p in self.board.plants 
                            if herbivore.position.distance_to(Vector2(p.location)) < 15]
            if nearby_plants:
                closest_plant, closest_plant_pos = min(nearby_plants, 
                                                       key=lambda p: herbivore.position.distance_to(p[1]))
                # move toward plant
                herbivore.move(closest_plant_pos, dt)
                # add to memory
                if closest_plant_pos not in memory["known_food"]:
                    memory["known_food"].append(closest_plant_pos)
                # eat if close enough
                if closest_plant.isAlive and herbivore.position.distance_to(closest_plant_pos) < 2:
                    herbivore.hunger = max(0, herbivore.hunger - 3)
                    closest_plant.getEaten(0.2)
                    return True
        elif memory["known_food"]:
            closest_plant_pos = min(memory["known_food"], 
                                    key=lambda p: herbivore.position.distance_to(p))
            closest_plant = None
            for p in self.board.plants:
                if p.isAlive and Vector2(p.location).distance_to(closest_plant_pos) < 1:
                    closest_plant = p
                    break
            if closest_plant:
                herbivore.move(closest_plant_pos, dt)
                # Eat if close enough
                if closest_plant.isAlive and herbivore.position.distance_to(closest_plant_pos) < 2:
                    herbivore.hunger = max(0, herbivore.hunger - 3)
                    closest_plant.getEaten(0.2)
                    return True
                else:
                    memory["known_food"].remove(closest_plant_pos)                
        return False
    
    def _seek_prey(self, carnivore: "Carnivore", dt: float) -> bool:
        memory = self._animals_memory[carnivore.animal_id]
        if not memory["known_food"] or random.random() < 0.1:
            nearby_herbivores = [(a, a.position) for a in self.board.animals 
                                 if isinstance(a, Herbivore) and carnivore.position.distance_to(a.position) < 15]
            if nearby_herbivores:
                closest_herbivore, closest_herbivore_pos = min(nearby_herbivores, 
                                                               key=lambda p: carnivore.distance_to(p[1]))
                # move toward plant
                closest_herbivore.move(closest_herbivore_pos, dt)
                # add to memory
                if closest_herbivore_pos not in memory["known_food"]:
                    memory["known_food"].append(closest_herbivore_pos)
                # eat if close enough
                if closest_herbivore.is_alive() and carnivore.position.distance_to(closest_herbivore_pos) < 2:
                    carnivore.hunger = max(0, carnivore.hunger - 5)
                    closest_herbivore.alive = False
                    return True
        elif memory["known_food"]:
            closest_herbivore_pos = min(memory["known_food"], 
                                    key=lambda p: carnivore.position.distance_to(p))
            closest_herbivore = None
            for a in self.board.animals:
                if isinstance(a, Herbivore) and a.distance_to(carnivore) < 1:
                    closest_herbivore = a
                    break
            if closest_herbivore:
                carnivore.move(closest_herbivore, dt)
                # eat if close enough
                if closest_herbivore.is_alive() and carnivore.position.distance_to(closest_herbivore_pos) < 2:
                    carnivore.hunger = max(0, carnivore.hunger - 5)
                    closest_herbivore.alive = False
                    return True
                else:
                    memory["known_food"].remove(closest_herbivore)                
        return False
        
    def _try_reproduce(self, animal: "Animal", dt: float) -> bool:
        if self._animals_reproduction_time.get(animal.animal_id, 0) > 0: return False
        # find potential mates (same species, adult, relatively healthy)
        potential_mates = [a for a in self.board.animals 
                           if a.animal_id != animal.animal_id 
                           and a.__class__ == animal.__class__ 
                           and a.alive and a.is_adult()
                           and a.hunger < 5 and a.thirst < 5 
                           and animal.position.distance_to(a.position) < 5]
        if potential_mates:
            # choose closest healthy mate
            mate = min(potential_mates, key=lambda m: animal.position.distance_to(m.position))
            animal.move(mate.position, dt)
            if animal.position.distance_to(mate.position) < 2:
                new_animal = animal.__class__(
                    animal_id=len(self.board.animals) + 1,
                    species=animal.species,
                    position=Vector2(
                        (animal.position.x + mate.position.x) / 2,
                        (animal.position.y + mate.position.y) / 2
                    ),
                    speed=animal.speed,
                    value=animal.value,
                    age=0,
                    lifespan=animal.lifespan
                )

                self.board.animals.append(new_animal)
                self._animals_reproduction_time[animal.animal_id] = 24.0  # 24 hours cooldown
                if mate.animal_id in self._animals_reproduction_time:
                    self._animals_reproduction_time[mate.animal_id] = 24.0
                return True
        return False

    def _stay_with_group(self, animal: "Animal", dt: float) -> bool:
        memory = self._animals_memory[animal.animal_id]
        # find group members (same species within certain range)
        group = [a for a in self.board.animals 
                if a.animal_id != animal.animal_id and a.species == animal.species and a.alive
                and animal.position.distance_to(a.position) < 30]
        # update group memory
        memory["group_members"] = [a.animal_id for a in group]
        if group:
            # move toward center of group if too far
            center = sum((a.position for a in group), Vector2()) / len(group)
            # only move toward center if outside comfortable range
            if animal.position.distance_to(center) > 10:
                animal.move(center, dt)
                return True 
        return False

    def _wander(self, animal: "Animal", dt: float) -> bool:
        memory = self._animals_memory[animal.animal_id]
        # if no target or close to target, pick a new one
        if (memory["wander_target"] is None or animal.position.distance_to(memory["wander_target"]) < 2):
            # choose random point on map
            memory["wander_target"] = Vector2(
                random.uniform(0, self.board.width - 1),
                random.uniform(0, self.board.height - 1)
            )
        # Move toward target
        animal.move(memory["wander_target"], dt)
        return True