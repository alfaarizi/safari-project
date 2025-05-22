from pygame.math import Vector2
import random
import math
from typing import Set
from my_safari_project.model.animal import Animal
from my_safari_project.model.jeep import Jeep


class Tourist:
    def __init__(self, tid: int, position: Vector2, board):
        self.id = tid
        self.position = position
        self.in_jeep: Jeep | None = None
        self.seen_animals: Set[int] = set()
        self.timer = 0.0
        self.roaming = False
        self.target: Vector2 | None = None
        self.speed = 0.6
        self.board = board
        self.wander_timer = 0.0
        self.wander_duration = random.uniform(15, 30)  # Wander for 15-30 seconds
        self.movement_state = "waiting"  # "waiting", "in_jeep", "wandering", "exiting"

    def enter_jeep(self, jeep: Jeep):
        if len(jeep.tourists) < 4:
            self.in_jeep = jeep
            jeep.tourists.append(self)
            self.movement_state = "in_jeep"
            return True
        return False

    def exit_jeep(self):
        if self.in_jeep:
            # Position slightly offset from jeep to avoid overlap
            offset_angle = random.uniform(0, 2 * math.pi)
            offset_distance = random.uniform(1, 2)
            offset_x = offset_distance * math.cos(offset_angle)
            offset_y = offset_distance * math.sin(offset_angle)
            
            self.position = Vector2(self.in_jeep.position.x + offset_x, self.in_jeep.position.y + offset_y)
            self.in_jeep.tourists.remove(self)
            self.in_jeep = None
            
            # Start wandering phase
            self.movement_state = "wandering"
            self.roaming = True
            self.wander_timer = 0.0
            self.wander_duration = random.uniform(15, 30)  # Wander for 15-30 seconds
            self.target = self._get_wander_target()

    def _get_wander_target(self):
        """Get a random nearby target for wandering."""
        # Wander in a small area around current position
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(1, 4)  # Stay relatively close
        dx = distance * math.cos(angle)
        dy = distance * math.sin(angle)
        
        new_target = self.position + Vector2(dx, dy)
        
        # Keep within board bounds
        if hasattr(self.board, 'width') and hasattr(self.board, 'height'):
            new_target.x = max(0, min(new_target.x, self.board.width - 1))
            new_target.y = max(0, min(new_target.y, self.board.height - 1))
        
        return new_target

    def _get_exit_target(self):
        """Get the nearest exit for leaving the safari."""
        if not self.board.exits:
            return self.position
        
        # Find nearest exit
        nearest_exit = min(self.board.exits, key=lambda exit: self.position.distance_to(Vector2(exit)))
        return Vector2(nearest_exit)

    def update(self, dt: float, board):
        if self.movement_state == "waiting":
            return  # Do nothing until tourist enters jeep

        if self.movement_state == "in_jeep":
            self.position = self.in_jeep.position

        elif self.movement_state == "wandering":
            self.wander_timer += dt

            if self.target and self.position.distance_to(self.target) > 0.5:
                direction = (self.target - self.position).normalize()
                self.position += direction * self.speed * dt
            else:
                if self.wander_timer < self.wander_duration:
                    self.target = self._get_wander_target()
                else:
                    self.movement_state = "exiting"
                    self.target = self._get_exit_target()
                    self.timer = 30.0

        elif self.movement_state == "exiting":
            self.timer -= dt

            if self.target and self.position.distance_to(self.target) > 0.5:
                direction = (self.target - self.position).normalize()
                self.position += direction * self.speed * dt
            else:
                self.timer = 0.0


    def detect_animals(self, animals: list[Animal], radius: float):
        """Detect animals within radius - works in all states except exiting."""
        if self.movement_state != "exiting":
            for animal in animals:
                if animal.is_alive and self.position.distance_to(animal.position) <= radius:
                    self.seen_animals.add(animal.animal_id)

    def is_done(self) -> bool:
        """Tourist is ready to despawn when they've finished exiting."""
        return self.movement_state == "exiting" and self.timer <= 0