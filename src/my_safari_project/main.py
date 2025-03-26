import pygame

def run_game():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Safari Game")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 100, 0))  # A greenish background
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    run_game()
