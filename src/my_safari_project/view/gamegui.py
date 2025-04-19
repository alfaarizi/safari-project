import pygame
from my_safari_project.model.board import Board
from pygame import Surface
from pygame.math import Vector2
from typing import Dict, Any, Tuple, List
import os


class BoardGUI:
    """
    BoardGUI class with:
      - A desert tile background from an image file (desert.png)
      - A gray, thinner outer box
      - A cactus image for plants (plant.jpeg)
      - A pond image for ponds (pond.jpeg)
      - day/night overlay
    """

    @staticmethod
    def lerp_color(c1, c2, t):
        """
        Linearly interpolate between two RGBA colors c1 and c2 with 0 <= t <= 1.
        Returns a new (R,G,B,A) tuple.
        """
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
            int(c1[3] + (c2[3] - c1[3]) * t),
        )

    def __init__(self, board: Board, tileW: int, tileH: int, isIso: bool):
        self.board: Board = board
        self.tileW: int = tileW
        self.tileH: int = tileH
        self.isIso: bool = isIso

        self.offsetX: int = 0
        self.offsetY: int = 0
        self.isometricMode: bool = False
        self.dayNightOverlayOpacity: float = 0.0
        self.cameraX: float = 0.0
        self.cameraY: float = 0.0

        self.terrainTextures: Dict[Any, Surface] = {}
        self.animalSprites: Dict[Any, Surface] = {}

        self.jeepSprite: Surface = None
        self.rangerSprite: Surface = None
        self.poacherSprite: Surface = None
        self.pondSprite: Surface = None
        self.cactusSprite: Surface = None   # For plants

        self.screen: Surface = None
        self.desert_bg: Surface = None

        # If Pygame not initialized
        if not pygame.get_init():
            pygame.init()

        # Day/Night cycle settings
        self.dayNightCycleEnabled: bool = True
        self.dayNightTimer: float = 0.0
        self.totalCycleTime: float = 8 * 60  # 8 minutes total: 5 day + 3 night
    
    def loadAssets(self) -> None:
        """
        Loads external images (if they exist): desert.png, plant.jpeg, pond.jpeg.
        Otherwise, uses fallback colors/shapes.
        """
        base_dir = os.path.dirname(__file__)
        images_dir = os.path.join(base_dir, "images")
        # 1) Desert tile texture -> terrainTextures["default"]

        desert_path = os.path.join(images_dir, "desert.png")
        if os.path.exists(desert_path):
            # Scale desert tile to exactly tileW x tileH
            #desert_img = pygame.transform.scale(desert_img, (self.tileW, self.tileH))
            desert_img = pygame.image.load(desert_path).convert()
            self.desert_bg = desert_img
        else:
            # fallback: a baby-yellow surface
            #fallback_tile = pygame.Surface((self.tileW, self.tileH))
            #fallback_tile.fill((255, 255, 153))  # desert-like color
            #self.terrainTextures["default"] = fallback_tile
            self.desert_bg = None

        # 2) Cactus sprite for plants -> self.cactusSprite
        if os.path.exists("plant.jpeg"):
            sprite = pygame.image.load("plant.jpeg").convert_alpha()
            self.cactusSprite = pygame.transform.scale(
                sprite,
                (self.tileW, int(self.tileH * 1.2))
            )
        else:
            # fallback: green rectangle
            fallback_cactus = pygame.Surface((self.tileW, int(self.tileH * 1.2)), pygame.SRCALPHA)
            fallback_cactus.fill((34, 139, 34))
            self.cactusSprite = fallback_cactus

        # 3) Pond sprite -> self.pondSprite
        if os.path.exists("pond.jpeg"):
            pond_img = pygame.image.load("pond.jpeg").convert_alpha()
            # Scale the pond bigger than a tile
            pond_img = pygame.transform.scale(
                pond_img, (int(self.tileW * 1.5), int(self.tileH * 1.2))
            )
            self.pondSprite = pond_img
        else:
            # fallback: ellipse on a Surface
            pond_surface = pygame.Surface((int(self.tileW * 1.5), int(self.tileH * 1.2)), pygame.SRCALPHA)
            pygame.draw.ellipse(pond_surface, (65, 105, 225),
                                (0, 0, int(self.tileW * 1.5), int(self.tileH * 1.2)))
            self.pondSprite = pond_surface

        # 4) Jeep, Ranger, Poacher placeholders
        self.jeepSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.rect(self.jeepSprite, (255, 215, 0),
                         (0, self.tileH // 3, self.tileW, self.tileH // 3))

        self.rangerSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.polygon(self.rangerSprite, (0, 191, 255),
                            [(self.tileW // 2, 0), (0, self.tileH), (self.tileW, self.tileH)])

        self.poacherSprite = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
        pygame.draw.polygon(self.poacherSprite, (255, 0, 0),
                            [(self.tileW // 2, 0), (0, self.tileH), (self.tileW, self.tileH)])


    def render(self, screen: Surface) -> None:
        """
        Renders a single large desert background image over the entire board area.
        Draws an outer gray box around it, and then draws ponds, plants, etc.
        Applies day/night color overlay.
        """
        self.screen = screen
        screen.fill((255, 255, 153))

    # Calculate board size in pixels
        board_width_px = self.board.width * self.tileW
        board_height_px = self.board.height * self.tileH


    # fill that board area with a desert color.
        if self.desert_bg:
        # Scale the desert_bg to the board's size
            bg_scaled = pygame.transform.scale(self.desert_bg, (board_width_px, board_height_px))
            screen.blit(bg_scaled, (0, 0))
        else:
        # Fallback: fill the board area with a desert-like color
             pygame.draw.rect(screen, (255, 255, 153), (0, 0, board_width_px, board_height_px))

    # Draw a thin, gray outer box around the entire board area
        border_color = (128, 128, 128)
        border_thickness = 2
        pygame.draw.rect(
        screen,
        border_color,
        (0, 0, board_width_px, board_height_px),
        border_thickness
    )
    
        for x in range(self.board.width + 1):
            pygame.draw.line(
                screen, (0, 0, 0),
                (x * self.tileW, 0),
                (x * self.tileW, board_height_px),
                1
            )
        for y in range(self.board.height + 1):
            pygame.draw.line(
            screen, (0, 0, 0),
            (0, y * self.tileH),
            (board_width_px, y * self.tileH),
            1
    )

    # Draw entities (ponds, plants, etc.)
        self.drawPonds(screen)
        self.drawPlants(screen)
        self.drawAnimals(screen)
        self.drawJeep(screen)
        self.drawRangers(screen)
        self.drawPoachers(screen)
        self.drawRoads(screen)

    # Finally, apply a day/night overlay if needed
        day_tint = (255, 255, 255, 0)  # invisible
        night_tint = (0, 0, 70, 160)   # bluish color with alpha
        if self.dayNightOverlayOpacity > 0:
            tint_color = BoardGUI.lerp_color(day_tint, night_tint, self.dayNightOverlayOpacity)
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill(tint_color)
            screen.blit(overlay, (0, 0))


    def drawFields(self, screen: Surface) -> None:
        """
        Renders each field with terrainTextures["default"].
        Then draws black grid lines.
        """
        for y in range(self.board.height):
            for x in range(self.board.width):
                tile_rect = (x * self.tileW, y * self.tileH)
                screen.blit(self.terrainTextures["default"], tile_rect)

        # Draw grid lines in black
        for x in range(self.board.width + 1):
            pygame.draw.line(
                screen, (0, 0, 0),
                (x * self.tileW, 0),
                (x * self.tileW, self.board.height * self.tileH),
                1
            )
        for y in range(self.board.height + 1):
            pygame.draw.line(
                screen, (0, 0, 0),
                (0, y * self.tileH),
                (self.board.width * self.tileW, y * self.tileH),
                1
            )

    def drawOuterBox(self, screen: Surface, border_color=(0, 0, 0), border_thickness=2) -> None:
        """
        Draws a rectangular border around the entire board area.
        """
        board_width_px = self.board.width * self.tileW
        board_height_px = self.board.height * self.tileH
        pygame.draw.rect(
            screen,
            border_color,
            (0, 0, board_width_px, board_height_px),
            border_thickness
        )

    def drawPonds(self, screen: Surface) -> None:
        """
        Renders each pond in board.ponds using self.pondSprite.
        """
        for pond in self.board.ponds:
            loc = getattr(pond, 'location', Vector2(0, 0))
            x = int(loc.x * self.tileW)
            y = int(loc.y * self.tileH)
            screen.blit(self.pondSprite, (x, y))

    def drawPlants(self, screen: Surface) -> None:
        """
        Draws each plant as a cactus sprite.
        Positions the cactus so its base sits at the tile bottom.
        """
        for plant in self.board.plants:
            loc = getattr(plant, 'location', Vector2(0, 0))
            x = int(loc.x * self.tileW)
            # shift the sprite up so the bottom aligns with the tile
            y = int(loc.y * self.tileH - (self.cactusSprite.get_height() - self.tileH))
            screen.blit(self.cactusSprite, (x, y))

    def drawAnimals(self, screen: Surface) -> None:
        """
        Placeholder for any animals
        """
        pass

    def drawJeep(self, screen: Surface) -> None:
        for jeep in self.board.jeeps:
            loc = getattr(jeep, 'location', Vector2(0, 0))
            x = int(loc.x * self.tileW)
            y = int(loc.y * self.tileH)
            screen.blit(self.jeepSprite, (x, y))

    def drawRangers(self, screen: Surface) -> None:
        for ranger in self.board.rangers:
            loc = getattr(ranger, 'position', Vector2(0, 0))
            x = int(loc.x * self.tileW)
            y = int(loc.y * self.tileH)
            screen.blit(self.rangerSprite, (x, y))

    def drawPoachers(self, screen: Surface) -> None:
        for poacher in self.board.poachers:
            loc = getattr(poacher, 'position', Vector2(0, 0))
            x = int(loc.x * self.tileW)
            y = int(loc.y * self.tileH)
            screen.blit(self.poacherSprite, (x, y))

    def drawRoads(self, screen: Surface) -> None:
        """
        Draws roads (if any) as gray lines connecting their points.
        """
        for road in self.board.roads:
            if len(road.points) < 2:
                continue
            points = []
            for p in road.points:
                px = int(p.x * self.tileW + self.tileW // 2)
                py = int(p.y * self.tileH + self.tileH // 2)
                points.append((px, py))
            pygame.draw.lines(screen, (105, 105, 105), False, points, 4)

    def setDayNightOverlayOpacity(self, opacity: float) -> None:
        """
        Clamps opacity to [0..1].
        """
        self.dayNightOverlayOpacity = max(0.0, min(1.0, opacity))

    def toggleIsometricMode(self) -> None:
        self.isometricMode = not self.isometricMode

    def getCameraPosition(self) -> Tuple[float, float]:
        return (self.cameraX, self.cameraY)

    def setCameraPosition(self, x: float, y: float) -> None:
        self.cameraX = x
        self.cameraY = y

    def handleResize(self, newWidth: int, newHeight: int) -> None:
        """
        Re-create the display if needed, or adapt tile sizes.
        """
        self.screen = pygame.display.set_mode((newWidth, newHeight))

    # ------------------------------------------------------------------
    # Day/Night Cycle 
    # ------------------------------------------------------------------
    def updateDayNightCycle(self, delta_time: float) -> None:
        """
        a cycle of 5 minutes day, 3 minutes night, with transitions.
        dayNightOverlayOpacity goes from 0..1 for transitions.
        """
        if not self.dayNightCycleEnabled:
            return

        self.dayNightTimer += delta_time
        if self.dayNightTimer > self.totalCycleTime:
            self.dayNightTimer -= self.totalCycleTime

        # 5 min day (0..300s), 3 min night (300..480s)
        t = self.dayNightTimer
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