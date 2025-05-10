from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any
from enum import Enum, auto
from pygame import Surface, draw, font, Color
from pygame.math import Vector2
import random, math

from my_safari_project.model.board import Board
from my_safari_project.model.herbivore import Herbivore
from my_safari_project.model.carnivore import Carnivore

# Constants
COLLISION_RADIUS = 0.5
DETECTION_RADIUS = 5.0
EPSILON = 1e-5

# Visual constants
DEFAULT_COLOR = Color(0, 100, 255, 128)
OUTLINE_COLOR = Color(255, 255, 255)
COLLISION_COLOR = Color(255, 0, 0, 180)
LABEL_FONT_SIZE = 28

# Simulation constants
HUNGER_THRESHOLD, THIRST_THRESHOLD = 6, 6
REPRODUCTION_COOLDOWN, COOLDOWN_RATE = 100.0, 0.5
MEMORY_TIMEOUT = 120.0
MAX_SPEED = 2.0
SPEEDS = {
    "SEEKING": MAX_SPEED,
    "MIGRATION": MAX_SPEED * 0.8,
    "WANDERING": MAX_SPEED * 0.4,
    "IDLE": 0
}

class AnimalState(Enum):
    DRINKING = auto()
    EATING = auto()
    REPRODUCING = auto()
    MIGRATING = auto()
    RESTING = auto()
    SEEKING_WATER = auto()
    SEEKING_FOOD = auto()
    SEEKING_MATE = auto()
    WANDER = auto()
    
    @property
    def speed(self):
        return { 
            AnimalState.DRINKING: SPEEDS["IDLE"],
            AnimalState.EATING: SPEEDS["IDLE"],
            AnimalState.REPRODUCING: SPEEDS["IDLE"],
            AnimalState.MIGRATING: SPEEDS["MIGRATION"],
            AnimalState.RESTING: SPEEDS["IDLE"],
            AnimalState.SEEKING_WATER: SPEEDS["SEEKING"],
            AnimalState.SEEKING_FOOD: SPEEDS["SEEKING"],
            AnimalState.SEEKING_MATE: SPEEDS["SEEKING"],
            AnimalState.WANDER: SPEEDS["WANDERING"]
        }[self]

@dataclass
class AnimalStatus:
    state: AnimalState = AnimalState.WANDER
    timer: float = 0.0
    target: Vector2 = None
    target_entity: Any = None
    reproduction_cooldown: float = REPRODUCTION_COOLDOWN
    memory: Dict = field(default_factory=lambda: {
        "food": {},  # entity_id -> (entity, position, last_seen)
        "water": {},
        "same_species": {}
    })
    last_state_change: float = 0.0

