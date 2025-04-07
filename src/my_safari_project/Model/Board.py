from pygame.math import Vector2
from collections import deque
from typing import List, Optional

from my_safari_project.model.field import Field
from my_safari_project.model.road import Road
from my_safari_project.model.pond import Pond
from my_safari_project.model.plant import Plant
from my_safari_project.model.animal import Animal
from my_safari_project.model.jeep import Jeep
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher

class Board:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        self.fields: List[List[Field]] = []
        self.roads: List[Road] = []
        self.ponds: List[Pond] = []
        self.plants: List[Plant] = []
        self.animals: List[Animal] = []
        self.jeeps: List[Jeep] = []
        self.rangers: List[Ranger] = []
        self.poachers: List[Poacher] = []
        self.obstaclesEnabled = True
    
    def initializeBoard(self):
        """Initialize the board with empty fields"""
        for y in range(self.height):
            for x in range(self.width):
                self.fields[y][x] = Field(Vector2(x, y))
    
    def getField(self, x: int, y: int) -> Optional[Field]:
        """Returns the field at the given coordinates."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.fields[y][x]
        return None
    
    def addRoad(self, road: Road):
        """Adds a road to the board."""
        self.roads.append(road)
    
    def addPond(self, pond: Pond):
        """Adds a pond to the board."""
        self.ponds.append(pond)
    
    def addPlant(self, plant: Plant):
        """Adds a plant to the board."""
        self.plants.append(plant)
    
    def addAnimal(self, animal: Animal):
        """Adds an animal to the board."""
        self.animals.append(animal)
    
    def removeAnimal(self, animal: Animal):
        """Removes an animal from the board."""
        try:
            self.animals.remove(animal)
        except:
            pass
    
    def addJeep(self, jeep: Jeep):
        """Adds a jeep to the board."""
        self.jeeps.append(jeep)
    
    def addRanger(self, ranger: Ranger):
        """Adds a ranger to the board."""
        self.rangers.append(ranger)
    
    def addPoacher(self, poacher: Poacher):
        """Adds a poacher to the board."""
        self.poachers.append(poacher)
    
    def updateAll(self, deltaTime: float):
        """Sample Implementation"""
        """Update all entities on the board based on the time delta."""
        for animal in self.animals:
            animal.age += deltaTime
            if animal.is_alive():
                # animals move, eat, drink, and reproduce here
                animal.add_hunger()
                animal.add_thirst()
                animal.move(Vector2(0, 0))  # update to move towards the target, this is a placeholder.
                
                # reproduce if possible
                for other_animal in self.animals:
                    if animal is not other_animal and animal.is_alive():
                        new_animal = animal.reproduce(other_animal)
                        if new_animal:
                            self.addAnimal(new_animal)
        # additional updates for jeeps, rangers, poachers, etc.
    
    def drawAll(self):
        pass
        # """Renders the board and everything on it."""
        # for row in self.fields:
        #     for field in row:
        #         field.draw()  # placeholder for drawing each field, implementation depends on your graphic engine

        # # render other entities (roads, ponds, plants, animals, jeeps, etc.)
        # for road in self.roads:
        #     road.draw()
        # for pond in self.ponds:
        #     pond.draw()
        # for plant in self.plants:
        #     plant.draw()
        # for animal in self.animals:
        #     animal.draw()
        # for jeep in self.jeeps:
        #     jeep.draw()
        # for ranger in self.rangers:
        #     ranger.draw()
        # for poacher in self.poachers:
        #     poacher.draw()
    
    def findPath(self, start: Field, end: Field) -> List[Field]:
        """Finds a path between start and end using a bfs pathfinding algorithm"""
        open_list = deque([start])
        came_from = {}
        
        while open_list:
            current = open_list.popleft()
            
            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()  # returns path from start to end
                return path
            
            for neighbor in self.get_neighbors(current):
                if neighbor not in came_from:
                    open_list.append(neighbor)
                    came_from[neighbor] = current
        
        return []  # returns an empty path if no path found
    
    def get_neighbors(self, field: Field) -> List[Field]:
        """Returns the neighboring fields of a given field."""
        neighbors = []
        x, y = field.position.x, field.position.y
        
        # checks the neighboring fields (up, down, left, right)
        if x > 0:
            neighbors.append(self.fields[y][x - 1])
        if x < self.width - 1:
            neighbors.append(self.fields[y][x + 1])
        if y > 0:
            neighbors.append(self.fields[y - 1][x])
        if y < self.height - 1:
            neighbors.append(self.fields[y + 1][x])
        
        return neighbors
