import pygame
from pygame.math import Vector2

import pygame
from pygame.math import Vector2
from board import Board
from my_safari_project.Model.field import Field  # Make sure Field has a minimal constructor and, if needed, a draw() method.


class BoardGUI:
    """
    A GUI class for rendering the game board and its entities using Pygame.
    """
    def __init__(self, board, tile_size=64):
        """
        :param board: An instance of Board (your game board).
        :param tile_size: The pixel size of each board tile.
        """
        self.board = board
        self.tile_size = tile_size
        self.screen = None

    def init_gui(self):
        """
        Initializes Pygame and sets up the window using the board dimensions.
        """
        pygame.init()
        window_width = self.board.width * self.tile_size
        window_height = self.board.height * self.tile_size
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Safari Game Board")

    def draw_board(self):
        """
        Draws the background board grid. Here we fill each field with a green shade
        and draw grid lines. You can replace this with more detailed images if desired.
        """
        for row in range(self.board.height):
            for col in range(self.board.width):
                # Calculate the pixel rectangle for the tile
                rect = pygame.Rect(col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size)
                # Fill with a light green (for example)
                pygame.draw.rect(self.screen, (144, 238, 144), rect)
                # Draw grid lines (black borders)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def draw_roads(self):
        """
        Draws the roads. This example assumes each Road object has a 'points'
        attribute which is a list of Vector2 positions (in board coordinates).
        """
        for road in self.board.roads:
            if hasattr(road, 'points'):
                # Convert board coordinates to pixel positions
                points = [(int(p.x * self.tile_size + self.tile_size / 2),
                           int(p.y * self.tile_size + self.tile_size / 2))
                          for p in road.points]
                if len(points) >= 2:
                    pygame.draw.lines(self.screen, (128, 128, 128), False, points, 5)

    def draw_ponds(self):
        """
        Draws ponds as blue ellipses. Assumes each Pond has a 'location' property.
        """
        for pond in self.board.ponds:
            if hasattr(pond, 'location'):
                # Convert pond location to pixel coordinates
                x = int(pond.location[0] * self.tile_size)
                y = int(pond.location[1] * self.tile_size)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.ellipse(self.screen, (0, 0, 255), rect)

    def draw_plants(self):
        """
        Draws plants as green rectangles. Assumes each Plant has a 'location' property.
        """
        for plant in self.board.plants:
            if hasattr(plant, 'location'):
                x = int(plant.location[0] * self.tile_size)
                y = int(plant.location[1] * self.tile_size)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, (34, 139, 34), rect)
                # Optionally, you could add a text label or growth indicator here.

    def draw_animals(self):
        """
        Draws animals as red circles. Assumes each Animal has a 'location' property.
        """
        for animal in self.board.animals:
            if hasattr(animal, 'location'):
                x = int(animal.location[0] * self.tile_size)
                y = int(animal.location[1] * self.tile_size)
                center = (x + self.tile_size // 2, y + self.tile_size // 2)
                pygame.draw.circle(self.screen, (255, 0, 0), center, self.tile_size // 3)

    def draw_jeeps(self):
        """
        Draws jeeps as yellow rectangles. Assumes each Jeep has a 'location' property.
        """
        for jeep in self.board.jeeps:
            if hasattr(jeep, 'location'):
                x = int(jeep.location[0] * self.tile_size)
                y = int(jeep.location[1] * self.tile_size)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, (255, 255, 0), rect)

    def draw_rangers(self):
        """
        Draws rangers as cyan rectangles. Assumes each Ranger has a 'location' property.
        """
        for ranger in self.board.rangers:
            if hasattr(ranger, 'location'):
                x = int(ranger.location[0] * self.tile_size)
                y = int(ranger.location[1] * self.tile_size)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, (0, 255, 255), rect)

    def draw_poachers(self):
        """
        Draws poachers as magenta rectangles. Assumes each Poacher has a 'location' property.
        """
        for poacher in self.board.poachers:
            if hasattr(poacher, 'location'):
                x = int(poacher.location[0] * self.tile_size)
                y = int(poacher.location[1] * self.tile_size)
                rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, (255, 0, 255), rect)

    def update(self):
        """
        Redraws the entire board and all entities.
        Call this in your main game loop.
        """
        if not self.screen:
            return
        # Draw the background board
        self.draw_board()
        # Draw all entities on top
        self.draw_roads()
        self.draw_ponds()
        self.draw_plants()
        self.draw_animals()
        self.draw_jeeps()
        self.draw_rangers()
        self.draw_poachers()
        # Update the display
        pygame.display.flip()

import pygame
from pygame.math import Vector2
from board import Board
from board_gui import BoardGUI
from field import Field  # Make sure Field has a minimal constructor and, if needed, a draw() method.

def main():
    # Create a Board instance with a width of 10 columns and height of 8 rows.
    board = Board(width=10, height=8)
    
    # Initialize board.fields as a 2D list of Field objects.
    # (If your Board.initializeBoard() is not complete, do it manually here.)
    board.fields = [[None for _ in range(board.width)] for _ in range(board.height)]
    for y in range(board.height):
        for x in range(board.width):
            # Create a Field with a position (using Vector2).
            board.fields[y][x] = Field(Vector2(x, y))
    
    # Optionally add some sample entities:
    # For instance, add a Pond and a Plant to see them rendered.
    from pond import Pond
    from plant import Plant
    board.ponds.append(Pond(pondID=1, location=(2, 3), name="Oasis", buildCost=100, retentionCost=10, capacity=500.0, evaporationRate=2.0))
    board.plants.append(Plant(plantID=1, location=(5, 4), name="Acacia", value=50, growthRate=0.5, maxSize=100.0, isEatable=True))
    
    # Create a BoardGUI instance with a tile size of 64 pixels.
    board_gui = BoardGUI(board, tile_size=64)
    board_gui.init_gui()
    
    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)  # Limit to 60 FPS
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update the board GUI (draw the board and all entities)
        board_gui.update()

    pygame.quit()

if __name__ == "__main__":
    main()
