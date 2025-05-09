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
DETECTION_RADIUS = 4.5
EPSILON = 1e-5

# Visual constants
DEFAULT_COLOR = Color(0, 100, 255, 128)
OUTLINE_COLOR = Color(255, 255, 255)
COLLISION_COLOR = Color(255, 0, 0, 180)
LABEL_FONT_SIZE = 28

# Simulation constants
REST_TIME_MIN, REST_TIME_MAX = 5.0, 15.0
HUNGER_THRESHOLD, THIRST_THRESHOLD = 7, 7
REPRODUCTION_COOLDOWN = 30.0
MEMORY_TIMEOUT = 120.0
MAX_SPEED = 2.0
SPEEDS = {
    "SEEKING": MAX_SPEED,
    "MIGRATION": MAX_SPEED * 0.8,
    "REPRODUCTION": MAX_SPEED * 0.7,
    "WANDERING": MAX_SPEED * 0.4,
    "RESTING": 0
}

# Vitals change rates (per second)
HUNGER_RATE = 0.05
THIRST_RATE = 0.08
AGE_RATE = 0.03

class AnimalState(Enum):
    WANDER = auto()
    SEEKING_FOOD = auto()
    EATING = auto()
    SEEKING_WATER = auto()
    DRINKING = auto()
    SEEKING_GROUP = auto()
    MIGRATING = auto()
    SEEKING_MATE = auto()
    REPRODUCING = auto()
    RESTING = auto()

