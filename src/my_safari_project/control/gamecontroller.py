'''import pygame
import sys
from pygame.math import Vector2

class GameController:
    """
    A mock GameController class that displays a static GUI layout
    (a top bar and a side shop panel) without real game logic.

    In a future version, this can be connected to actual model objects
    (Board, Timer, Capital, etc.) for dynamic updates.
    """

    def __init__(self, screen_width=1024, screen_height=640):
        """
        Initializes the GameController with a fixed window size,
        UI layout positions, and placeholder data.
        """
        # Basic window dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Pygame setup
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Safari - GameController Demo")

        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()

        # Fonts for text display
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font_medium = pygame.font.SysFont("Arial", 20)
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)

        # UI Layout (mock positions)
        self.top_bar_height = 50
        self.side_panel_width = 300

        # Mock data placeholders (would be replaced by real logic or references to Model)
        self.game_state = "RUNNING"  # e.g., could be { RUNNING, PAUSED, WON, LOST }
        self.current_capital = 1000
        self.selected_difficulty = "Easy"
        self.day_night_cycle_enabled = True
        self.day_phase = "Day"  # or "Night"

        # Mock shop items
        self.shop_items = [
            {"name": "Road", "cost": 50},
            {"name": "Pond", "cost": 200},
            {"name": "Plant", "cost": 20},
            {"name": "Herbivore", "cost": 300},
            {"name": "Carnivore", "cost": 500},
            {"name": "Jeep", "cost": 400},
            {"name": "Ranger", "cost": 150},
            {"name": "Poacher Bait", "cost": 100},  # purely fictional item for demo
        ]

    def run(self):
        """
        Main loop of this mock controller.
        Handles events, draws the UI, and updates the screen.
        No real game logic is implemented here.
        """
        running = True
        while running:
            delta_time = self.clock.tick(60) / 1000.0  # Frame timing (seconds)
            # Handle events (basic placeholders)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Clear screen with a background color
            self.screen.fill((70, 180, 90))  # Some greenish tone for 'grass'

            # Draw the mock UI
            self.draw_top_bar()
            self.draw_side_panel()

            # Flip buffers to show the updated screen
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def draw_top_bar(self):
        """
        Draws a top UI bar containing:
        - Game title or state
        - Current capital
        - Selected difficulty
        - Possibly a day/night toggle placeholder
        """
        # Top bar rect
        top_bar_rect = pygame.Rect(0, 0, self.screen_width, self.top_bar_height)
        pygame.draw.rect(self.screen, (60, 60, 60), top_bar_rect)

        # Display game title/state
        title_surface = self.font_large.render("Safari Controller (Demo)", True, (255, 255, 255))
        self.screen.blit(title_surface, (10, 10))

        # Display current capital
        capital_text = f"Capital: ${self.current_capital}"
        capital_surface = self.font_medium.render(capital_text, True, (255, 255, 0))
        self.screen.blit(capital_surface, (400, 15))

        # Display difficulty
        difficulty_text = f"Difficulty: {self.selected_difficulty}"
        difficulty_surface = self.font_medium.render(difficulty_text, True, (255, 255, 255))
        self.screen.blit(difficulty_surface, (600, 15))

        # Display day/night
        daynight_text = f"Day/Night: {self.day_phase}"
        daynight_surface = self.font_medium.render(daynight_text, True, (200, 200, 255))
        self.screen.blit(daynight_surface, (800, 15))

    def draw_side_panel(self):
        """
        Draws a right-side panel for the shop and other UI controls.
        """
        x_start = self.screen_width - self.side_panel_width
        panel_rect = pygame.Rect(x_start, self.top_bar_height, self.side_panel_width, self.screen_height - self.top_bar_height)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect)

        # Title "Shop"
        shop_title_surface = self.font_large.render("Shop", True, (255, 255, 255))
        self.screen.blit(shop_title_surface, (x_start + 20, self.top_bar_height + 10))

        # Render each shop item as text (no real buttons yet)
        y_offset = self.top_bar_height + 60
        for item in self.shop_items:
            item_text = f"{item['name']}: ${item['cost']}"
            item_surface = self.font_medium.render(item_text, True, (255, 255, 255))
            self.screen.blit(item_surface, (x_start + 20, y_offset))
            y_offset += 30

        # (Optional) Additional placeholders for more controls, e.g., toggles or expansions

    def handle_mouse_click(self, pos: tuple):
        """
        Placeholder for mouse clicks on the UI.
        Currently does nothing except print the click position.
        """
        print(f"Mouse clicked at: {pos}")
        # Here you might check if pos is within the side panel
        # then detect which shop item was clicked, etc.
        # For now, it's just a placeholder.

# If you want this file to run independently, we can define a main check:
if __name__ == "__main__":
    gc = GameController()
    gc.run()'''


