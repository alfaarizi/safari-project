class Pond:
    def __init__(self,
                 pondID: int,
                 location: tuple,
                 name: str,
                 buildCost: int,
                 retentionCost: int,
                 capacity: float,
                 evaporationRate: float):

        self.pondID: int = pondID
        self.location: tuple = location  # (x, y)
        self.name: str = name
        self.buildCost: int = buildCost
        self.retentionCost: int = retentionCost
        self.capacity: float = capacity
        self.currentLevelOfWater: float = capacity #setting it to capacity
        self.evaporationRate: float = evaporationRate
        self.isDepleted: bool = False

    def refill(self, amount: float) -> None:
  
        if self.isDepleted:
            self.isDepleted = False
        self.currentLevelOfWater += amount
        if self.currentLevelOfWater > self.capacity:
            self.currentLevelOfWater = self.capacity

    def evaporate(self) -> None:

        self.currentLevelOfWater -= self.evaporationRate
        if self.currentLevelOfWater < 0:
            self.currentLevelOfWater = 0
        if self.currentLevelOfWater == 0:
            self.isDepleted = True

    def supplyWater(self, amount: float) -> float:
    
        if self.currentLevelOfWater <= 0:
            self.isDepleted = True
            return 0.0

        if amount >= self.currentLevelOfWater:
            supplied = self.currentLevelOfWater
            self.currentLevelOfWater = 0
            self.isDepleted = True
            return supplied
        else:
            self.currentLevelOfWater -= amount
            if self.currentLevelOfWater <= 0:
                self.currentLevelOfWater = 0
                self.isDepleted = True
            return amount

    def isEmpty(self) -> bool:

        return self.currentLevelOfWater <= 0