class AnimalAI:
    def __init__(self, board: Board):
        self.board = board
        self.collision_shapes: Dict[int, Dict] = {}
        self.detected_entities: Dict[int, Dict[str, List[Any]]] = {}
        self.animal_states: Dict[int, AnimalStatus] = {}
        self.simulation_time = 0.0
        
        for animal in self.board.animals: self.animal_states[animal.animal_id] = AnimalStatus()
        
        # debug setup
        self.debug_mode = False
        self.label = font.SysFont(None, LABEL_FONT_SIZE, bold=True)
        self.state_label = font.SysFont(None, int(LABEL_FONT_SIZE*2/3), bold=True)

    def update(self, dt: float) -> None:
        self.simulation_time += dt
        self._process_stats(dt)        
        self._process_collisions()
        self._process_behaviours(dt)
    
    def _process_stats(self, dt: float) -> None:
        current_time = self.simulation_time
        for animal in self.board.animals:
            if not animal.is_alive:  continue
            if animal.animal_id not in self.animal_states: 
                self.animal_states[animal.animal_id] = AnimalStatus()
            # update vital stats
            animal.add_age(dt)
            animal.add_hunger(dt)
            animal.add_thirst(dt)
            # update reproduction cooldown
            state = self.animal_states[animal.animal_id]
            state.reproduction_cooldown = max(state.reproduction_cooldown - COOLDOWN_RATE*dt, 0)
            # remove expired memory items
            for resource_type in state.memory:
                expired = [
                    eid for eid, (_, _, last_seen) in state.memory[resource_type].items() 
                    if current_time - last_seen > MEMORY_TIMEOUT
                ]
                for eid in expired: 
                    state.memory[resource_type].pop(eid)

    def _process_collisions(self) -> None:
        # Cleanup
        self.collision_shapes = {
            animal.animal_id: {
                "animal": animal,
                "position": animal.position,
                "in_collision": False,
                "collision_radius": COLLISION_RADIUS,
                "detection_radius": DETECTION_RADIUS,
                "color": DEFAULT_COLOR,
                "detection_color": animal.species.color,
            }
            for animal in self.board.animals if animal.is_alive
        }
        self.detected_entities = {
            animal_id: {"detected": [], "collided": []}
            for animal_id in self.collision_shapes
        }

        # entities to detect
        entity_types = [
            ('pond', self.board.ponds),
            ('plant', self.board.plants),
            ('jeep', self.board.jeeps),
            ('ranger', self.board.rangers),
            ('poacher', self.board.poachers),
            ('tourist', self.board.tourists),
        ]
        
        # process area detection/collision
        for animal_id, shape in self.collision_shapes.items():
            animal = shape["animal"]
            status = self.animal_states[animal_id]
            # process all entity types
            for entity_type, entities in entity_types + [
                ('animal', [a for a in self.board.animals 
                if a.animal_id != animal_id and a.is_alive])
            ]:
                for entity in entities:
                    delta = entity.position - shape["position"]
                    sq_dist = delta.length_squared()
                    # detection check
                    if sq_dist <= shape["detection_radius"] ** 2:
                        distance = math.sqrt(sq_dist)
                        self.detected_entities[animal_id]["detected"].append({
                            "type": entity_type, 
                            "entity": entity, 
                            "distance": distance
                        })
                        # update memory
                        entity_id = getattr(entity, "animal_id", id(entity))
                        if entity_type == "pond":
                            status.memory["water"][entity_id] = (entity, entity.position.copy(), self.simulation_time)
                        elif entity_type == "plant" and isinstance(animal, Herbivore):
                            status.memory["food"][entity_id] = (entity, entity.position.copy(), self.simulation_time)
                        elif entity_type == "animal":
                            if isinstance(animal, Carnivore) and isinstance(entity, Herbivore):
                                status.memory["food"][entity_id] = (entity, entity.position.copy(), self.simulation_time)
                            if animal.species == entity.species:
                                status.memory["same_species"][entity_id] = (entity, entity.position.copy(), self.simulation_time)
                        # collision check
                        if sq_dist <= (shape["collision_radius"] + COLLISION_RADIUS) ** 2:
                            self.detected_entities[animal_id]["collided"].append({
                                "type": entity_type, 
                                "entity": entity, 
                                "distance": distance
                            })
                            # collision response
                            distance = max(distance, EPSILON)
                            min_dist = shape["collision_radius"] + COLLISION_RADIUS
                            separation = delta * ((min_dist - distance) / distance)
                            animal.position = shape["position"] - separation
                            animal.target = None
                            shape["in_collision"] = True
                            # State transitions on collision
                            match entity_type:
                                case "pond":
                                    if status.state == AnimalState.SEEKING_WATER:
                                        status.target_entity = entity
                                        self._change_state(animal_id, AnimalState.DRINKING)
                                case "plant":
                                    if status.state == AnimalState.SEEKING_FOOD and isinstance(animal, Herbivore):
                                        status.target_entity = entity
                                        self._change_state(animal_id, AnimalState.EATING)
                                case "animal":
                                    if status.state == AnimalState.SEEKING_FOOD and isinstance(animal, Carnivore) and isinstance(entity, Herbivore):
                                        entity.speed = 0
                                        status.target_entity = entity
                                        self._change_state(animal_id, AnimalState.EATING)
                                    elif status.state == AnimalState.SEEKING_MATE and animal.species == entity.species and entity.is_adult() and animal.is_adult():
                                        entity_status = self.animal_states[entity.animal_id]
                                        if status.reproduction_cooldown <= 0 and entity_status.reproduction_cooldown <= 0:
                                            entity.speed = 0
                                            status.target_entity = entity
                                            entity_status.reproduction_cooldown = 0.1 # Just enough to prevent double reproduction
                                            self._change_state(animal_id, AnimalState.REPRODUCING)
                                case "jeep":
                                    is_moving = bool(entity._path) and entity._idx < len(entity._path)
                                    if is_moving:
                                        animal.is_alive = False
            # sort detections by distance
            self.detected_entities[animal_id]["detected"].sort(key=lambda e: e["distance"])
            self.detected_entities[animal_id]["collided"].sort(key=lambda e: e["distance"])
    
    def _process_behaviours(self, dt: float) -> None:
        for animal_id, shape in self.collision_shapes.items():
            animal = shape["animal"]
            status = self.animal_states[animal_id]
            # Handle active timers
            if status.timer > 0:
                status.timer = max(0, status.timer - dt)
                # For migration, update target position if we have a target entity
                if status.state == AnimalState.MIGRATING and status.target_entity and status.target_entity in {entity for entity, *_ in status.memory["same_species"].values()}:
                    for entity, pos, _ in status.memory["same_species"].values():
                        if entity == status.target_entity:
                            status.target = animal.target = pos
                            break
                if status.timer > 0: continue
                # completed action effects
                match status.state:
                    case AnimalState.DRINKING:
                        if animal.drink(status.target_entity):
                            print(f"{animal_id} drank from pond {status.target_entity}")
                        elif status.target_entity in self.board.ponds:
                            self.board.ponds.remove(status.target_entity)
                        # clean memory if pond no longer exists
                        entity_id = getattr(status.target_entity, "pond_id", id(status.target_entity))
                        if entity_id in status.memory["water"] and status.target_entity not in self.board.ponds:
                            status.memory["water"].pop(entity_id)
                    case AnimalState.EATING:
                        if animal.consume(status.target_entity):
                            print(f"{animal_id} ate {status.target_entity}")    
                        elif status.target_entity in self.board.animals:
                            self.board.animals.remove(status.target_entity)
                        elif status.target_entity in self.board.plants:
                            self.board.plants.remove(status.target_entity)
                        # clean memory if plant/animal no longer exists
                        entity_id = getattr(status.target_entity, "animal_id", id(status.target_entity))
                        collection = self.board.animals if isinstance(status.target_entity, Herbivore) else self.board.plants
                        if entity_id in status.memory["food"] and status.target_entity not in collection:
                            status.memory["food"].pop(entity_id)
                            if entity_id in status.memory["same_species"]:  # for animals, also clean same_species memory
                                status.memory["same_species"].pop(entity_id)
                    case AnimalState.REPRODUCING:
                        offspring = animal.reproduce(status.target_entity, len(self.board.animals) + 1)
                        if offspring is not None:
                            print(f"{animal_id} reproduced with {status.target_entity}")
                            # animal cooldown
                            status.reproduction_cooldown = REPRODUCTION_COOLDOWN
                            # entity cooldown
                            mate_status = self.animal_states[status.target_entity.animal_id]
                            mate_status.reproduction_cooldown = REPRODUCTION_COOLDOWN
                            self.board.animals.append(offspring)
                    case AnimalState.WANDER:
                        if status.target and (animal.position - status.target).length() < 1.0:
                            animal.speed = 0
                            status.timer = random.uniform(1.0, 2.0)
                            continue
                self._next_state(animal_id)
            if self._interrupt_state(animal_id): continue
            # Check if we should reconsider the current state
            time_since_change = self.simulation_time - status.last_state_change
            needs_state_update = (
                time_since_change > 20.0 or
                status.target is None or
                (status.state == AnimalState.WANDER and (animal.hunger >= HUNGER_THRESHOLD or animal.thirst >= THIRST_THRESHOLD))
            )
            if needs_state_update: self._next_state(animal_id)
    
    def _interrupt_state(self, animal_id: int) -> bool:
        animal = self.collision_shapes[animal_id]["animal"]
        status = self.animal_states[animal_id]
        if status.state in { AnimalState.DRINKING, AnimalState.EATING, AnimalState.REPRODUCING, AnimalState.MIGRATING }:
            return False
        if animal.thirst >= THIRST_THRESHOLD * 1.5 and status.memory["water"]:
            return self._change_state(animal_id, AnimalState.SEEKING_WATER) or True
        elif animal.hunger >= HUNGER_THRESHOLD * 1.5 and status.memory["food"]:
            return self._change_state(animal_id, AnimalState.SEEKING_FOOD) or True
        return False
        
    def _next_state(self, animal_id: int) -> None:
        animal = self.collision_shapes[animal_id]["animal"]
        status = self.animal_states[animal_id]
        # check needs
        needs_water = animal.thirst >= THIRST_THRESHOLD and status.memory["water"]
        needs_food = animal.hunger >= HUNGER_THRESHOLD and status.memory["food"]
        can_reproduce = (
            animal.hunger < HUNGER_THRESHOLD and animal.thirst < THIRST_THRESHOLD and
            status.reproduction_cooldown <= 0 and animal.is_adult() and
            any(entity.is_adult() for entity, _, _ in status.memory["same_species"].values())
        )
        can_rest = animal.hunger < HUNGER_THRESHOLD * 0.7 and animal.thirst < THIRST_THRESHOLD * 0.7 and random.random() < 0.6
        # prioritize states
        if needs_water:
            self._change_state(animal_id, AnimalState.SEEKING_WATER)
        elif needs_food:
            self._change_state(animal_id, AnimalState.SEEKING_FOOD)
        elif can_reproduce:
            self._change_state(animal_id, AnimalState.SEEKING_MATE)
        elif can_rest:
            self._change_state(animal_id, AnimalState.RESTING)
        elif status.memory["same_species"]:
            self._change_state(animal_id, AnimalState.MIGRATING)
        else:
            self._change_state(animal_id, AnimalState.WANDER)

    def _change_state(self, animal_id: int, new_state: AnimalState) -> None:
        animal, status = self.collision_shapes[animal_id]["animal"], self.animal_states[animal_id]
        status.state, status.last_state_change = new_state, self.simulation_time
        match status.state:
            case AnimalState.DRINKING:
                status.timer = 3.0
            case AnimalState.EATING | AnimalState.REPRODUCING:
                status.timer = 5.0
            case AnimalState.RESTING:
                status.timer = 8.0
            case AnimalState.SEEKING_WATER if status.memory["water"]:
                closest = min(
                    status.memory["water"].values(),
                    key=lambda item: animal.position.distance_squared_to(item[1]),
                    default=None
                )
                if closest: status.target = closest[1]
            case AnimalState.SEEKING_FOOD if status.memory["food"]:
                closest = min(
                    status.memory["food"].values(),
                    key=lambda item: animal.position.distance_squared_to(item[1]),
                    default=None
                )
                if closest: status.target = closest[1]
            case AnimalState.SEEKING_MATE:
                closest = min(
                    (v for v in status.memory["same_species"].values() if v[0].is_adult() and (self.animal_states[v[0].animal_id].reproduction_cooldown <= 0)),
                    key=lambda item: animal.position.distance_squared_to(item[1]),
                    default=None
                )
                if closest: status.target = closest[1]
            case AnimalState.MIGRATING:
                status.timer = random.uniform(5.0, 12.0)
                oldest = max(
                    (v for v in status.memory["same_species"].values() if self.animal_states[v[0].animal_id].state == AnimalState.MIGRATING),
                    key=lambda x: x[0].age,
                    default=None
                )
                if oldest:
                    direction = oldest[1] - animal.position # limit migration distance, ensure target stays within boundaries
                    if direction.length_squared() > 0:
                        migration_distance = min(direction.length(), random.uniform(5.0, 10.0))
                        direction = direction.normalize() * migration_distance
                    board_margin = 2.0
                    target_pos = Vector2(
                        max(board_margin, min(self.board.width - board_margin, animal.position.x + direction.x)),
                        max(board_margin, min(self.board.height - board_margin, animal.position.y + direction.y))
                    )
                    status.target, status.target_entity = target_pos, oldest[0]
            case AnimalState.WANDER:
                min_distance, max_distance = 5.0, 15.0
                distance = random.uniform(min_distance, max_distance)
                angle = random.uniform(0, 2 * math.pi)
                status.target = Vector2(
                    animal.position.x + distance * math.cos(angle),
                    animal.position.y + distance * math.sin(angle)
                )
                status.timer = max(4.0, distance / (SPEEDS["WANDERING"] + 0.01) * 1.5)
        animal.speed = status.state.speed
        if status.target: animal.target = status.target

    def render(
            self, 
            surface: Surface, 
            offset_x: float, 
            offset_y: float, 
            tile_size: int, 
            min_x: int, 
            min_y: int
        ) -> None:
        half_tile = tile_size // 2
        # rendering text with outline
        def render_text(text, font, color, center_pos):
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=center_pos)
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                surface.blit(font.render(text, True, (0, 0, 0)), text_rect.move(dx, dy))
            surface.blit(text_surf, text_rect)
        # FIRST PASS: draw detection circles
        for animal_id, shape in self.collision_shapes.items():
            pos = shape["position"]
            x, y = (offset_x + int((pos.x - min_x) * tile_size) + half_tile,
                    offset_y + int((pos.y - min_y) * tile_size) + half_tile)
            det_radius = int(shape["detection_radius"] * tile_size)
            draw.circle(surface, shape["detection_color"], (x, y), det_radius)
            draw.circle(surface, OUTLINE_COLOR, (x, y), det_radius, width=1)
        # SECOND PASS: draw collision circles, direction lines, and text
        for animal_id, shape in self.collision_shapes.items():
            animal, pos = shape["animal"], shape["position"]
            x, y = (offset_x + int((pos.x - min_x) * tile_size) + half_tile,
                    offset_y + int((pos.y - min_y) * tile_size) + half_tile)
            col_radius = int(shape["collision_radius"] * tile_size)
            det_radius = int(shape["detection_radius"] * tile_size) 
            # draw collision circle
            draw.circle(surface, COLLISION_COLOR if shape["in_collision"] else shape["color"], (x, y), col_radius)
            draw.circle(surface, OUTLINE_COLOR, (x, y), col_radius, width=1)
            # draw movement direction
            if target := getattr(animal, "target", None):
                if (dir_vec := target - pos).length_squared() > 0:
                    dir_vec = dir_vec.normalize()
                    draw.line(surface, Color(0, 255, 0), (x, y), 
                            (x + int(dir_vec.x * det_radius), y + int(dir_vec.y * det_radius)), 3)
            # draw ID label
            render_text(str(animal_id), self.label, (255, 255, 255), (x, y - col_radius - 10))
            # draw state and stats
            if animal_id in self.animal_states:
                state = self.animal_states[animal_id]
                state_text = f"{state.state.name}: {state.timer:.1f}s" 
                stats_text = f"A: {int(animal.age)}    L: {animal.lifespan}   H: {int(animal.hunger)}   T: {int(animal.thirst)}   C: {state.reproduction_cooldown:.1f}s"
                render_text(state_text, self.state_label, (255, 255, 0), (x, y + col_radius + 10))
                render_text(stats_text, self.state_label, (255, 255, 255), (x, y + col_radius + 25))