"""
GameController.py

Demonstration of a Pygame-based GameController class that:
- Has a top bar with clickable buttons to toggle day/night, difficulty, and game state.
- Has a side "Shop" panel where clicking items deducts from capital if affordable.
- Shows a more modern color scheme, hover highlights, and textual feedback.
- No real game logic is implemented; it's a static UI demo.

You can run this file directly:
    python GameController.py
"""

import pygame
import sys
from typing import List, Dict, Tuple

# -----------------------------------------------------------
# Enums / Simple Classes to Mimic UML or Basic Features
# -----------------------------------------------------------

class DifficultyLevel:
    """Simple utility for cycling difficulties."""
    LEVELS = ["Easy", "Medium", "Hard"]

class GameState:
    RUNNING = "Running"
    PAUSED = "Paused"

class DayPhase:
    DAY = "Day"
    NIGHT = "Night"

# -----------------------------------------------------------
# Main GameController
# -----------------------------------------------------------

class GameController:
    """
    A large GameController class that:
    - Provides a Pygame GUI with top-bar buttons and a side shop panel.
    - Toggles day/night, difficulty, and game state on click.
    - Deducts cost from capital when shop items are clicked.
    - Renders a slightly more "modern" look using color schemes and hover effects.
    """

    def __init__(self):
        """
        Initializes Pygame and sets up the UI layout, placeholders for capital,
        day/night, difficulty, game state, etc.
        """
        pygame.init()
        self.screen_width = 1080
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Safari - GameController Demo")

        # Frame timing
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_small = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large = pygame.font.SysFont("Verdana", 28, bold=True)

        # Basic data placeholders
        self.capital = 1000
        self.game_state = GameState.RUNNING
        self.difficulty_index = 0  # 0 -> Easy, 1 -> Medium, 2 -> Hard
        self.day_phase = DayPhase.DAY

        # UI layout
        self.top_bar_height = 60
        self.side_panel_width = 320
        self.background_color = (40, 45, 50)  # A dark background

        # Buttons (top bar) config
        self.button_height = 40
        self.button_width = 150
        self.button_margin = 10
        self.top_bar_buttons = []
        self.create_top_bar_buttons()

        # Shop items
        self.shop_items: List[Dict] = [
            {"name": "Road",       "cost": 50},
            {"name": "Pond",       "cost": 200},
            {"name": "Plant",      "cost": 20},
            {"name": "Herbivore",  "cost": 300},
            {"name": "Carnivore",  "cost": 500},
            {"name": "Jeep",       "cost": 400},
            {"name": "Ranger",     "cost": 150},
            {"name": "Poacher Trap","cost": 100}
        ]
        self.item_height = 40
        self.item_margin = 8
        self.shop_rects: List[pygame.Rect] = []

        # Hover / feedback messages
        self.hovered_item_index = -1
        self.feedback_message = ""         # e.g., "Not enough funds!"
        self.feedback_message_timer = 0.0  # How long to display the message (in seconds)

    # -----------------------------------------------------------
    # Setup or update UI elements
    # -----------------------------------------------------------

    def create_top_bar_buttons(self):
        """
        Create button rectangles for day/night, difficulty, game state.
        We'll store them in a list for easy click detection.
        """
        # We'll place them horizontally with some margin
        x_start = 10
        y_start = (self.top_bar_height - self.button_height) // 2

        # 1) Day/Night Toggle button
        btn_daynight = pygame.Rect(x_start, y_start, self.button_width, self.button_height)
        x_start += self.button_width + self.button_margin

        # 2) Difficulty Toggle button
        btn_diff = pygame.Rect(x_start, y_start, self.button_width, self.button_height)
        x_start += self.button_width + self.button_margin

        # 3) Game State button
        btn_gamestate = pygame.Rect(x_start, y_start, self.button_width, self.button_height)

        # Store in top_bar_buttons
        self.top_bar_buttons = [
            ("daynight", btn_daynight),
            ("difficulty", btn_diff),
            ("gamestate", btn_gamestate),
        ]

    # -----------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------

    def run(self):
        running = True
        while running:
            delta_time = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)

            # Update background, messages, etc.
            self.update_feedback_message(delta_time)

            # Clear screen
            self.screen.fill(self.background_color)

            # Draw top bar
            self.draw_top_bar()

            # Draw side shop panel
            self.draw_side_panel()

            # Draw feedback message, if any
            self.draw_feedback_message()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # -----------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------

    def handle_mouse_click(self, pos: Tuple[int, int]):
        """
        Detect if the user clicked on:
        1) One of the top bar buttons
        2) A shop item in the side panel
        """
        # 1) Check top bar buttons
        for tag, rect in self.top_bar_buttons:
            if rect.collidepoint(pos):
                self.on_top_bar_button_click(tag)
                return

        # 2) Check shop items
        for i, item_rect in enumerate(self.shop_rects):
            if item_rect.collidepoint(pos):
                self.on_shop_item_click(i)
                return

    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """
        Check if we're hovering over a shop item, so we can highlight it.
        """
        self.hovered_item_index = -1
        for i, item_rect in enumerate(self.shop_rects):
            if item_rect.collidepoint(pos):
                self.hovered_item_index = i
                break

    def on_top_bar_button_click(self, tag: str):
        """
        Called when a top bar button is clicked.
        Switch day/night, cycle difficulty, or toggle game state.
        """
        if tag == "daynight":
            self.toggle_day_night()
        elif tag == "difficulty":
            self.cycle_difficulty()
        elif tag == "gamestate":
            self.toggle_game_state()

    def on_shop_item_click(self, index: int):
        """
        When a shop item is clicked, attempt to deduct cost from capital.
        """
        item = self.shop_items[index]
        cost = item["cost"]
        if self.capital >= cost:
            self.capital -= cost
            self.feedback_message = f"Purchased {item['name']} for ${cost}"
        else:
            self.feedback_message = "Not enough funds!"
        # Display feedback message for 2 seconds
        self.feedback_message_timer = 2.0

    # -----------------------------------------------------------
    # Button / Toggle Logic
    # -----------------------------------------------------------

    def toggle_day_night(self):
        """Switch between Day and Night."""
        if self.day_phase == DayPhase.DAY:
            self.day_phase = DayPhase.NIGHT
        else:
            self.day_phase = DayPhase.DAY

    def cycle_difficulty(self):
        """Cycle among Easy -> Medium -> Hard -> Easy..."""
        self.difficulty_index = (self.difficulty_index + 1) % len(DifficultyLevel.LEVELS)

    def toggle_game_state(self):
        """Toggle Running <-> Paused."""
        if self.game_state == GameState.RUNNING:
            self.game_state = GameState.PAUSED
        else:
            self.game_state = GameState.RUNNING

    # -----------------------------------------------------------
    # Drawing / Rendering
    # -----------------------------------------------------------

    def draw_top_bar(self):
        """
        Draws a top bar with:
         - Three rectangular buttons (day/night, difficulty, game state).
         - Display of capital in the top-right corner, for example.
        """
        bar_rect = pygame.Rect(0, 0, self.screen_width, self.top_bar_height)
        pygame.draw.rect(self.screen, (60, 70, 90), bar_rect)

        # Draw the three buttons
        for tag, rect in self.top_bar_buttons:
            if tag == "daynight":
                text = f"Day/Night: {self.day_phase}"
            elif tag == "difficulty":
                diff_name = DifficultyLevel.LEVELS[self.difficulty_index]
                text = f"Difficulty: {diff_name}"
            elif tag == "gamestate":
                text = f"State: {self.game_state}"
            else:
                text = tag

            self.draw_button(rect, text)

        # Draw capital on the far right
        capital_text = f"Capital: ${self.capital:.2f}"
        text_surface = self.font_medium.render(capital_text, True, (255, 255, 255))
        text_x = self.screen_width - text_surface.get_width() - 15
        text_y = (self.top_bar_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

    def draw_button(self, rect: pygame.Rect, text: str):
        """Draws a simple button with text inside rect."""
        # Button background
        pygame.draw.rect(self.screen, (90, 100, 120), rect, border_radius=5)
        # Button text
        txt_surface = self.font_small.render(text, True, (255, 255, 255))
        txt_x = rect.x + (rect.width - txt_surface.get_width()) // 2
        txt_y = rect.y + (rect.height - txt_surface.get_height()) // 2
        self.screen.blit(txt_surface, (txt_x, txt_y))

    def draw_side_panel(self):
        """
        Draw a side panel on the right side with "Shop" items,
        each drawn as a clickable 'card' or 'row'.
        """
        x_start = self.screen_width - self.side_panel_width
        y_start = self.top_bar_height
        w = self.side_panel_width
        h = self.screen_height - self.top_bar_height

        panel_rect = pygame.Rect(x_start, y_start, w, h)
        pygame.draw.rect(self.screen, (70, 80, 100), panel_rect)

        # Title: "Shop"
        title = "Shop"
        title_surf = self.font_large.render(title, True, (255, 255, 255))
        self.screen.blit(title_surf, (x_start + 20, y_start + 10))

        # Draw each item
        self.shop_rects.clear()
        item_x = x_start + 20
        item_y = y_start + 70
        for i, item in enumerate(self.shop_items):
            item_rect = pygame.Rect(item_x, item_y, w - 40, self.item_height)
            self.shop_rects.append(item_rect)

            # Hover highlight or normal color
            if i == self.hovered_item_index:
                color_bg = (80, 110, 160)  # highlight color
            else:
                color_bg = (90, 100, 120)

            pygame.draw.rect(self.screen, color_bg, item_rect, border_radius=4)
            text = f"{item['name']}: ${item['cost']}"
            txt_surf = self.font_medium.render(text, True, (255, 255, 255))
            txt_x = item_rect.x + 8
            txt_y = item_rect.y + (self.item_height - txt_surf.get_height()) // 2
            self.screen.blit(txt_surf, (txt_x, txt_y))

            item_y += self.item_height + self.item_margin

    def draw_feedback_message(self):
        """
        If there's a feedback message (e.g. "Not enough funds!"),
        display it near the bottom center for clarity.
        """
        if not self.feedback_message:
            return

        msg_surf = self.font_medium.render(self.feedback_message, True, (255, 220, 220))
        x = (self.screen_width - msg_surf.get_width()) // 2
        y = self.screen_height - msg_surf.get_height() - 20
        self.screen.blit(msg_surf, (x, y))

    # -----------------------------------------------------------
    # Feedback / Timed Messages
    # -----------------------------------------------------------

    def update_feedback_message(self, delta_time: float):
        """
        Reduces the feedback message timer, hides it when time expires.
        """
        if self.feedback_message_timer > 0:
            self.feedback_message_timer -= delta_time
            if self.feedback_message_timer <= 0:
                self.feedback_message_timer = 0
                self.feedback_message = ""

# -----------------------------------------------------------
# Main entry
# -----------------------------------------------------------

if __name__ == "__main__":
    controller = GameController()
    controller.run()

