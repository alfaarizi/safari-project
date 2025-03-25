import random
from Animal import Animal


class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def getX(self) -> int:
        return self.x
    
    def getY(self) -> int:
        return self.y

class Ranger:
    def __init__(self, id: int, name: str, salary: float, position: Position):
        self.id = id
        self.name = name
        self.salary = salary
        self.position = position
        self.isOnDuty = True
        self.poachersCaught = 0
        self.animalsEliminated = 0
    
    def patrol(self):
        self.position.x += random.randint(-1, 1)
        self.position.y += random.randint(-1, 1)
    
    def eliminatePoacher(self, poacher) -> bool:
        if poacher.isHunting:
            poacher.isHunting = False
            self.poachersCaught += 1
            return True
        return False
    
    def eliminateAnimal(self, animal) -> bool:
        if isinstance(animal, Animal) and animal.isAlive:
            animal.isAlive = False
            self.animalsEliminated += 1
            return True
        return False
    
    def getisOnDuty(self) -> bool:
        return self.isOnDuty
    
    def receiveSalary(self, capital) -> bool:
        return capital.deductFunds(self.salary)

