from __future__ import annotations
import random
import sys

import pygame
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher
from my_safari_project.control.game_controller import DifficultyLevel
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
    def __init__(self, difficulty: DifficultyLevel):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        # Difficulty‐based parameters
        self.difficulty = difficulty
        if difficulty == DifficultyLevel.EASY:
            init_balance      = 1500.0
            self._poacher_ivl = 30.0
            self._max_poachers = 4
        elif difficulty == DifficultyLevel.NORMAL:
            init_balance      = 1000.0
            self._poacher_ivl = 20.0
            self._max_poachers = 6
        else:
            init_balance      =  500.0
            self._poacher_ivl = 10.0
            self._max_poachers = 8

        # MODEL
        self.board   = Board(45, 40)
        self.capital = Capital(init_balance)

        # our global timer
        self.timer = Timer()
        self._poacher_timer = 0.0
        self.elapsed_real_seconds = 0.0

        # VIEW
        self.board_gui = BoardGUI(self.board)

        # UI fonts
        self.font_small  = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large  = pygame.font.SysFont("Verdana", 28, bold=True)

        # shop & feedback state
        self.running        = True
        self.feedback       = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0
        self.shop_items     = [
            {"name": "Ranger", "cost": 150},
            {"name": "Plant",  "cost":  20},
            {"name": "Pond",   "cost": 200},
            {"name": "Hyena",   "cost": 60},
            {"name": "Lion",   "cost": 150},
            {"name": "Tiger",   "cost": 180},
            {"name": "Buffalo",   "cost": 100},
            {"name": "Elephant",   "cost": 300},
            {"name": "Giraffe",   "cost": 150},
            {"name": "Hippo",   "cost": 175},
            {"name": "Zebra",   "cost": 130}
        ]
        self.item_rects = []
        self.hover_item = -1

        # start with a single ranger
        self._spawn_ranger()


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


    def _buy_item(self, index: int):
        item = self.shop_items[index]
        if self.capital.deductFunds(item["cost"]):
            if item["name"] == "Ranger":
                self._spawn_ranger()
            elif item["name"] == "Plant":
                self._spawn_plant()
            elif item["name"] == "Pond":
                self._spawn_pond()
            elif item["name"] in [
                "Hyena", "Lion", "Tiger", 
                "Buffalo", "Elephant", "Giraffe", "Hippo", "Zebra"
            ]:
                self._spawn_animal(item["name"].upper())
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

    def _spawn_animal(self, species_name):
        import random
        from my_safari_project.model.animal import AnimalSpecies
        from my_safari_project.model.carnivore import Carnivore
        from my_safari_project.model.herbivore import Herbivore
        properties = {
            # species: (class, speed, value, lifespan)
            AnimalSpecies.HYENA:    (Carnivore, 1.5, 60,  random.randint(5, 8)),
            AnimalSpecies.LION:     (Carnivore, 1.8, 150, random.randint(10, 15)),
            AnimalSpecies.TIGER:    (Carnivore, 2.0, 180, random.randint(8, 12)),
            AnimalSpecies.BUFFALO:  (Herbivore, 1.2, 100, random.randint(7, 10)),
            AnimalSpecies.ELEPHANT: (Herbivore, 0.8, 300, random.randint(18,25)),
            AnimalSpecies.GIRAFFE:  (Herbivore, 1.4, 150, random.randint(13, 18)),
            AnimalSpecies.HIPPO:    (Herbivore, 0.9, 175, random.randint(15, 22)),
            AnimalSpecies.ZEBRA:    (Herbivore, 1.7, 130, random.randint(6, 9))
        }
        species = getattr(AnimalSpecies, species_name.upper())
        animal_class, speed, value, lifespan = properties[species]
        self.board.animals.append(animal_class(
            animal_id=len(self.board.animals) + 1,
            species=species,
            position=self._random_tile(),
            speed=speed,
            value=value,
            age=0,
            lifespan=lifespan
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

    # -- Simulation Update  ---------------------------------------
    def _update_sim(self, dt: float):
        # board entities (jeeps grow / move)
        self.board.update(dt)

        # centre camera on first jeep if any
        if self.board.jeeps:
            self.board_gui.follow(self.board.jeeps[0].position)

        # day/night overlay
        self.board_gui.update_day_night(dt)

        # auto-spawn poachers
        if len(self.board.poachers) < self._max_poachers:
            self._poacher_timer += dt
            if self._poacher_timer >= self._poacher_ivl:
                self._poacher_timer = 0.0
                self._spawn_poacher()

        # move poachers & rangers
        for p in list(self.board.poachers):
            p.update(dt, self.board)
        for r in self.board.rangers:
            r.update(dt, self.board)

        # feedback fade-out
        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
            self.feedback = ""

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
            oval_w = surf.get_width() + 40
            rect = pygame.Rect(
                x_pos,
                (SCREEN_H - BOTTOM_BAR_H + (BOTTOM_BAR_H - oval_h)//2),
                oval_w, oval_h
            )
            pygame.draw.ellipse(self.screen, (40,45,60), rect)
            pygame.draw.ellipse(self.screen, (255,255,255), rect, 2)
            self.screen.blit(surf, (
                rect.x + (rect.width - surf.get_width())//2,
                rect.y + (rect.height - surf.get_height())//2
            ))
            return oval_w

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


if __name__ == "__main__":
    GameGUI(DifficultyLevel.NORMAL).run()
