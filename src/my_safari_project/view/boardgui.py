import pygame
import math
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.pond import Pond
from my_safari_project.model.plant import Plant
from my_safari_project.model.animal import Animal
from my_safari_project.model.jeep import Jeep
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.model.road import Road

class BoardGUI:
    def __init__(self, board: Board, tile_width=64, tile_height=64, isometric=False):
        """
        Initializes the BoardGUI with a Board model instance and visual settings.
        """
        self.board = board
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.isometric_mode = isometric
        self.day_night_opacity = 0.0  # 0.0 = day, 1.0 = night
        self.camera_x = 0
        self.camera_y = 0

        # Colors defined according to the UML/design spec
        self.colors = {
            'sand': (194, 178, 128),
            'sand_dark': (160, 140, 90),
            'water': (65, 105, 225),
            'plant': (34, 139, 34),
            'animal': (255, 69, 0),
            'jeep': (255, 215, 0),
            'ranger': (0, 191, 255),
            'poacher': (255, 0, 0),
            'road': (105, 105, 105),
            'night': (10, 10, 30)
        }

        # Ensure pygame is initialized
        if not pygame.get_init():
            pygame.init()

        self.screen = None
        self.overlay = None

    def init_gui(self, screen_width=800, screen_height=600):
        """
        Initializes the pygame display and overlay surface.
        """
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Safari Game")
        self.overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

    def draw_board(self):
        """
        Clears the screen, draws the background grid, and renders all entities.
        """
        self.screen.fill(self.colors['sand'])

        # Draw grid lines
        for x in range(0, self.screen.get_width(), self.tile_width):
            pygame.draw.line(self.screen, self.colors['sand_dark'], (x, 0), (x, self.screen.get_height()))
        for y in range(0, self.screen.get_height(), self.tile_height):
            pygame.draw.line(self.screen, self.colors['sand_dark'], (0, y), (self.screen.get_width(), y))

        # Draw entities in order (back to front)
        self.draw_ponds()
        self.draw_plants()
        self.draw_animals()
        self.draw_jeeps()
        self.draw_rangers()
        self.draw_poachers()
        self.draw_roads()

        # Apply day/night overlay 
        self.apply_day_night_overlay()

        pygame.display.flip()

    def draw_ponds(self):
        """
        Draws each pond as an ellipse. Assumes pond.location is either a tuple (x,y)
        or a pygame.math.Vector2.
        """
        for pond in self.board.ponds:
            # Adapt to location type
            if hasattr(pond.location, 'x'):
                x = int(pond.location.x * self.tile_width)
                y = int(pond.location.y * self.tile_height)
            else:
                x = int(pond.location[0] * self.tile_width)
                y = int(pond.location[1] * self.tile_height)
            rect = pygame.Rect(
                x - self.camera_x, 
                y - self.camera_y, 
                int(self.tile_width * 1.5), 
                int(self.tile_height * 1.2)
            )
            pygame.draw.ellipse(self.screen, self.colors['water'], rect)

    def draw_plants(self):
        """
        Draws plants as circles with stems. Assumes plant.location is a Vector2.
        """
        for plant in self.board.plants:
            x = int(plant.location.x * self.tile_width + self.tile_width / 2)
            y = int(plant.location.y * self.tile_height + self.tile_height / 2)
            # Draw stem
            pygame.draw.line(
                self.screen, 
                (50, 205, 50),
                (x - self.camera_x, y - self.camera_y + 10),
                (x - self.camera_x, y - self.camera_y - 10),
                3
            )
            # Draw plant crown
            pygame.draw.circle(
                self.screen, 
                self.colors['plant'],
                (x - self.camera_x, y - self.camera_y - 15),
                12
            )

    def draw_animals(self):
        """
        Draws animals as simple circles. Assumes animal.location is a Vector2.
        """
        for animal in self.board.animals:
            x = int(animal.location.x * self.tile_width + self.tile_width / 2)
            y = int(animal.location.y * self.tile_height + self.tile_height / 2)
            pygame.draw.circle(self.screen, self.colors['animal'], (x - self.camera_x, y - self.camera_y), 10)

    def draw_jeeps(self):
        """
        Draws jeeps as rectangles. Assumes jeep.location is a Vector2.
        """
        for jeep in self.board.jeeps:
            x = int(jeep.location.x * self.tile_width)
            y = int(jeep.location.y * self.tile_height)
            rect = pygame.Rect(
                x - self.camera_x,
                y - self.camera_y,
                int(self.tile_width * 0.8),
                int(self.tile_height * 0.5)
            )
            pygame.draw.rect(self.screen, self.colors['jeep'], rect)

    def draw_rangers(self):
        """
        Draws rangers as triangles. Assumes ranger.location is a Vector2.
        """
        for ranger in self.board.rangers:
            x = int(ranger.location.x * self.tile_width + self.tile_width / 2)
            y = int(ranger.location.y * self.tile_height + self.tile_height / 2)
            points = [
                (x - self.camera_x, y - self.camera_y - 10),  # Top point
                (x - self.camera_x - 8, y - self.camera_y + 10),  # Bottom left
                (x - self.camera_x + 8, y - self.camera_y + 10)   # Bottom right
            ]
            pygame.draw.polygon(self.screen, self.colors['ranger'], points)

    def draw_poachers(self):
        """
        Draws poachers as triangles. Assumes poacher.location is a Vector2.
        """
        for poacher in self.board.poachers:
            x = int(poacher.location.x * self.tile_width + self.tile_width / 2)
            y = int(poacher.location.y * self.tile_height + self.tile_height / 2)
            points = [
                (x - self.camera_x, y - self.camera_y - 10),
                (x - self.camera_x - 8, y - self.camera_y + 10),
                (x - self.camera_x + 8, y - self.camera_y + 10)
            ]
            pygame.draw.polygon(self.screen, self.colors['poacher'], points)

    def draw_roads(self):
        """
        Draws roads as gray lines. Assumes each road has a list of points (Vector2).
        """
        for road in self.board.roads:
            if len(road.points) >= 2:
                points = [
                    (int(p.x * self.tile_width + self.tile_width / 2 - self.camera_x),
                     int(p.y * self.tile_height + self.tile_height / 2 - self.camera_y))
                    for p in road.points
                ]
                pygame.draw.lines(self.screen, self.colors['road'], False, points, 5)

    def apply_day_night_overlay(self):
        """
        Applies a translucent overlay for the day/night cycle.
        """
        if self.day_night_opacity > 0:
            self.overlay.fill((0, 0, 0, int(200 * self.day_night_opacity)))
            self.screen.blit(self.overlay, (0, 0))

    def set_day_night_opacity(self, opacity: float):
        """
        Sets the opacity for the day/night overlay (clamped between 0.0 and 1.0).
        """
        self.day_night_opacity = max(0.0, min(1.0, opacity))

    def toggle_isometric_mode(self):
        """
        Toggles between isometric and orthogonal views.
        (Implement isometric projection transformation if required by the UML.)
        """
        self.isometric_mode = not self.isometric_mode
        # Apply any view transformation changes here if needed


