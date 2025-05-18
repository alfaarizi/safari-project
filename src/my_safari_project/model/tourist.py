from pygame.math import Vector2
import random
import math
from typing import Set
from my_safari_project.model.animal import Animal
from my_safari_project.model.jeep import Jeep


class Tourist:
    def __init__(self, tid: int, position: Vector2,board):
        self.id = tid
        self.position = position
        self.in_jeep: Jeep | None = None
        self.seen_animals: Set[int] = set()
        self.timer = 0.0
        self.roaming = False
        self.target: Vector2 | None = None
        self.speed = 0.6
        self.board = board

    def enter_jeep(self, jeep: Jeep):
        if len(jeep.tourists) < 4:
            self.in_jeep = jeep
            jeep.tourists.append(self)
            return True
        return False

    def exit_jeep(self):
        if self.in_jeep:
            self.position = Vector2(self.in_jeep.position)
            self.in_jeep.tourists.remove(self)
            self.in_jeep = None
            self.roaming = True
            self.timer = 10 + random.uniform(5, 10)  # delay before leaving
            self.exit_point = random.choice(self.board.exits)
            self.target = self.exit_point

        
    def _random_target(self):
        angle = random.uniform(0, 360)
        dist = random.uniform(2, 6)
        dx = dist * math.cos(angle)
        dy = dist * math.sin(angle)
        return self.position + Vector2(dx, dy)

    def update(self, dt: float, board):
        if self.in_jeep:
            self.position = self.in_jeep.position
        elif self.roaming:
            self.timer -= dt
            if self.target and self.position.distance_to(self.target) > 0.2:
                direction = (self.target - self.position).normalize()
                self.position += direction * self.speed * dt
            elif self.timer <= 0:
                self.target = None  # ready to despawn


    def detect_animals(self, animals: list[Animal], radius: float):
        for a in animals:
            if a.is_alive and self.position.distance_to(a.position) <= radius:
                self.seen_animals.add(a.animal_id)

    def is_done(self) -> bool:
        return self.roaming and self.timer <= 0
