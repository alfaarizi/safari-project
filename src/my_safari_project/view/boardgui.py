import pygame
from pygame import Surface
from pygame.math import Vector2
from typing import Dict, Any, Tuple, List
import os
from my_safari_project.model.board import Board

class BoardGUI:
    """
    BoardGUI with:
    - A top bar (topBarHeight) at the top
    - A shop panel (shopWidth) on the right
    - The board in the remaining 'center' area
    - The number of row tiles = board.width, column tiles = board.height
    - Tile sizes computed so the board won't overflow
    - A desert background scaled to the board area
    - Grid lines, outer border, entity drawing
    - Day/night overlay
    """

    @staticmethod
    def lerp_color(c1, c2, t):
        """
        Interpolates between c1 and c2 (RGBA) by factor t in [0..1].
        """
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
            int(c1[3] + (c2[3] - c1[3]) * t),
        )

    def __init__(self, board: Board, tileW: int, tileH: int, isIso: bool):
        self.board = board
        self.tileW = tileW
        self.tileH = tileH
        self.isIso = isIso

        # The top bar and shop panel dimensions
        self.topBarHeight = 60
        self.shopWidth = 320

        # We'll keep track of the number of row & column tiles from the board model
        # plus a total number of tiles if needed
        self.numRowTiles = self.board.width
        self.numColTiles = self.board.height
        self.numTiles = self.numRowTiles * self.numColTiles

        # Additional state
        self.offsetX = 0
        self.offsetY = 0
        self.isometricMode = False
        self.dayNightOverlayOpacity = 0.0
        self.cameraX = 0.0
        self.cameraY = 0.0

        # Sprites and background
        self.terrainTextures: Dict[Any, Surface] = {}
        self.animalSprites: Dict[Any, Surface] = {}
        self.jeepSprite = None
        self.rangerSprite = None
        self.poacherSprite = None
        self.pondSprite = None
        self.cactusSprite = None
        self.desert_bg = None

        self.screen: Surface = None

        # If pygame is not initialized
        if not pygame.get_init():
            pygame.init()

        # Day/night cycle
        self.dayNightCycleEnabled = True
        self.dayNightTimer = 0.0
        self.totalCycleTime = 8 * 60  # e.g. 8 minutes: 5 day + 3 night

    def loadAssets(self) -> None:
        """
        Loads images from an 'images' folder, or uses fallbacks if not found.
        """
        base_dir = os.path.dirname(__file__)
        images_dir = os.path.join(base_dir, "images")

        # Desert background
        desert_path = os.path.join(images_dir, "desert.png")
        if os.path.exists(desert_path):
            desert_img = pygame.image.load(desert_path).convert()
            self.desert_bg = desert_img
        else:
            self.desert_bg = None

        # Cactus sprite for plants
        plant_path = os.path.join(images_dir, "plant.jpeg")
        if os.path.exists(plant_path):
            sprite = pygame.image.load(plant_path).convert_alpha()
            # We'll do an initial scale for fallback, but final sizing is still computed in render
            self.cactusSprite = pygame.transform.scale(
                sprite, (self.tileW, int(self.tileH * 1.2))
            )
        else:
            fallback_cactus = pygame.Surface((self.tileW, int(self.tileH * 1.2)), pygame.SRCALPHA)
            fallback_cactus.fill((34,139,34))
            self.cactusSprite = fallback_cactus

        # Pond
        pond_path = os.path.join(images_dir, "pond.jpeg")
        if os.path.exists(pond_path):
            pond_img = pygame.image.load(pond_path).convert_alpha()
            pond_img = pygame.transform.scale(
                pond_img, (int(self.tileW*1.5), int(self.tileH*1.2))
            )
            self.pondSprite = pond_img
        else:
            pond_surface = pygame.Surface((int(self.tileW*1.5), int(self.tileH*1.2)), pygame.SRCALPHA)
            pygame.draw.ellipse(pond_surface, (65,105,225),
                                (0,0,int(self.tileW*1.5),int(self.tileH*1.2)))
            self.pondSprite = pond_surface

        # Jeep, Ranger, Poacher placeholders
        self.jeepSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.rect(self.jeepSprite, (255,215,0),
                         (0,self.tileH//3,self.tileW,self.tileH//3))

        self.rangerSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.polygon(self.rangerSprite, (0,191,255),
                            [(self.tileW//2,0),(0,self.tileH),(self.tileW,self.tileH)])

        self.poacherSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.polygon(self.poacherSprite, (255,0,0),
                            [(self.tileW//2,0),(0,self.tileH),(self.tileW,self.tileH)])

    def render(self, screen: Surface) -> None:
        """
        Draws the board below a top bar and to the left of a shop panel.
        The final board area is:
          - from x=0..(screenWidth - shopWidth)
          - from y=topBarHeight..screenHeight
        We compute tile sizes so board.width columns and board.height rows fit in that area
        without overflowing.
        """
        self.screen = screen

        # 1) Full window size
        full_w, full_h = screen.get_size()

        # 2) The "top bar" occupies the top self.topBarHeight pixels,
        #    the "shop" occupies the right self.shopWidth pixels.
        #    So, the board's available area is:
        board_area_x = 0
        board_area_y = self.topBarHeight
        board_area_width = max(0, full_w - self.shopWidth)
        board_area_height = max(0, full_h - self.topBarHeight)

        # 3) We want exactly board.width columns and board.height rows of tiles.
        #    So, compute tileW, tileH from that available area:
        self.numRowTiles = self.board.width
        self.numColTiles = self.board.height
        self.numTiles = self.numRowTiles * self.numColTiles

        # if self.numRowTiles > 0:
        #     self.tileW = max(1, board_area_width // self.numRowTiles)
        # if self.numColTiles > 0:
        #     self.tileH = max(1, board_area_height // self.numColTiles)

        # board_width_px = self.numRowTiles * self.tileW
        # board_height_px = self.numColTiles * self.tileH
        if self.numRowTiles > 0 and self.numColTiles > 0:
            tile_side_w = board_area_width // self.numRowTiles
            tile_side_h = board_area_height // self.numColTiles
            tile_side = min(tile_side_w, tile_side_h)
            tile_side = max(tile_side, 1)  # ensure at least 1 pixel

        # Now both tileW and tileH are the same
        self.tileW = tile_side
        self.tileH = tile_side

        # 3) Board area in pixels
        board_width_px = self.numRowTiles * self.tileW
        board_height_px = self.numColTiles * self.tileH

        # 4) Fill entire window in a base color
        screen.fill((255, 255, 153))
        # 5) Draw the desert background in the offset region (board_area_x, board_area_y)
        if self.desert_bg:
            # Scale desert to the actual board area
            background_scaled = pygame.transform.scale(self.desert_bg, (board_width_px, board_height_px))
            screen.blit(background_scaled, (board_area_x, board_area_y))
        else:
            pygame.draw.rect(screen, (255, 255, 153),
                             (board_area_x, board_area_y, board_width_px, board_height_px))

        # 6) Draw a thin, gray outer border around the board
        pygame.draw.rect(
            screen,
            (128,128,128),
            (board_area_x, board_area_y, board_width_px, board_height_px),
            2
        )

        # 7) Draw grid lines
        for x in range(self.numRowTiles + 1):
            xx = board_area_x + x * self.tileW
            pygame.draw.line(screen, (0,0,0),
                             (xx, board_area_y),
                             (xx, board_area_y + board_height_px),
                             1)
        for y in range(self.numColTiles + 1):
            yy = board_area_y + y * self.tileH
            pygame.draw.line(screen, (0,0,0),
                             (board_area_x, yy),
                             (board_area_x + board_width_px, yy),
                             1)

        # 8) Draw the board entities in the offset region
        self.drawPonds(screen, board_area_x, board_area_y)
        self.drawPlants(screen, board_area_x, board_area_y)
        self.drawAnimals(screen, board_area_x, board_area_y)
        self.drawJeep(screen, board_area_x, board_area_y)
        self.drawRangers(screen, board_area_x, board_area_y)
        self.drawPoachers(screen, board_area_x, board_area_y)
        self.drawRoads(screen, board_area_x, board_area_y)

        # 9) Apply day/night overlay over the entire window
        if self.dayNightOverlayOpacity > 0:
            day_tint = (255,255,255,0)
            night_tint = (0,0,70,160)
            tint_color = self.lerp_color(day_tint, night_tint, self.dayNightOverlayOpacity)
            overlay = pygame.Surface((full_w, full_h), pygame.SRCALPHA)
            overlay.fill(tint_color)
            screen.blit(overlay, (0,0))

    # adapt each draw method to accept (offset_x, offset_y)
    def drawPonds(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for pond in self.board.ponds:
            loc = getattr(pond, 'location', Vector2(0,0))
            x = offset_x + int(loc.x * self.tileW)
            y = offset_y + int(loc.y * self.tileH)
            screen.blit(self.pondSprite, (x,y))

    def drawPlants(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for plant in self.board.plants:
            loc = getattr(plant, 'location', Vector2(0,0))
            x = offset_x + int(loc.x * self.tileW)
            # shift cactus so its bottom sits at the tile's bottom
            y = offset_y + int(loc.y * self.tileH - (self.cactusSprite.get_height() - self.tileH))
            screen.blit(self.cactusSprite, (x,y))

    def drawAnimals(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        pass

    def drawJeep(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for jeep in self.board.jeeps:
            loc = getattr(jeep, 'location', Vector2(0,0))
            x = offset_x + int(loc.x * self.tileW)
            y = offset_y + int(loc.y * self.tileH)
            screen.blit(self.jeepSprite, (x,y))

    def drawRangers(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for ranger in self.board.rangers:
            loc = getattr(ranger, 'position', Vector2(0,0))
            x = offset_x + int(loc.x * self.tileW)
            y = offset_y + int(loc.y * self.tileH)
            screen.blit(self.rangerSprite, (x,y))

    def drawPoachers(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for poacher in self.board.poachers:
            loc = getattr(poacher, 'position', Vector2(0,0))
            x = offset_x + int(loc.x * self.tileW)
            y = offset_y + int(loc.y * self.tileH)
            screen.blit(self.poacherSprite, (x,y))

    def drawRoads(self, screen: Surface, offset_x: int, offset_y: int) -> None:
        for road in self.board.roads:
            if len(road.points) < 2:
                continue
            points = []
            for p in road.points:
                px = offset_x + int(p.x * self.tileW + self.tileW//2)
                py = offset_y + int(p.y * self.tileH + self.tileH//2)
                points.append((px, py))
            pygame.draw.lines(screen, (105,105,105), False, points, 4)

    # Day/night
    def setDayNightOverlayOpacity(self, opacity: float) -> None:
        self.dayNightOverlayOpacity = max(0.0, min(1.0, opacity))

    def updateDayNightCycle(self, delta_time: float) -> None:
        if not self.dayNightCycleEnabled:
            return
        self.dayNightTimer += delta_time
        if self.dayNightTimer > self.totalCycleTime:
            self.dayNightTimer -= self.totalCycleTime

        t = self.dayNightTimer
        # 5 min day (0..300s), 3 min night (300..480s)
        if t < 270:  # pure day
            self.setDayNightOverlayOpacity(0.0)
        elif t < 300:  # day->night transition
            fraction = (t - 270) / 30.0
            self.setDayNightOverlayOpacity(fraction)
        elif t < 450:  # pure night
            self.setDayNightOverlayOpacity(1.0)
        else:  # night->day transition
            fraction = 1.0 - ((t - 450) / 30.0)
            self.setDayNightOverlayOpacity(fraction)

    def toggleIsometricMode(self) -> None:
        self.isometricMode = not self.isometricMode

    def getCameraPosition(self) -> Tuple[float,float]:
        return (self.cameraX, self.cameraY)

    def setCameraPosition(self, x: float, y: float) -> None:
        self.cameraX = x
        self.cameraY = y

    def handleResize(self, newWidth: int, newHeight: int) -> None:
        """
        Only if you want to programmatically resize the window from BoardGUI.
        """
        self.screen = pygame.display.set_mode((newWidth, newHeight))

<<<<<<< HEAD:src/my_safari_project/view/boardgui.py
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
=======
>>>>>>> origin/31-Implement-BoardGUI:src/my_safari_project/view/BoardGUI.py