# Test harness (only run if executed directly)

if __name__ == '__main__':

    # The following is an example assuming the model classes are properly defined.
    board = Board(width=10, height=8)
    
    # Add two ponds and two plants (using your actual constructors)
    board.ponds.append(Pond(1, Vector2(2, 3), "Oasis", 100, 200, 400, 500))
    board.ponds.append(Pond(2, Vector2(7, 5), "Waterhole", 100, 200, 400, 500))
    board.plants.append(Plant(1, Vector2(4, 2), "Acacia", 50, 0.1, 100, True))
    board.plants.append(Plant(2, Vector2(5, 6), "Baobab", 70, 0.05, 200, False))
    
    # Ensuring the other lists exist even if empty
    board.animals = []
    board.jeeps = []
    board.rangers = []
    board.poachers = []
    board.roads = []

    gui = BoardGUI(board)
    gui.init_gui(800, 600)

    clock = pygame.time.Clock()
    running = True
    time_counter = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Toggle isometric mode with the spacebar
                if event.key == pygame.K_SPACE:
                    gui.toggle_isometric_mode()

       # time_counter += 0.01
        #if time_counter > 10:
           # time_counter = 0
       # gui.set_day_night_opacity(abs(math.sin(time_counter * math.pi / 5)))
        gui.draw_board()
        clock.tick(60)

    pygame.quit()
