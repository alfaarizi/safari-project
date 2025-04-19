import pygame
from my_safari_project.model.timespeed import TimeSpeed
#from timespeed import TimeSpeed

from enum import Enum

class TimeSpeed(Enum):
    SLOW = 1
    NORMAL = 2
    FAST = 3


class Timer:
    def __init__(self):
        self.currentTime: float = 0.0
        self.timeSpeed: TimeSpeed = TimeSpeed.NORMAL
        self.dayNightCycleEnabled: bool = True
        self.dayLength: float = 10.0
        self.nightLength: float = 14.0
        self.clock = pygame.time.Clock()
        self.delta_time = 0  # Time between frames (in seconds)

    def setSpeedLevel(self, speed: TimeSpeed) -> None:
        self.timeSpeed = speed

    def getSpeedLevel(self) -> TimeSpeed:
        return self.timeSpeed

    def updateTime(self, delta: float) -> None:
        if self.timeSpeed == TimeSpeed.SLOW:
            multiplier = 0.3
        elif self.timeSpeed == TimeSpeed.FAST:
            multiplier = 3.0
        else:  # TimeSpeed.NORMAL
            multiplier = 1.0

        self.currentTime += delta * multiplier

        if self.dayNightCycleEnabled:
            total_cycle = self.dayLength + self.nightLength
            # Wrap around if it exceeds the total cycle length
            if self.currentTime > total_cycle:
                self.currentTime %= total_cycle

    def getCurrentTime(self) -> float:
        return self.currentTime

    def isNightTime(self) -> bool:
        if not self.dayNightCycleEnabled:
            return False
        return self.currentTime >= self.dayLength

    def toggleDayNightCycle(self) -> None:
        self.dayNightCycleEnabled = not self.dayNightCycleEnabled