import pygame
from my_safari_project.model.board import Board
from my_safari_project.view.boardgui import BoardGUI
from my_safari_project.model.plant import Plant
from my_safari_project.model.pond import Pond
from pygame.math import Vector2

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Safari")

    board = Board(10, 8)
    board.initializeBoard()

    # Add sample plants and ponds
    #board.plants.append(Plant(1, Vector2(3, 2), "Cactus", 0, 0, 0, False))
    #board.ponds.append(Pond(1, Vector2(5, 4), "Waterhole", 100, 10, 500, 2))

    gui = BoardGUI(board, 64, 64, False)
    gui.loadAssets()

    clock = pygame.time.Clock()
    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update day/night
        gui.updateDayNightCycle(delta_time)
        # Render
        gui.render(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
