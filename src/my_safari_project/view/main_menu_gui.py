import pygame
import sys
import tkinter as tk
from tkinter import filedialog
from my_safari_project.view.board_gui import BoardGUI

pygame.init()
font_main = pygame.font.SysFont("Comic Sans MS", 36)
font_small = pygame.font.SysFont("Comic Sans MS", 28)

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Safari Game Menu")
clock = pygame.time.Clock()

background = pygame.image.load("assets/background.jpg")

WHITE = (255, 255, 255)
LIGHT_GREEN = (173, 255, 47)
PASTEL_YELLOW = (255, 255, 200)
PASTEL_PINK = (255, 220, 240)
BUTTON_COLOR = (255, 255, 255)
BUTTON_TEXT = (70, 70, 70)
HIGHLIGHT = (128, 200, 60)

difficulty_levels = ["Easy", "Medium", "Hard"]
selected_difficulty = 0
fullscreen = False

class Button:
    def __init__(self, text, x, y, width, height, callback):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback

    def draw(self):
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=12)
        pygame.draw.rect(screen, HIGHLIGHT, self.rect, 2, border_radius=12)
        text_surf = font_main.render(self.text, True, BUTTON_TEXT)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_difficulty_selector():
    global WIDTH, HEIGHT
    label = font_main.render("Difficulty:", True, BUTTON_TEXT)
    screen.blit(label, (WIDTH // 2 - 100, HEIGHT // 2 - 180))

    x_start = WIDTH // 2 - 210
    for i, level in enumerate(difficulty_levels):
        color = HIGHLIGHT if i == selected_difficulty else BUTTON_TEXT
        rect = pygame.Rect(x_start + i * 140, HEIGHT // 2 - 120, 130, 50)
        pygame.draw.rect(screen, PASTEL_YELLOW if i == selected_difficulty else PASTEL_PINK, rect, border_radius=10)
        pygame.draw.rect(screen, HIGHLIGHT, rect, 2, border_radius=10)
        text = font_small.render(level, True, color)
        screen.blit(text, text.get_rect(center=rect.center))

def handle_difficulty_click(pos):
    global selected_difficulty, WIDTH
    x_start = WIDTH // 2 - 210
    for i in range(len(difficulty_levels)):
        rect = pygame.Rect(x_start + i * 140, HEIGHT // 2 - 120, 130, 50)
        if rect.collidepoint(pos):
            selected_difficulty = i
            print("Selected difficulty:", difficulty_levels[i])

def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    WIDTH, HEIGHT = screen.get_size()

def main_menu():
    global WIDTH, HEIGHT
    btn_width, btn_height = 250, 60

    def new_game():
        difficulty = difficulty_levels[selected_difficulty]
        print(f"Starting game with difficulty: {difficulty}")
        pygame.quit()
        game = BoardGUI(difficulty)
        game.run()

    def load_game():
        root = tk.Tk()
        root.withdraw()  

        file_path = filedialog.askopenfilename(
            title="Select a saved game file",
            filetypes=[("Save Files", "*.sav *.json *.txt"), ("All Files", "*.*")]
        )

        if file_path:
            print(f"Selected save file: {file_path}")
            # TODO: Load and pass to your BoardGUI if needed
            # game = BoardGUI(difficulty="Easy", save_file=file_path)
            # game.run()
        else:
            print("No file selected.")

    def quit_game():
        pygame.quit()
        sys.exit()

    buttons = [
        Button("New Game", 0, 0, btn_width, btn_height, new_game),
        Button("Load Game", 0, 0, btn_width, btn_height, load_game),
        Button("Quit", 0, 0, btn_width, btn_height, quit_game)
    ]

    while True:
        WIDTH, HEIGHT = screen.get_size()
        bg_scaled = pygame.transform.scale(background, (WIDTH, HEIGHT))
        screen.blit(bg_scaled, (0, 0))

        btn_x = WIDTH // 2 - btn_width // 2
        start_y = HEIGHT // 2
        for i, btn in enumerate(buttons):
            btn.rect.topleft = (btn_x, start_y + i * 80)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_game()
                elif event.key == pygame.K_F11:
                    toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_difficulty_click(event.pos)
                for btn in buttons:
                    if btn.is_clicked(event.pos):
                        btn.callback()

        draw_difficulty_selector()
        for btn in buttons:
            btn.draw()

        pygame.display.flip()
        clock.tick(60)

