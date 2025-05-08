import random

class Plant:
    def __init__(
        self,
        plantID: int,
        position: tuple,
        name: str,
        value: int,
        growthRate: float,
        maxSize: float,
        isEatable: bool
    ):
        self.plantID: int = plantID
        self.position: tuple = position  # (x, y)
        self.name: str = name
        self.value: int = value
        self.growthRate: float = growthRate
        self.maxSize: float = maxSize
        self.isEatable: bool = isEatable

        self.currentSize: float = 0.0
        self.isAlive: bool = True

        # Reproduction cooldown in hours.if it triggers, the plant must wait this many hours to reproduce again.
        self.reproductionCooldown = 5.0
        
        #Keeps track of time elapsed since the last reproduction event.
        self.timeSinceLastReproduction = 0.0

    def update(self, hoursPassed: float) -> None:
   
        if not self.isAlive:
            return

        # Grow
        self.currentSize += self.growthRate * hoursPassed
        if self.currentSize > self.maxSize:
            self.currentSize = self.maxSize

        # Increment the time since the last reproduction.
        self.timeSinceLastReproduction += hoursPassed

        # If the plant is mature and the reproduction cooldown has passed, reproduce.
        if self.isMature() and self.timeSinceLastReproduction >= self.reproductionCooldown:
            self.reproduce()
            self.timeSinceLastReproduction = 0.0
    # it creates an offspring plant at a position offset from the parent 
    def reproduce(self) -> None:
 
        if not self.isAlive:
            return

        # Generate a small random offset so the offspring isn't in the same exact spot.
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        new_position = (self.position[0] + offset_x, self.position[1] + offset_y)

        # Generating distinct plantID.
        new_plant_id = self.plantID * 100 + random.randint(1, 99)

        # Create the offspring plant
        new_plant = Plant(
            plantID=new_plant_id,
            position=new_position,
            name=self.name,
            value=self.value,
            growthRate=self.growthRate,
            maxSize=self.maxSize,
            isEatable=self.isEatable
        )


        print(f"Plant {self.plantID} reproduced! Offspring {new_plant_id} created at {new_position}.")

    def getEaten(self, amount: float) -> None:

        if not self.isAlive:
            return
        self.currentSize -= amount
        if self.currentSize < 0:
            self.currentSize = 0
            self.wither()

    def wither(self) -> None:

        self.isAlive = False
        self.currentSize = 0

    def isMature(self) -> bool:

        return self.currentSize >= self.maxSize
