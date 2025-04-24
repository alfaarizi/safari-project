from __future__ import annotations
import sys
import pygame

from my_safari_project.view.boardgui import BoardGUI
from my_safari_project.control.game_controller import (
    GameController,
    RANGER_COST, PLANT_COST, POND_COST,
    HYENA_COST, LION_COST, TIGER_COST,
    BUFFALO_COST, ELEPHANT_COST, GIRAFFE_COST, HIPPO_COST, ZEBRA_COST
)

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

class GameGUI:

    def __init__(self, control: GameController):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        # Global Control
        self.control: GameController = control

        # View
        self.board_gui = BoardGUI(self.control.board)

        # UI fonts
        self.font_small  = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large  = pygame.font.SysFont("Verdana", 28, bold=True)

        # shop & feedback state
        self.feedback       = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0
        self.shop_items     = [
            {"name": "Ranger",      "cost": RANGER_COST},
            {"name": "Plant",       "cost": PLANT_COST},
            {"name": "Pond",        "cost": POND_COST},
            {"name": "Hyena",       "cost": HYENA_COST},
            {"name": "Lion",        "cost": LION_COST},
            {"name": "Tiger",       "cost": TIGER_COST},
            {"name": "Buffalo",     "cost": BUFFALO_COST},
            {"name": "Elephant",    "cost": ELEPHANT_COST},
            {"name": "Giraffe",     "cost": GIRAFFE_COST},
            {"name": "Hippo",       "cost": HIPPO_COST},
            {"name": "Zebra",       "cost": ZEBRA_COST}
        ]
        self.item_rects = []
        self.hover_item = -1

        # start with a single ranger
        self.control.spawn_poacher()

    # ————————————————————————————————————————————————————————————————————— Event Handling

    def update(self, dt: float):
        self._update_ui(dt)
        self._handle_events()
        self._draw()
    
    def show_feedback(self, msg: str):
        self.feedback       = msg
        self.feedback_timer = 2.0
        self.feedback_alpha = 255
    
    def exit(self):
        pygame.quit()
        sys.exit()

    def _update_ui(self, dt: float):
        # centre camera on first jeep if any
        if self.control.board.jeeps:
            self.board_gui.follow(self.control.board.jeeps[0].position)

        # day/night overlay
        self.board_gui.update_day_night(dt)

        if self.feedback_timer > 0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255 * min(1.0, self.feedback_timer * 2))
        else:
            self.feedback_alpha = 0
            self.feedback = ""

    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.control.running = False
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
        if self.control.capital.deductFunds(item["cost"]):
            if item["name"] == "Ranger":
                self.control.spawn_ranger()
            elif item["name"] == "Plant":
                self.control.spawn_plant()
            elif item["name"] == "Pond":
                self.control.spawn_pond()
            elif item["name"] in [
                "Hyena", "Lion", "Tiger", 
                "Buffalo", "Elephant", "Giraffe", "Hippo", "Zebra"
            ]:
                self.control.spawn_animal(item["name"].upper())
            self.show_feedback(f"Purchased {item['name']} for ${item['cost']}")
        else:
            self.show_feedback("Insufficient funds!")

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
        for label in [f"Tourists: {len(self.control.board.tourists)}",
                      f"Animals:   {len(self.control.board.animals)}"]:
            w = draw_box(label, x)
            x += w + margin

        # capital on right
        draw_box(f"Capital: ${self.control.capital.getBalance():.0f}", margin, {
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
        date, time_str = self.control.timer.get_date_time()
        game_time      = self.control.timer.get_game_time()

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


# if __name__ == "__main__":
#     GameGUI(DifficultyLevel.NORMAL).run()
