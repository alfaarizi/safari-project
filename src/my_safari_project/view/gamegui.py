from __future__ import annotations
import random
import sys
from typing import Dict, List, Optional
import os
import tkinter as tk
from tkinter import filedialog

import pygame
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.control.game_controller import GameController, DifficultyLevel
from my_safari_project.model.timer import Timer
from my_safari_project.view.boardgui import BoardGUI

# window & layout constants
SCREEN_W, SCREEN_H = 1080, 720
SIDE_PANEL_W    = 320
TOP_BAR_H       = 60
BOTTOM_BAR_H    = 80

# the rectangle in which we'll draw the board
BOARD_RECT = pygame.Rect(
    0,
    TOP_BAR_H,
    SCREEN_W - SIDE_PANEL_W,
    SCREEN_H - TOP_BAR_H - BOTTOM_BAR_H
)

# how fast new poachers spawn
POACHER_INTERVAL = 20.0
# maximum concurrently on board
MAX_POACHERS     = 6

# how many real seconds = one in-game day
GAME_SEC_PER_DAY = 5.0


class GameGUI:
    def __init__(self, controller_or_difficulty):
        if isinstance(controller_or_difficulty, GameController):
            self.game_controller = controller_or_difficulty
            self.board = self.game_controller.board
            self.capital = self.game_controller.capital
            self.timer = self.game_controller.timer
            self.difficulty = self.game_controller.difficulty_level
            difficulty = self.difficulty 
        else:
            difficulty = controller_or_difficulty
            self.difficulty = difficulty
            init_balance = difficulty.thresholds[3]
            self.board = Board(45, 40)
            self.capital = Capital(init_balance)
            self.timer = Timer()
            self.game_controller = GameController(
                board_width=self.board.width,
                board_height=self.board.height,
                init_balance=init_balance,
                difficulty=difficulty
            )
            self.game_controller.board = self.board
            self.game_controller.capital = self.capital
            self.game_controller.timer = self.timer

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        # Difficulty‐based parameters
        if difficulty == DifficultyLevel.EASY:
            init_balance = 1500.0
            self._poacher_ivl = 30.0
            self._max_poachers = 4
        elif difficulty == DifficultyLevel.NORMAL:
            init_balance = 1000.0
            self._poacher_ivl = 20.0
            self._max_poachers = 6
        else:
            init_balance = 500.0
            self._poacher_ivl = 10.0
            self._max_poachers = 8

        if isinstance(controller_or_difficulty, GameController):
            self.game_controller = controller_or_difficulty
            self.board = self.game_controller.board
            self.capital = self.game_controller.capital
            self.timer = self.game_controller.timer
            self.difficulty = self.game_controller.difficulty_level
        else:
            self.difficulty = controller_or_difficulty
            init_balance = self.difficulty.thresholds[3]
            self.board = Board(45, 40)
            self.capital = Capital(init_balance)
            self.timer = Timer()
            self.game_controller = GameController(
                board_width=self.board.width,
                board_height=self.board.height,
                init_balance=init_balance,
                difficulty=self.difficulty
            )

        self._poacher_timer = 0.0
        self.elapsed_real_seconds = 0.0

        # VIEW
        self.board_gui = BoardGUI(self.board)

        # UI fonts
        self.font_small = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large = pygame.font.SysFont("Verdana", 28, bold=True)

        # shop & feedback state
        self.running = True
        self.feedback = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0
        self.shop_items = [
            {"name": "Ranger", "cost": 150},
            {"name": "Plant", "cost": 20},
            {"name": "Pond", "cost": 200},
        ]
        self.item_rects = []
        self.hover_item = -1
        self.save_button_rect = None

        self.timer = Timer()
        self._poacher_timer = 0.0

        self._spawn_ranger()
    # ------------------------------------------------------------------ main
    def run(self):
        while self.running:
            raw_dt = self.timer.tick()
            dt = min(raw_dt, 0.02)

    def run(self):
        """Main loop."""
        while self.running:
            # tick() both returns the real‐dt and internally advances game‐time
            raw_dt = self.timer.tick()
            dt     = min(raw_dt, 0.02)  # clamp to avoid large jumps

            # accumulate real seconds if you need them
            self.elapsed_real_seconds += dt

            self._handle_events()
            self._update_sim(dt)
            self._draw()

        pygame.quit()
        sys.exit()


    # ————————————————————————————————————————————————————————————————————— Event Handling

    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.MOUSEMOTION:
                self.hover_item = -1
                for i, r in enumerate(self.item_rects):
                    if r.collidepoint(ev.pos):
                        self.hover_item = i
                        break
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(self.item_rects):
                    if r.collidepoint(ev.pos):
                        self._buy_item(i)
                        break
                # Check if save button was clicked
                if hasattr(self, 'save_button_rect') and self.save_button_rect.collidepoint(ev.pos):
                    self._handle_save_game()
        


    def _buy_item(self, index: int):
        item = self.shop_items[index]
        if self.capital.deductFunds(item["cost"]):
            if item["name"] == "Ranger":
                self._spawn_ranger()
            elif item["name"] == "Plant":
                self._spawn_plant()
            elif item["name"] == "Pond":
                self._spawn_pond()
            self._show_feedback(f"Purchased {item['name']} for ${item['cost']}")
        else:
            self._show_feedback("Insufficient funds!")


    # ————————————————————————————————————————————————————————————————————— Spawning

    def _random_tile(self) -> Vector2:
        return Vector2(
            random.randint(0, self.board.width  - 1),
            random.randint(0, self.board.height - 1)
        )

    def _spawn_ranger(self):
        rid = len(self.board.rangers) + 1
        r = Ranger(
            rid,
            f"R{rid}",
            salary=50,
            position=self._random_tile()
        )
        self.board.rangers.append(r)

    def _spawn_poacher(self):
        pid = len(self.board.poachers) + 1
        p = Poacher(pid, f"P{pid}", position=self._random_tile())
        self.board.poachers.append(p)

    def _spawn_plant(self):
        from my_safari_project.model.plant import Plant
        pid = len(self.board.plants) + 1
        self.board.plants.append(Plant(
            pid,
            self._random_tile(),
            "Bush", 20, 0.0, 1, True
        ))

    def _spawn_pond(self):
        from my_safari_project.model.pond import Pond
        pid = len(self.board.ponds) + 1
        self.board.ponds.append(Pond(
            pid,
            self._random_tile(),
            "Pond", 0, 0, 0, 0
        ))


    # ————————————————————————————————————————————————————————————————————— Simulation Update

    def _update_sim(self, dt: float):
        self.board.update(dt)

        if self.board.jeeps:
            self.board_gui.follow(self.board.jeeps[0].position)
        self.board_gui.update_day_night(dt)

        # automatically spawn new poachers up to the limit
        if len(self.board.poachers) < self._max_poachers:
            self._poacher_timer += dt
            if self._poacher_timer >= self._poacher_ivl:
                self._poacher_timer = 0.0
                self._spawn_poacher()

        # move each poacher
        for p in self.board.poachers:
            p.update(dt, (self.board.width, self.board.height))

        # simple ranger AI: chase + eliminate
        for r in self.board.rangers:
            visible = [p for p in self.board.poachers if p.is_visible_to(r)]
            if visible:
                target = min(visible, key=lambda p: r.position.distance_to(p.position))
                r.chase_poacher(target)
                if r.eliminate_poacher(target):
                    self.capital.addFunds(50)
            else:
                r.patrol(self.board.width, self.board.height)

        if self.board.jeeps:
            self.board_gui.follow(self.board.jeeps[0].position)

        # fade out any feedback message
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
            self.feedback       = ""


    # ————————————————————————————————————————————————————————————————————— Rendering

    def _draw(self):
        # background
        self.screen.fill((40, 45, 50))

        # board area
        self.board_gui.render(self.screen, BOARD_RECT)

        # UI panels
        self._draw_top_bar()
        self._draw_bottom_bar()
        self._draw_side_panel()
        self._draw_feedback()

        pygame.display.flip()


    def _draw_top_bar(self):
        margin, box_h, radius = 10, 30, 8
        default_opts = {"from_right": False, "background_color": (60, 60, 232)}

        def draw_box(txt, x_pos, opts=None):
            opts = {**default_opts, **(opts or {})}
            surf = self.font_medium.render(txt, True, (255, 255, 255))
            box_w = surf.get_width() + 20
            rect_x = (SCREEN_W - x_pos - box_w) if opts["from_right"] else x_pos
            rect = pygame.Rect(rect_x, (TOP_BAR_H - box_h)//2, box_w, box_h)
            pygame.draw.rect(self.screen, opts["background_color"], rect, border_radius=radius)
            pygame.draw.rect(self.screen, (255,255,255), rect, 2, border_radius=radius)
            self.screen.blit(surf, (rect_x + 10, rect.y + (box_h - surf.get_height())//2))
            return box_w

        # fill bar
        pygame.draw.rect(self.screen, (60,70,90), (0,0,SCREEN_W, TOP_BAR_H))
        # show tourist & animal counts
        x = margin
        for label in [f"Tourists: {len(self.board.tourists)}",
                      f"Animals:   {len(self.board.animals)}"]:
            w = draw_box(label, x)
            x += w + margin

        # capital on right
        draw_box(f"Capital: ${self.capital.getBalance():.0f}", margin, {
            "from_right": True, "background_color": (0,100,0)
        })


    def _draw_bottom_bar(self):
        margin, oval_h = 20, 50
        def draw_oval(txt, x_pos):
            surf = self.font_medium.render(txt, True, (255,255,255))
            o_w = surf.get_width() + 40
            rect = pygame.Rect(
                x_pos,
                (SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - oval_h)//2),
                o_w, oval_h
            )
            pygame.draw.ellipse(self.screen, (40,45,60), rect)
            pygame.draw.ellipse(self.screen, (255,255,255), rect, 2)
            self.screen.blit(surf, (
                rect.x + (rect.width - surf.get_width())//2,
                rect.y + (rect.height - surf.get_height())//2
            ))
            return o_w

        # fill
        pygame.draw.rect(self.screen, (60,70,90),
                         (0, SCREEN_H - BOTTOM_BAR_H,
                          SCREEN_W - SIDE_PANEL_W,
                          BOTTOM_BAR_H))

        # get date/time from timer
        date, time_str = self.timer.get_date_time()
        game_time      = self.timer.get_game_time()

        x = margin
        for unit, val in list(game_time.items())[:4]:
            w = draw_oval(f"{unit}: {val}", x)
            x += w + margin

        # draw date/time boxes on the far right
        box_y = (SCREEN_H - BOTTOM_BAR_H) + (BOTTOM_BAR_H - 64)//2
        box_x = SCREEN_W - SIDE_PANEL_W - 140
        for i, txt in enumerate((date, time_str)):
            rect = pygame.Rect(box_x, box_y + i*34, 120, 30)
            pygame.draw.rect(self.screen, (153,101,21), rect, border_radius=4)
            pygame.draw.rect(self.screen, (255,255,255), rect, 2, border_radius=4)
            surf = self.font_medium.render(txt, True, (255,255,255))
            self.screen.blit(surf, (
                rect.x + (rect.width - surf.get_width())//2,
                rect.y + (rect.height - surf.get_height())//2
            ))


    def _draw_side_panel(self):
        px, py = SCREEN_W - SIDE_PANEL_W, TOP_BAR_H
        pygame.draw.rect(self.screen, (70,80,100),
                         (px, py, SIDE_PANEL_W, SCREEN_H - py))
        title = self.font_medium.render("Shop", True, (255,255,255))
        self.screen.blit(title, (px + 20, py + 10))

        self.item_rects.clear()
        y = py + 50
        for i, item in enumerate(self.shop_items):
            rect = pygame.Rect(px + 20, y, SIDE_PANEL_W - 40, 36)
            self.item_rects.append(rect)
            col = (80,110,160) if i == self.hover_item else (90,100,120)
            pygame.draw.rect(self.screen, col, rect, border_radius=4)
            txt = self.font_small.render(f"{item['name']}: ${item['cost']}", True, (255,255,255))
            self.screen.blit(txt, (rect.x + 8, rect.y + 6))
            y += 44
        
        # Add Save Game button at the bottom of the side panel
        save_button_height = 50
        save_button_rect = pygame.Rect(
            px + 20, 
            SCREEN_H - save_button_height - 20,  # Position at bottom with margin
            SIDE_PANEL_W - 40, 
            save_button_height
        )
        
        # Check if mouse is hovering over save button
        mouse_pos = pygame.mouse.get_pos()
        save_button_hover = save_button_rect.collidepoint(mouse_pos)
        
        # Draw save button with hover effect
        button_color = (0, 120, 50) if save_button_hover else (0, 100, 40)
        pygame.draw.rect(self.screen, button_color, save_button_rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), save_button_rect, 2, border_radius=6)
        
        # Save button text
        save_text = self.font_medium.render("Save Game", True, (255, 255, 255))
        self.screen.blit(save_text, (
            save_button_rect.x + (save_button_rect.width - save_text.get_width()) // 2,
            save_button_rect.y + (save_button_rect.height - save_text.get_height()) // 2
        ))
        
        # Store the save button rect for click detection
        self.save_button_rect = save_button_rect


    def _draw_feedback(self):
        if self.feedback_alpha <= 0:
            return
        surf = self.font_medium.render(self.feedback, True, (128,0,0))
        surf.set_alpha(self.feedback_alpha)
        x = (SCREEN_W - surf.get_width()) // 2
        y = SCREEN_H - BOTTOM_BAR_H - surf.get_height() - 20
        self.screen.blit(surf, (x,y))


    def _show_feedback(self, msg: str):
        self.feedback       = msg
        self.feedback_timer = 2.0
        self.feedback_alpha = 255

    def _open_save_dialog(self) -> Optional[str]:
        """Open a file dialog and return the selected save path or None if canceled"""
        # Hide pygame window temporarily
        pygame.display.iconify()
        
        # Create root tkinter window and hide it
        root = tk.Tk()
        root.withdraw()
        
        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Game",
            defaultextension=".sav",
            filetypes=[("Safari Save Files", "*.sav"), ("All Files", "*.*")],
            initialdir=os.path.expanduser("~"),  # Start in user's home directory
        )
        
        # Clean up tkinter
        root.destroy()
        
        # Restore pygame window
        pygame.display.update()
        
        # Remove file extension as our save function will add its own extensions
        if file_path:
            base_path, _ = os.path.splitext(file_path)
            return base_path
        
        return None
    

    def _handle_save_game(self):
        """Handle save game button click by opening file dialog and saving game"""
        # Pause updates while dialog is open
        paused_state = self.running
        self.running = True  # Keep the loop running to prevent freezing

        # Hide pygame window and open dialog
        pygame.display.iconify()
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            title="Save Game",
            defaultextension=".sav",
            filetypes=[("Safari Save Files", "*.sav"), ("All Files", "*.*")],
            initialdir=os.path.expanduser("~"),
        )
        root.destroy()
        pygame.display.update()

        # Resume updates
        self.running = paused_state

        if file_path:
            base_path, _ = os.path.splitext(file_path)
            success = self.game_controller.save_game(base_path)
            if success:
                self._show_feedback(f"Game saved to: {os.path.basename(base_path)}")
            else:
                self._show_feedback("Failed to save game!")


if __name__ == "__main__":
    GameGUI(DifficultyLevel.NORMAL).run()
