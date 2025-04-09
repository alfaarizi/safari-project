"""
GameGUI.py

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
from my_safari_project.control.gamecontroller import GameController, DifficultyLevel, GameState, DayPhase
from my_safari_project.model.board import Board
from my_safari_project.view.boardgui import BoardGUI


class GameGUI:
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
        # UI layout
        self.top_bar_height = 60
        self.side_panel_width = 320
        self.background_color = (40, 45, 50)  # A dark background

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.display.set_caption("Safari - GameGUI Demo")
        
        # GameController instance
        self.game_controller = GameController(25, 25, 1000, DifficultyLevel.LEVELS[0])

        # Frame timing
        # self.game_controller.timer.clock

        # Create board instance
        self.board = Board(20, 15)  # Adjust size as needed

        # Modified in __init__
        self.board_gui = BoardGUI(self.board)
        # self.board_gui.init_gui(self.screen_width - self.side_panel_width, self.screen_height - self.top_bar_height)

        # Fonts
        self.font_small = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large = pygame.font.SysFont("Verdana", 28, bold=True)

        # Basic data placeholders
        self.capital = 1000
        self.game_state = GameState.RUNNING
        self.difficulty_index = 0  # 0 -> Easy, 1 -> Medium, 2 -> Hard
        self.day_phase = DayPhase.DAY

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
        print(self.screen_width)
        running = True
        while running:
            delta_time = self.game_controller.timer.clock.tick(60) / 1000.0
            self.game_controller.update(delta_time)  # Update game logic

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)

            self.update_feedback_message(delta_time)
            self.screen.fill(self.background_color)

            # Draw the top bar
            self.draw_top_bar()

            # === NEW CODE: Draw the BoardGUI in the left area ===
            board_area_rect = pygame.Rect(
                0,
                self.top_bar_height,
                self.screen_width - self.side_panel_width,
                self.screen_height - self.top_bar_height
            )
            board_surface = pygame.Surface((board_area_rect.width, board_area_rect.height))
            self.board_gui.screen = board_surface
            self.board_gui.overlay = pygame.Surface((board_area_rect.width, board_area_rect.height), pygame.SRCALPHA)
            board_surface.fill(self.board_gui.colors.get('sand', (194, 178, 128)))
            self.board_gui.draw_board()  # Ensure draw_board() does NOT call pygame.display.flip()
            self.screen.blit(board_surface, board_area_rect.topleft)
            # === END NEW CODE ===

            # Draw the side shop panel
            self.draw_side_panel()

            # Draw feedback message if any
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
        self.feedback_message_alpha = 0 

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
        if not self.feedback_message or self.feedback_message_alpha <= 0:
            return

        msg_surf = self.font_medium.render(self.feedback_message, True, (255, 255, 255))
        msg_surf.set_alpha(self.feedback_message_alpha)  # Apply alpha

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

            total_time = 2.0  
            fade_in_time = 0.01 
            fade_out_time = total_time - fade_in_time 
            if self.feedback_message_timer > fade_out_time:
                # Fade-in
                self.feedback_message_alpha = int(255 * (1 - (self.feedback_message_timer - fade_out_time) / fade_in_time))
            else:
                # Fade-out
                self.feedback_message_alpha = int(255 * (self.feedback_message_timer / fade_out_time))
        else:
            self.feedback_message_alpha = 0
            self.feedback_message = ""

# -----------------------------------------------------------
# Main entry
# -----------------------------------------------------------

if __name__ == "__main__":
    controller = GameGUI()
    controller.run()