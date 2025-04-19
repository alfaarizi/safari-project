import pygame
import sys
import tkinter as tk
from tkinter import filedialog
from my_safari_project.view.boardgui import BoardGUI
from my_safari_project.control.game_controller import GameController
from my_safari_project.view.gamegui import GameGUI

# Initialize Pygame modules
pygame.init()
pygame.mixer.init()

font_main = pygame.font.SysFont("Comic Sans MS", 36)
font_small = pygame.font.SysFont("Comic Sans MS", 28)

# Set screen dimensions to 1080x720
WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Safari Game Menu")
clock = pygame.time.Clock()

# Load background and music
background = pygame.image.load("assets/background.jpg")
pygame.mixer.music.load("assets/menu_music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Colors
WHITE = (255, 255, 255)
LIGHT_GREEN = (173, 255, 47)
PASTEL_YELLOW = (255, 255, 200)
PASTEL_PINK = (90, 100, 120)
BUTTON_COLOR = (90, 100, 120)
BUTTON_TEXT = (255, 255, 255)
HIGHLIGHT = (128, 200, 60)
SIDEBAR_COLOR = (50, 50, 50)  # Solid sidebar background

# Difficulty settings
difficulty_levels = ["Easy", "Normal", "Hard"]
selected_difficulty = 0
fullscreen = False

def draw_background_cover(surface, image, x, y, w, h):
    """
    Scales and draws 'image' to fill the rectangle (x, y, w, h) completely,
    preserving aspect ratio and cropping as needed (cover approach).
    """
    orig_width, orig_height = image.get_size()
    # Determine the scaling factor to fully cover the area without black bars
    scale_factor = max(w / orig_width, h / orig_height)
    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)

    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    # Center the scaled image within the target rectangle
    offset_x = x + (w - new_width) // 2
    offset_y = y + (h - new_height) // 2

    surface.blit(scaled_image, (offset_x, offset_y))

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

def draw_difficulty_selector(left_x, top_y):
    spacing = 10
    button_width = 110
    button_height = 50
    for i, level in enumerate(difficulty_levels):
        x = left_x + i * (button_width + spacing)
        rect = pygame.Rect(x, top_y, button_width, button_height)
        color = HIGHLIGHT if i == selected_difficulty else BUTTON_TEXT
        bg_color = PASTEL_YELLOW if i == selected_difficulty else PASTEL_PINK
        pygame.draw.rect(screen, bg_color, rect, border_radius=10)
        pygame.draw.rect(screen, HIGHLIGHT, rect, 2, border_radius=10)
        text = font_small.render(level, True, color)
        screen.blit(text, text.get_rect(center=rect.center))

def handle_difficulty_click(pos, left_x, top_y):
    global selected_difficulty
    spacing = 10
    button_width = 110
    button_height = 50
    for i in range(len(difficulty_levels)):
        x = left_x + i * (button_width + spacing)
        rect = pygame.Rect(x, top_y, button_width, button_height)
        if rect.collidepoint(pos):
            selected_difficulty = i
            print("Selected difficulty:", difficulty_levels[i])

def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
    WIDTH, HEIGHT = screen.get_size()

def main_menu():
    global WIDTH, HEIGHT
    btn_width, btn_height = 250, 60
    margin_right = 50
    sidebar_width = 400

    def new_game():
        difficulty = difficulty_levels[selected_difficulty]
        print(f"Starting game with difficulty: {difficulty}")
        width, height = screen.get_size()
        pygame.mixer.music.stop()
        pygame.quit()
        game_gui = GameGUI()
        game_gui.run()

    def load_game():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select a saved game file",
            filetypes=[("Save Files", "*.sav *.json *.txt"), ("All Files", "*.*")]
        )
        if file_path:
            print(f"Selected save file: {file_path}")
        else:
            print("No file selected.")

    def quit_game():
        pygame.mixer.music.stop()
        pygame.quit()
        sys.exit()

    buttons = [
        Button("New Game", 0, 0, btn_width, btn_height, new_game),
        Button("Load Game", 0, 0, btn_width, btn_height, load_game),
        Button("Quit", 0, 0, btn_width, btn_height, quit_game)
    ]

    while True:
        WIDTH, HEIGHT = screen.get_size()

        # Determine space for background (left portion) and draw it
        available_width = WIDTH - sidebar_width
        available_height = HEIGHT

        # Fill that left area with the background (cover approach)
        draw_background_cover(screen, background, 0, 0, available_width, available_height)

        # Draw sidebar on the right
        sidebar_rect = pygame.Rect(WIDTH - sidebar_width, 0, sidebar_width, HEIGHT)
        pygame.draw.rect(screen, SIDEBAR_COLOR, sidebar_rect)

        # Position buttons within the sidebar
        base_x = WIDTH - btn_width - margin_right
        start_y = HEIGHT // 2 - 150

        # "New Game" + difficulty
        buttons[0].rect.topleft = (base_x, start_y)
        buttons[0].draw()
        difficulty_y = buttons[0].rect.bottom + 10
        difficulty_x = base_x - 60
        draw_difficulty_selector(difficulty_x, difficulty_y)

        # "Load Game"
        buttons[1].rect.topleft = (base_x, difficulty_y + 70)
        buttons[1].draw()

        # "Quit"
        buttons[2].rect.topleft = (base_x, buttons[1].rect.bottom + 20)
        buttons[2].draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_game()
                elif event.key == pygame.K_F11:
                    toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_difficulty_click(event.pos, difficulty_x, difficulty_y)
                for btn in buttons:
                    if btn.is_clicked(event.pos):
                        btn.callback()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()

