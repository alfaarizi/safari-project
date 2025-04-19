from __future__ import annotations
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pygame
from pygame.math import Vector2

from my_safari_project.model.board import Board
from my_safari_project.model.capital import Capital
from my_safari_project.model.ranger import Ranger
from my_safari_project.model.poacher import Poacher

from my_safari_project.view.boardgui import BoardGUI



SCREEN_W, SCREEN_H = 1080, 720
SIDE_PANEL_W = 320
TOP_BAR_H = 60

BOARD_RECT = pygame.Rect(
    0, TOP_BAR_H,
    SCREEN_W - SIDE_PANEL_W,
    SCREEN_H - TOP_BAR_H
)

POACHER_INTERVAL = 20.0        # seconds between automatic spawns
MAX_POACHERS     = 6


class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Safari – prototype")

        # MODEL --------------------------------------------------------------
        self.board   = Board(30, 30)
        self.capital = Capital(1000.0)

        # VIEW ---------------------------------------------------------------
        self.board_gui = BoardGUI(self.board)

        # UI state
        self.font_small  = pygame.font.SysFont("Verdana", 16)
        self.font_medium = pygame.font.SysFont("Verdana", 20)
        self.font_large  = pygame.font.SysFont("Verdana", 28, bold=True)

        self.button_h = 40
        self.button_w = 150
        self.button_gap = 10

        self.day_phase = "Day"
        self.running   = True
        self.feedback: str = ""
        self.feedback_timer = 0.0
        self.feedback_alpha = 0

        # shop definitions
        self.shop_items: List[Dict] = [
            {"name":"Ranger", "cost":150},
            {"name":"Plant",  "cost":20},
            {"name":"Pond",   "cost":200},
        ]
        self.item_rects: List[pygame.Rect] = []
        self.hover_item = -1

        # timers
        self.clock = pygame.time.Clock()
        self._poacher_timer = 0.0

        # seed one ranger so you can see behaviour
        self._spawn_ranger()

    # ------------------------------------------------------------------ main
    def run(self):
        while self.running:
            raw_dt = self.clock.tick(60) / 1000.0
            dt = min(raw_dt, 0.02)

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
                for i,r in enumerate(self.item_rects):
                    if r.collidepoint(ev.pos):
                        self.hover_item = i
                        break
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # did we click a shop item?
                for i,r in enumerate(self.item_rects):
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
        return Vector2(random.randint(0,self.board.width-1),
                       random.randint(0,self.board.height-1))

    def _spawn_ranger(self):
        rid = len(self.board.rangers)+1
        ranger = Ranger(rid, f"R{rid}", salary=50,
                        position=self._random_tile())
        self.board.rangers.append(ranger)

    def _spawn_poacher(self):
        pid = len(self.board.poachers)+1
        p = Poacher(pid, f"P{pid}", position=self._random_tile())
        self.board.poachers.append(p)

    def _spawn_plant(self):
        from my_safari_project.model.plant import Plant
        pid = len(self.board.plants)+1
        self.board.plants.append(Plant(pid, self._random_tile(),
                                       "Bush", 20, 0.0, 1, True))

    def _spawn_pond(self):
        from my_safari_project.model.pond import Pond
        pid = len(self.board.ponds)+1
        self.board.ponds.append(Pond(pid, self._random_tile(),
                                     "Pond", 0,0,0,0))

    # ------------------------------------------------------------------ tick
    def _update_sim(self, dt: float):
        # day/night
        self.board_gui.update_day_night(dt)

        # auto‑spawn poachers
        if len(self.board.poachers) < MAX_POACHERS:
            self._poacher_timer += dt
            if self._poacher_timer >= POACHER_INTERVAL:
                self._poacher_timer = 0.0
                self._spawn_poacher()

        # update poachers
        for p in self.board.poachers:
            p.update(dt, (self.board.width, self.board.height))

        # rangers AI
        for r in self.board.rangers:
            # look for nearest visible poacher
            visible = [p for p in self.board.poachers if p.is_visible_to(r)]
            if visible:
                target = min(visible, key=lambda p: r.position.distance_to(p.position))
                r.chase_poacher(target)
                if r.eliminate_poacher(target):
                    self.capital.addFunds(50)      # bounty
            else:
                r.patrol(self.board.width, self.board.height)

        # feedback fade
        if self.feedback_timer>0:
            self.feedback_timer -= dt
            self.feedback_alpha = int(255*min(1.0, self.feedback_timer*2))
        else:
            self.feedback_alpha = 0
            self.feedback      = ""

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill((40,45,50))

        # board area rect
        self.board_gui.render(self.screen, BOARD_RECT)

        self._draw_top_bar()
        self._draw_side_panel()
        self._draw_feedback()
        pygame.display.flip()

    # ---------- UI draw helpers --------------------------------------
    def _draw_top_bar(self):
        pygame.draw.rect(self.screen,(60,70,90),(0,0,SCREEN_W,TOP_BAR_H))
        cap = self.font_medium.render(f"Capital: ${self.capital.getBalance():.0f}", True, (255,255,255))
        self.screen.blit(cap,(SCREEN_W-cap.get_width()-20,(TOP_BAR_H-cap.get_height())//2))

    def _draw_side_panel(self):
        px,py = SCREEN_W - SIDE_PANEL_W, TOP_BAR_H
        pygame.draw.rect(self.screen,(70,80,100),(px,py,SIDE_PANEL_W,SCREEN_H-py))
        title = self.font_large.render("Shop", True, (255,255,255))
        self.screen.blit(title,(px+20,py+10))

        self.item_rects.clear()
        y = py+70
        for i,item in enumerate(self.shop_items):
            rect = pygame.Rect(px+20, y, SIDE_PANEL_W-40, 40)
            self.item_rects.append(rect)
            color = (80,110,160) if i==self.hover_item else (90,100,120)
            pygame.draw.rect(self.screen,color,rect,border_radius=4)
            txt = self.font_medium.render(f"{item['name']}: ${item['cost']}",True,(255,255,255))
            self.screen.blit(txt,(rect.x+8,rect.y+8))
            y += 48

    def _draw_feedback(self):
        if self.feedback_alpha<=0: return
        surf = self.font_medium.render(self.feedback,True,(255,255,255))
        surf.set_alpha(self.feedback_alpha)
        x = (SCREEN_W-surf.get_width())//2
        y = SCREEN_H - surf.get_height() - 20
        self.screen.blit(surf,(x,y))

    def _show_feedback(self,msg:str):
        self.feedback = msg
        self.feedback_timer = 2.0
        self.feedback_alpha = 255



if __name__ == "__main__":
    GameGUI().run()
