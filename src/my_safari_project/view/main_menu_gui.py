import os
import sys
import tkinter as tk
from tkinter import filedialog

import pygame
from my_safari_project.control.game_controller import DifficultyLevel, GameController
from my_safari_project.view.gamegui import GameGUI
from my_safari_project.view.boardgui import BoardGUI

pygame.init()
pygame.mixer.init()

# Fonts
font_main   = pygame.font.SysFont("Comic Sans MS", 36)
font_small  = pygame.font.SysFont("Comic Sans MS", 28)
safari_font = pygame.font.Font("assets/Anton.ttf", 82)

# Colors
WHITE          = (255, 255, 255)
YELLOW         = (122, 185, 91)
PASTEL_YELLOW  = (255, 255, 200)
PASTEL_PINK    = (90, 100, 120)
BUTTON_COLOR   = (90, 100, 120)
BUTTON_TEXT    = (255, 255, 255)
HIGHLIGHT      = (128, 200, 60)
SIDEBAR_COLOR  = (50, 50, 50)

# Screen setup
WIDTH, HEIGHT = 1080, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Safari Game Menu")
clock = pygame.time.Clock()

# Load background and music
background = pygame.image.load("assets/background.jpg")
pygame.mixer.music.load("assets/menu_music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Difficulty settings
difficulty_levels    = [DifficultyLevel.EASY, DifficultyLevel.NORMAL, DifficultyLevel.HARD]
selected_difficulty  = 1  # default to Normal
fullscreen = False

def draw_background_cover(surface, img, x, y, w, h):
    orig_w, orig_h = img.get_size()
    sf = max(w/orig_w, h/orig_h)
    nw, nh = int(orig_w*sf), int(orig_h*sf)
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    ox = x + (w - nw)//2
    oy = y + (h - nh)//2
    surface.blit(scaled, (ox, oy))

def draw_safari_title(cx, cy):
    ts = safari_font.render("Safari", True, YELLOW)
    rect = ts.get_rect(center=(cx, cy+80))
    screen.blit(ts, rect)

def scale_and_draw_image(surface, img, x, y, w, h):
    orig_w, orig_h = img.get_size()
    sf = max(w/orig_w, h/orig_h)
    nw, nh = int(orig_w*sf), int(orig_h*sf)
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    ox = x + (w - nw)//2
    oy = y + (h - nh)//2
    surface.blit(scaled, (ox, oy))

class Button:
    def __init__(self, text, x, y, w, h, cb):
        self.text     = text
        self.rect     = pygame.Rect(x, y, w, h)
        self.callback = cb

    def draw(self):
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=12)
        pygame.draw.rect(screen, HIGHLIGHT, self.rect, 2, border_radius=12)
        ts = font_main.render(self.text, True, BUTTON_TEXT)
        screen.blit(ts, ts.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_difficulty_selector(left_x, top_y):
    spacing, bw, bh = 10, 110, 50
    for i, level in enumerate(difficulty_levels):
        x = left_x + i*(bw+spacing)
        rect = pygame.Rect(x, top_y, bw, bh)
        bg = PASTEL_YELLOW if i==selected_difficulty else PASTEL_PINK
        col = HIGHLIGHT    if i==selected_difficulty else BUTTON_TEXT
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, HIGHLIGHT, rect, 2, border_radius=10)
        ts = font_small.render(level.value, True, col)
        screen.blit(ts, ts.get_rect(center=rect.center))

def handle_difficulty_click(pos, left_x, top_y):
    global selected_difficulty
    spacing, bw, bh = 10, 110, 50
    for i in range(len(difficulty_levels)):
        x = left_x + i*(bw+spacing)
        if pygame.Rect(x, top_y, bw, bh).collidepoint(pos):
            selected_difficulty = i
            print("Selected difficulty:", difficulty_levels[i].value)

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

    btn_w, btn_h    = 250, 60
    margin_right    = 50
    sidebar_width   = 400

    def new_game():
        difficulty = difficulty_levels[selected_difficulty]
        print(f"Starting new game at {difficulty.value}")
        pygame.mixer.music.stop()
        pygame.quit()
        gui = GameGUI(difficulty)
        gui.run()

    def load_game():
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select save JSON",
            filetypes=[("Save JSON Files","*.json"),("All Files","*.*")]
        )
        if not file_path:
            print("No file selected.")
            return

        base, ext = os.path.splitext(file_path)
        save_base = base  # strip .json
        controller = GameController(0, 0, 0.0, difficulty_levels[selected_difficulty])
        success = controller.load_game(save_base)
        if success:
            print("Loaded save:", save_base)
            pygame.mixer.music.stop()
            pygame.quit()
            gui = GameGUI(controller)
            gui.run()
        else:
            print("Failed to load game.")

    def quit_game():
        pygame.mixer.music.stop()
        pygame.quit()
        sys.exit()

    buttons = [
        Button("New Game", 0, 0, btn_w, btn_h, new_game),
        Button("Load Game",0, 0, btn_w, btn_h, load_game),
        Button("Quit",     0, 0, btn_w, btn_h, quit_game)
    ]

    while True:
        WIDTH, HEIGHT = screen.get_size()
        avail_w = WIDTH - sidebar_width

        # Background
        draw_background_cover(screen, background, 0, 0, avail_w, HEIGHT)

        # Sidebar
        sidebar = pygame.Rect(avail_w, 0, sidebar_width, HEIGHT)
        pygame.draw.rect(screen, SIDEBAR_COLOR, sidebar)

        # Title
        draw_safari_title(avail_w//2, HEIGHT//2 - 120)
        hdr = font_main.render("Main Menu", True, WHITE)
        screen.blit(hdr, hdr.get_rect(center=(avail_w + sidebar_width//2 + 30, 60)))

        # Buttons & Difficulty
        base_x = WIDTH - btn_w - margin_right
        y0     = HEIGHT//2 - 150

        buttons[0].rect.topleft = (base_x, y0)
        buttons[0].draw()
        diff_y = y0 + btn_h + 10
        diff_x = base_x - 60
        draw_difficulty_selector(diff_x, diff_y)

        # Load & Quit
        buttons[1].rect.topleft = (base_x, diff_y + 70)
        buttons[1].draw()
        buttons[2].rect.topleft = (base_x, buttons[1].rect.bottom + 20)
        buttons[2].draw()

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                quit_game()
            elif evt.type == pygame.KEYDOWN:
                if evt.key in (pygame.K_ESCAPE,):
                    quit_game()
                elif evt.key == pygame.K_F11:
                    toggle_fullscreen()
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                handle_difficulty_click(evt.pos, diff_x, diff_y)
                for btn in buttons:
                    if btn.is_clicked(evt.pos):
                        btn.callback()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()
