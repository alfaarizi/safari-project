from __future__ import annotations
import random
import sys
from typing import Dict, List

import pygame
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.control.game_controller import DifficultyLevel
from my_safari_project.model.timer import Timer

from my_safari_project.view.boardgui import BoardGUI

SCREEN_W, SCREEN_H = 1080, 720
SIDE_PANEL_W = 320
TOP_BAR_H = 60
BOTTOM_BAR_H = 80

BOARD_RECT = pygame.Rect(
    0,
    TOP_BAR_H,
    SCREEN_W - SIDE_PANEL_W,
    SCREEN_H - TOP_BAR_H - BOTTOM_BAR_H
)

POACHER_INTERVAL = 20.0        # seconds between automatic spawns
MAX_POACHERS     = 6

# How many real‐seconds equal one in‐game day
GAME_SECONDS_PER_DAY = 5.0


class GameGUI:
    def __init__(self, difficulty: DifficultyLevel):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        # Difficulty
        self.difficulty = difficulty

        # MODEL --------------------------------------------------------------
        if difficulty == DifficultyLevel.EASY:
            init_balance = 1500.0
            self._poacher_interval = 30.0
            self._max_poachers = 4
        elif difficulty == DifficultyLevel.NORMAL:
            init_balance = 1000.0
            self._poacher_interval = 20.0
            self._max_poachers = 6
        else:  # HARD
            init_balance = 500.0
            self._poacher_interval = 10.0
            self._max_poachers = 8

        self.board   = Board(25, 25)
        self.capital = Capital(init_balance)

        # Timer (for day/night cycle)
        self.timer = Timer()

        # track real‐time to map into game days
        self.elapsed_real_seconds = 0.0

        # VIEW ---------------------------------------------------------------
        self.board_gui = BoardGUI(self.board)

        # UI state
        self.font_small  = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large  = pygame.font.SysFont("Verdana", 28, bold=True)

        self.running        = True
        self.feedback: str  = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0

        # shop definitions
        self.shop_items: List[Dict] = [
            {"name": "Ranger", "cost": 150},
            {"name": "Plant",  "cost": 20},
            {"name": "Pond",   "cost": 200},
        ]
        self.item_rects: List[pygame.Rect] = []
        self.hover_item = -1

        # timers
        self.timer = Timer()
        self._poacher_timer = 0.0

        # seed one ranger
        self._spawn_ranger()

    # ------------------------------------------------------------------ main
    def run(self):
        while self.running:
            raw_dt = self.timer.tick()
            dt = min(raw_dt, 0.02)

            # accumulate real seconds
            self.elapsed_real_seconds += dt

            self._handle_events()
            self._update_sim(dt)
            self._draw()

        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------ event loop
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

    # ------------------------------------------------------------- buy logic
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

    # ----------------------------------------------------------- world spawn
    def _random_tile(self) -> Vector2:
        return Vector2(
            random.randint(0, self.board.width - 1),
            random.randint(0, self.board.height - 1)
        )

    def _spawn_ranger(self):
        rid = len(self.board.rangers) + 1
        ranger = Ranger(
            rid,
            f"R{rid}",
            salary=50,
            position=self._random_tile()
        )
        self.board.rangers.append(ranger)

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

    # ------------------------------------------------------------------ tick
    def _update_sim(self, dt: float):
        # update day/night cycle
        self.timer.updateTime(dt)
        self.board_gui.update_day_night(dt)

        # auto‑spawn poachers
        if len(self.board.poachers) < self._max_poachers:
            self._poacher_timer += dt
            if self._poacher_timer >= self._poacher_interval:
                self._poacher_timer = 0.0
                self._spawn_poacher()

        # update poachers
        for p in self.board.poachers:
            p.update(dt, (self.board.width, self.board.height))

        # rangers AI
        for r in self.board.rangers:
            visible = [p for p in self.board.poachers if p.is_visible_to(r)]
            if visible:
                target = min(visible, key=lambda p: r.position.distance_to(p.position))
                r.chase_poacher(target)
                if r.eliminate_poacher(target):
                    self.capital.addFunds(50)
            else:
                r.patrol(self.board.width, self.board.height)

        # feedback fade
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
            self.feedback       = ""

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill((40, 45, 50))

        # board area
        board_rect = pygame.Rect(
            0, TOP_BAR_H,
            SCREEN_W - SIDE_PANEL_W,
            SCREEN_H - TOP_BAR_H
        )
        self.board_gui.render(self.screen, board_rect)

        # UI panels
        self._draw_top_bar()
        self._draw_bottom_bar()
        self._draw_side_panel()
        self._draw_feedback()

        pygame.display.flip()

    # ---------- UI draw helpers --------------------------------------
    def _draw_top_bar(self):
        margin, box_h, radius = 10, 30, 8
        default_options = {
            "from_right": False,
            "background_color": (60, 60, 232)
        }
        def draw_box(text_str, x_pos, options=None):
            options = {**default_options, **(options or {})}

            text = self.font_medium.render(text_str, True, (255, 255, 255))
            box_w = text.get_size()[0] + 20
            rect_x = (SCREEN_W - x_pos - box_w) if options["from_right"] else x_pos
            rect = pygame.Rect(rect_x, (TOP_BAR_H - box_h) // 2, box_w, box_h)
            # draw fill and border
            pygame.draw.rect(self.screen, options["background_color"], rect, border_radius=radius)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=radius)
            # draw text
            self.screen.blit(text, (rect_x + 10, rect.y + (box_h - text.get_height()) // 2))
            return box_w
        
        # draw the labels
        pygame.draw.rect(self.screen,(60,70,90),(0,0,SCREEN_W,TOP_BAR_H))

        x_pos = margin
        for label in [
            f"Tourists: {len(self.board.tourists)}",
            f"Animals: {len(self.board.animals)}",
        ]:
            width = draw_box(label, x_pos)
            x_pos += width + margin

        draw_box(f"Capital: ${self.capital.getBalance():.0f}", margin, {
            "from_right": True,
            "background_color": (0, 100, 0)
        })

    def _draw_bottom_bar(self):
        margin, oval_h = 20, 50
        def draw_oval(text_str, x_pos):
            text = self.font_medium.render(text_str, True, (255, 255, 255))
            oval_w = text.get_width() + 40
            rect = pygame.Rect(x_pos, (
                SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - oval_h) // 2
            ), oval_w, oval_h)
            # draw box
            pygame.draw.ellipse(self.screen, (40, 45, 60), rect)
            pygame.draw.ellipse(self.screen, (255, 255, 255), rect, 2)
            # draw fill
            self.screen.blit(text,(
                rect.x + (rect.width - text.get_width()) // 2,
                rect.y + (rect.height - text.get_height()) // 2
            ))
            return oval_w

        pygame.draw.rect(self.screen, (60, 70, 90), 
                        (0, SCREEN_H - BOTTOM_BAR_H, SCREEN_W - SIDE_PANEL_W, BOTTOM_BAR_H))

        # get time data
        date, time_str = self.timer.get_date_time()
        game_time = self.timer.get_game_time()
        
        x_pos = margin
        for time_unit, time in list(game_time.items())[:4]:
            width = draw_oval(f"{time_unit}: {time}", x_pos)
            x_pos += width + margin

        # draw date/time boxes
        box_y = (SCREEN_H - BOTTOM_BAR_H) + (BOTTOM_BAR_H - 30 * 2 - 4) // 2
        box_x = SCREEN_W - SIDE_PANEL_W - 120 - 20
        for i, (text, y_offset) in enumerate([(date, 0), (time_str, 34)]):
            rect = pygame.Rect(box_x, box_y + y_offset, 120, 30)
            pygame.draw.rect(self.screen, (153,101,21), rect, border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=4)
            text_surf = self.font_medium.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (
                rect.x + (rect.width - text_surf.get_width()) // 2,
                rect.y + (rect.height - text_surf.get_height()) // 2
            ))

    def _draw_side_panel(self):
        px, py = SCREEN_W - SIDE_PANEL_W, TOP_BAR_H
        pygame.draw.rect(self.screen, (70, 80, 100), (px, py, SIDE_PANEL_W, SCREEN_H - py))
        title = self.font_medium.render("Shop", True, (255, 255, 255))
        self.screen.blit(title, (px + 20, py + 10))

        self.item_rects.clear()
        y = py + 50
        for i, item in enumerate(self.shop_items):
            rect = pygame.Rect(px + 20, y, SIDE_PANEL_W - 40, 36)
            self.item_rects.append(rect)
            color = (80, 110, 160) if i == self.hover_item else (90, 100, 120)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            txt = self.font_small.render(f"{item['name']}: ${item['cost']}", True, (255, 255, 255))
            self.screen.blit(txt, (rect.x + 8, rect.y + 6))
            y += 44

    def _draw_feedback(self):
        if self.feedback_alpha<=0: return
        surf = self.font_medium.render(self.feedback,True,(128,0,0))
        surf.set_alpha(self.feedback_alpha)
        x = (SCREEN_W-surf.get_width())//2
        y = SCREEN_H - BOTTOM_BAR_H - surf.get_height() - 20
        self.screen.blit(surf,(x,y))

    def _show_feedback(self, msg: str):
        self.feedback       = msg
        self.feedback_timer = 2.0
        self.feedback_alpha = 255


if __name__ == "__main__":
    GameGUI(DifficultyLevel.NORMAL).run()
