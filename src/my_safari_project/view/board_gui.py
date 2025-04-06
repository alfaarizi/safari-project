import pygame
import sys

class BoardGUI:
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.running = True
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(f"Safari Game - {self.difficulty} Mode")

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            self.screen.fill((0, 100, 0))
            pygame.display.flip()

        pygame.quit()
        sys.exit()
