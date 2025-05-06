import pygame
from my_safari_project.model.board import Board
from my_safari_project.view.boardgui import BoardGUI
from my_safari_project.view.gamegui import BOARD_RECT

def main():
    pygame.init()
    screen = pygame.display.set_mode((1500,750))
    board = Board(6, 4)  # e.g. 6 wide, 4 tall
    board.initializeBoard()

    gui = BoardGUI(board, 64, 64, isometric=False)
    gui._load_assets()

    clock = pygame.time.Clock()
    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # board changes from 6×4 to 10×8, next call to render() uses that
        gui.update_day_night(delta_time)
        gui.render(screen, BOARD_RECT)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
