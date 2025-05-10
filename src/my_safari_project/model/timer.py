import pygame

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
    
    def tick(self, speed: float = 1.0) -> float:
        """
        Advance the in-game clock by real_dt * speed
        Returns that *scaled* at so callers can step their logic.
        """
        real_dt = self.clock.tick(60) / 1000.0# seconds
        dt = real_dt * speed
        self.elapsed_seconds += dt
        return dt
    
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