@dataclass
class AnimalStatus:
    state: AnimalState
    timer: float = 0.0
    target: Vector2 = None
    reproduction_cooldown: float = 0.0
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
        
        for animal in self.board.animals:
            self.animal_states[animal.animal_id] = AnimalStatus(
                state=AnimalState.WANDER,
                reproduction_cooldown=REPRODUCTION_COOLDOWN * random.uniform(0.5, 1.0)
            )
        
        # debug setup
        self.debug_mode = False
        self.label = font.SysFont(None, LABEL_FONT_SIZE, bold=True)
        self.state_label = font.SysFont(None, int(LABEL_FONT_SIZE/2), bold=True)

    def update(self, dt: float) -> None:
        self.simulation_time += dt
        self._update_states_and_memory(dt)
        
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
            for animal in self.board.animals if animal.alive
        }
        
        self.detected_entities = {
            animal_id: {"detected": [], "collided": []}
            for animal_id in self.collision_shapes
        }
        
        self._process_collisions()
        self._update_animal_behavior(dt)
    
    def _update_states_and_memory(self, dt: float) -> None:
        current_time = self.simulation_time
        
        for animal in self.board.animals:
            if not animal.alive:  continue
                
            if animal.animal_id not in self.animal_states:
                self.animal_states[animal.animal_id] = AnimalStatus(
                    state=AnimalState.WANDER,
                    reproduction_cooldown=REPRODUCTION_COOLDOWN * random.uniform(0.5, 1.0)
                )
                
            # update vital stats
            animal.age += AGE_RATE * dt
            animal.hunger += HUNGER_RATE * dt
            animal.thirst += THIRST_RATE * dt
            # update reproduction cooldown
            state = self.animal_states[animal.animal_id]
            if state.reproduction_cooldown > 0:
                state.reproduction_cooldown = max(0, state.reproduction_cooldown - dt)
            # remove expired memory items
            for resource_type in state.memory:
                expired = [
                    eid for eid, (_, _, last_seen) in state.memory[resource_type].items() 
                    if current_time - last_seen > MEMORY_TIMEOUT
                ]
                for eid in expired: 
                    state.memory[resource_type].pop(eid)

    def _process_collisions(self) -> None:
        entity_types = [
            ('jeep', self.board.jeeps),
            ('plant', self.board.plants),
            ('pond', self.board.ponds),
            ('ranger', self.board.rangers),
            ('poacher', self.board.poachers),
            ('tourist', self.board.tourists),
        ]
        
        for animal_id, shape in self.collision_shapes.items():
            animal = shape["animal"]
            status = self.animal_states[animal_id]
            # Process all entity types
            for entity_type, entities in entity_types + [
                ('animal', [a for a in self.board.animals 
                if a.animal_id != animal_id and a.alive])
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
                            if entity_type != "animal" or animal.species != entity.species:
                                animal._target = None
                            shape["in_collision"] = True
                            # State transitions on collision
                            if entity_type == "pond" and status.state == AnimalState.SEEKING_WATER:
                                status.state, status.timer, animal.speed = AnimalState.DRINKING, 3.0, 0
                            elif entity_type == "plant" and status.state == AnimalState.SEEKING_FOOD and isinstance(animal, Herbivore):
                                status.state, status.timer, animal.speed = AnimalState.EATING, 5.0, 0
                            elif entity_type == "animal":
                                if status.state == AnimalState.SEEKING_FOOD and isinstance(animal, Carnivore) and isinstance(entity, Herbivore):
                                    status.state, status.timer, animal.speed  = AnimalState.EATING, 5.0, 0
                                elif status.state == AnimalState.SEEKING_MATE and animal.species == entity.species and entity.is_adult() and animal.is_adult():
                                    status.state, status.timer, animal.speed, entity.speed = AnimalState.REPRODUCING, 5.0, 0, 0
                                elif status.state == AnimalState.SEEKING_GROUP and animal.species == entity.species:
                                    status.state, status.timer = AnimalState.MIGRATING, 5.0
            # sort detections by distance
            self.detected_entities[animal_id]["detected"].sort(key=lambda e: e["distance"])
            self.detected_entities[animal_id]["collided"].sort(key=lambda e: e["distance"])
    
    def _update_animal_behavior(self, dt: float) -> None:
        for animal_id, shape in self.collision_shapes.items():
            animal = shape["animal"]
            status = self.animal_states[animal_id]
            # Handle active timers
            if status.timer > 0:
                status.timer = max(0, status.timer - dt)
                if status.timer <= 0:
                    # action completed effects
                    if status.state == AnimalState.DRINKING:
                        animal.thirst = max(0, animal.thirst - 5)
                    elif status.state == AnimalState.EATING:
                        animal.hunger = max(0, animal.hunger - 5)
                    elif status.state == AnimalState.REPRODUCING:
                        status.reproduction_cooldown = REPRODUCTION_COOLDOWN
                    self._choose_next_state(animal_id)
                continue
            # Check for urgent needs (interrupt current state)
            if self._check_urgent_needs(animal_id): continue
            # Check if we should reconsider the current state
            time_since_change = self.simulation_time - status.last_state_change
            if (time_since_change > 20.0 or status.target is None or (
                status.state == AnimalState.WANDER and (
                    animal.hunger >= HUNGER_THRESHOLD or animal.thirst >= THIRST_THRESHOLD
                ))
            ):
                self._choose_next_state(animal_id)
    
    
    def _check_urgent_needs(self, animal_id: int) -> bool:
        """handle urgent needs that would interrupt current state"""
        animal = self.collision_shapes[animal_id]["animal"]
        status = self.animal_states[animal_id]
        if status.state in [AnimalState.DRINKING, AnimalState.EATING, AnimalState.REPRODUCING, AnimalState.MIGRATING]:
            return False
        if animal.thirst >= THIRST_THRESHOLD * 1.5 and status.memory["water"]:
            self._set_state(animal_id, AnimalState.SEEKING_WATER)
            return True
        elif animal.hunger >= HUNGER_THRESHOLD * 1.5 and status.memory["food"]:
            self._set_state(animal_id, AnimalState.SEEKING_FOOD)
            return True
        elif status.reproduction_cooldown <= 0 and any(entity.is_adult() for entity, _, _ in status.memory["same_species"].values()):
            self._set_state(animal_id, AnimalState.SEEKING_MATE)
            return True
        elif status.memory["same_species"]:
            self._set_state(animal_id, AnimalState.SEEKING_GROUP)
            return True
        return False
        
    def _choose_next_state(self, animal_id: int) -> None:
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
        
        # Prioritize states
        if needs_water:
            self._set_state(animal_id, AnimalState.SEEKING_WATER)
        elif needs_food:
            self._set_state(animal_id, AnimalState.SEEKING_FOOD)
        elif can_reproduce:
            self._set_state(animal_id, AnimalState.SEEKING_MATE)
        elif can_rest:
            self._set_state(animal_id, AnimalState.RESTING, animal.position)
        elif status.memory["same_species"]:
            # Migrate with herd - find center of group
            herd_positions = [pos for _, pos, _ in status.memory["same_species"].values()]
            if herd_positions:
                center = Vector2(0, 0)
                for pos in herd_positions:
                    center += pos
                center /= len(herd_positions)
                # Add small random offset
                center += Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
                self._set_state(animal_id, AnimalState.MIGRATING, center)
        else:
            distance, angle = random.uniform(5, 20), random.uniform(0, 6.28)
            target = Vector2(
                animal.position.x + distance * math.cos(angle),
                animal.position.y + distance * math.sin(angle)
            )
            self._set_state(animal_id, AnimalState.WANDER, target)

    def _set_state(self, animal_id: int, new_state: AnimalState, target: Vector2 = None) -> None:
        """Set animal state with appropriate target and speed"""
        animal = self.collision_shapes[animal_id]["animal"]
        status = self.animal_states[animal_id]
        # set new state
        status.state = new_state
        status.last_state_change = self.simulation_time
        # Handle target selection based on state
        if target: status.target = target
        elif status.state == AnimalState.SEEKING_WATER and status.memory["water"]:
            closest = min(
                status.memory["water"].values(), 
                key=lambda item: animal.position.distance_squared_to(item[1]),
                default=None
            )
            if closest: status.target = closest[1]
        elif status.state == AnimalState.SEEKING_FOOD and status.memory["food"]:
            closest = min(
                status.memory["food"].values(), 
                key=lambda item: animal.position.distance_squared_to(item[1]),
                default=None
            )
            if closest: status.target = closest[1]  # Position
        elif status.state == AnimalState.SEEKING_MATE and any(entity.is_adult() for entity, _, _ in status.memory["same_species"].values()):
            closest = min(
                (item for item in status.memory["same_species"].values() if item[0].is_adult()),
                key=lambda item: animal.position.distance_squared_to(item[1]),
                default=None
            )
            if closest: status.target = closest[1]  # Position
        elif status.state == AnimalState.SEEKING_GROUP:
            oldest = max(
                status.memory["same_species"].values(),
                key=lambda item: item[0].age,
                default=None
            )
            if oldest: status.target = oldest[1]    # Position
        # Set animal speed based on state
        speeds = {
            AnimalState.SEEKING_FOOD: SPEEDS["SEEKING"],
            AnimalState.SEEKING_WATER: SPEEDS["SEEKING"],
            AnimalState.MIGRATING: SPEEDS["MIGRATION"],
            AnimalState.REPRODUCING: SPEEDS["REPRODUCTION"],
            AnimalState.WANDER: SPEEDS["WANDERING"],
            AnimalState.EATING: SPEEDS["RESTING"],
            AnimalState.DRINKING: SPEEDS["RESTING"],
            AnimalState.RESTING: SPEEDS["RESTING"]
        }
        animal.speed = speeds.get(status.state, SPEEDS["WANDERING"])
        if status.target: animal._target = status.target # Update animal target for rendering

    def render(
            self, 
            surface: Surface, 
            offset_x: float, 
            offset_y: float, 
            tile_size: int, 
            min_x: int, 
            min_y: int
        ) -> None:
        labels = []
        half_tile = tile_size // 2
        # render detection areas
        for shape in self.collision_shapes.values():
            screen_pos = (
                offset_x + int((shape["position"].x - min_x) * tile_size) + half_tile,
                offset_y + int((shape["position"].y - min_y) * tile_size) + half_tile
            )
            # render detection circle
            detection_radius_px = int(shape["detection_radius"] * tile_size)
            draw.circle(surface, shape["detection_color"], screen_pos, detection_radius_px)
            draw.circle(surface, OUTLINE_COLOR, screen_pos, detection_radius_px, width=1)
            labels.append((str(shape["animal"].animal_id), screen_pos))
        for shape in self.collision_shapes.values():
            screen_pos = (
                offset_x + int((shape["position"].x - min_x) * tile_size) + half_tile,
                offset_y + int((shape["position"].y - min_y) * tile_size) + half_tile
            )
            # render collision area
            collision_radius_px = int(shape["collision_radius"] * tile_size)
            draw.circle(
                surface,
                COLLISION_COLOR if shape["in_collision"] else shape["color"],
                screen_pos,
                collision_radius_px
            )
            draw.circle(surface, OUTLINE_COLOR, screen_pos, collision_radius_px, width=1)
            # render direction line
            target = getattr(shape["animal"], "_target", None)
            if target and (dir_vec := target - shape["position"]).length_squared() > 0:
                dir_vec = dir_vec.normalize()
                end_pos = (
                    screen_pos[0] + int(dir_vec.x * detection_radius_px),
                    screen_pos[1] + int(dir_vec.y * detection_radius_px),
                )
                draw.line(surface, Color(0, 255, 0), screen_pos, end_pos, 3)
        # render labels
        for label_text, (x, y) in labels:
            y_top = y - int(COLLISION_RADIUS * tile_size) - 10
            y_bottom = y + int(COLLISION_RADIUS * tile_size) + 10
            # render animal ID (top)
            text_surf = self.label.render(label_text, True, (255, 255, 255))
            outline_surf = self.label.render(label_text, True, (0, 0, 0))
            rect = text_surf.get_rect(center=(x, y_top))
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                surface.blit(outline_surf, rect.move(dx, dy))
            surface.blit(text_surf, rect)
            # render current state (bottom)
            animal_id = int(label_text)
            if animal_id in self.animal_states:
                state_name = self.animal_states[animal_id].state.name
                state_surf = self.state_label.render(state_name, True, (255, 255, 0))
                outline_state = self.state_label.render(state_name, True, (0, 0, 0))
                state_rect = state_surf.get_rect(center=(x, y_bottom))
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                    surface.blit(outline_state, state_rect.move(dx, dy))
                surface.blit(state_surf, state_rect)