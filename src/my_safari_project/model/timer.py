import pygame
# from my_safari_project.model.timespeed import TimeSpeed
#from timespeed import TimeSpeed

# from enum import Enum

# class TimeSpeed(Enum):
#     SLOW = 1
#     NORMAL = 2
#     FAST = 3

# Game time Units to how much real time in Seconds
TIME_SCALE = {            # Game time Bounds
    "minute": 0.7,        # 1 minute
    "hour": 42.0,         # 60 minutes
    "day": 840.0,         # 20 hours (6:00 AM - 2:00 AM)
    "week": 5_880.0,      # 7 Days
    "month": 23_520.0,    # 28 Days (4 Weeks)
    "year": 94_080.0      # 4 Months (Spring, Summer, Fall, Winter)
}

DAYS = ("Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun.")
MONTHS = ("Spring", "Summer", "Fall", "Winter")

class Timer:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.elapsed_seconds = 0.0
    
    def tick(self):
        self.elapsed_seconds += self.clock.tick(60) / 1000.0
        return self.elapsed_seconds
    
    def get_game_time(self):
        years, r    = divmod(self.elapsed_seconds, TIME_SCALE["year"])
        months, r   = divmod(r, TIME_SCALE["month"])
        weeks, r    = divmod(r, TIME_SCALE["week"])
        days, r     = divmod(r, TIME_SCALE["day"])
        hours, r    = divmod(r, TIME_SCALE["hour"])
        minutes     = int(r / TIME_SCALE["minute"])
        return {
            "years": int(years), 
            "months": int(months), 
            "weeks": int(weeks), 
            "days": int(days), 
            "hours": int(hours), 
            "minutes": minutes
        }
    
    def get_date_time(self):
        t = self.get_game_time()
        total_days = t["years"]*4*28 + t["months"]*28 + t["weeks"]*7 + t["days"]

        hour = (6 + t["hours"]) % 24 
        am_pm = "am" if hour < 12 else "pm"
        hour = 12 if hour % 12 == 0 else hour % 12 # 12-hour display
        
        date = f"{DAYS[total_days % 7]} {total_days % 28 + 1}"
        time = f"{hour}:{t['minutes']:02d} {am_pm}"
        
        return date, time



# class Timer:
#     def __init__(self):
#         self.currentTime: float = 0.0
#         self.timeSpeed: TimeSpeed = TimeSpeed.NORMAL
#         self.dayNightCycleEnabled: bool = True
#         self.dayLength: float = 10.0
#         self.nightLength: float = 14.0
#         self.clock = pygame.time.Clock()
#         self.delta_time = 0  # Time between frames (in seconds)

#     def getWeeks(self) -> int:
#         """
#         Returns the 1-based in‑game week number.
#         One day-night cycle = one "day". 7 cycles = one week.
#         """
#         cycle = self.dayLength + self.nightLength
#         # how many full cycles (days) have passed?
#         days_passed = int(self.currentTime // cycle)
#         # each 7 days is a week, +1 so 0–6 → week 1, 7–13 → week 2, etc.
#         return (days_passed // 7) + 1

#     def setSpeedLevel(self, speed: TimeSpeed) -> None:
#         self.timeSpeed = speed

#     def getSpeedLevel(self) -> TimeSpeed:
#         return self.timeSpeed

#     def updateTime(self, delta: float) -> None:
#         mul = {TimeSpeed.SLOW: 0.3,
#                TimeSpeed.NORMAL: 1.0,
#                TimeSpeed.FAST: 3.0}[self.timeSpeed]

#         self.currentTime += delta * mul

#         if self.dayNightCycleEnabled:
#             cycle = self.dayLength + self.nightLength
#             # wrap around
#             if self.currentTime > cycle:
#                 self.currentTime %= cycle


#     def getCurrentTime(self) -> float:
#         return self.currentTime

#     def isNightTime(self) -> bool:
#       """True when clock has passed the stored dayLength."""
#       if not self.dayNightCycleEnabled:
#         return False
#       return self.currentTime >= self.dayLength

#     def toggleDayNightCycle(self) -> None:
#         self.dayNightCycleEnabled = not self.dayNightCycleEnabled

#     def getDayPortion(self) -> float:
#         """0..1 fraction through day (clamped to 1 once in night)."""
#         if self.currentTime < self.dayLength:
#             return self.currentTime / self.dayLength
#         return 1.0

#     def getNightPortion(self) -> float:
#         """0..1 fraction through night, resets once day begins."""
#         if self.currentTime < self.dayLength:
#             return 0.0
#         return (self.currentTime - self.dayLength) / self.nightLength