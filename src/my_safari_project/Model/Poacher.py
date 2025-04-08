import random
from my_safari_project.model.ranger import Position
from my_safari_project.model.animal import Animal

class Poacher:
    def __init__(self, id: int, name: str, position: "Position"):
        self.id = id
        self.name = name
        self.isHunting = True
        self.position = position
        self.animalsCaught = 0
        self.timesSpotted = 0
    
    def huntAnimal(self, animal) -> bool:
        if isinstance(animal, Animal) and animal.isAlive:
            animal.isAlive = False
            self.animalsCaught += 1
            return True
        return False
    
    def evadeRanger(self, ranger) -> bool:
        success = random.choice([True, False])
        if not success:
            self.timesSpotted += 1
        return success
    
    def moveRandomly(self):
        self.position.x += random.randint(-1, 1)
        self.position.y += random.randint(-1, 1)
    
    def isVisibleTo(self, p: "Position") -> bool:
        return abs(self.position.x - p.x) <= 1 and abs(self.position.y - p.y) <= 1
