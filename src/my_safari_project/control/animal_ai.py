from __future__ import annotations
from typing import Dict, List, Any
from pygame import Surface, draw, font, Color
from pygame.math import Vector2

from my_safari_project.model.board import Board

COLLISION_RADIUS = 0.5
DETECTION_RADIUS = 4.5
EPSILON = 1e-5

DEFAULT_COLOR = Color(0, 100, 255, 128)
OUTLINE_COLOR = Color(255, 255, 255)
COLLISION_COLOR = Color(255, 0, 0, 180)
LABEL_FONT_SIZE = 28
DIRECTION_LINE_WIDTH = 3

class AnimalAI:
    def __init__(self, board: Board):
        self.board = board
        self.collision_shapes: Dict[int, Dict] = {}
        self.detected_entities: Dict[int, Dict[str, List[Any]]] = {}
        self.debug_mode = False
        self.label = font.SysFont(None, LABEL_FONT_SIZE, bold=True)

    def update(self, dt: float) -> None:
        self.collision_shapes = {
            animal.animal_id: {
                "animal": animal,
                "position": animal.position,
                "speed": animal.speed,
                "in_collision": False,
                "collision_radius": COLLISION_RADIUS,
                "detection_radius": DETECTION_RADIUS,
                "color": DEFAULT_COLOR,
                "detection_color": animal.species.color,
            }
            for animal in self.board.animals if animal.alive
        }

        self.detected_entities = {
            animal_id: {
                "detected": [], 
                "collided": []
            }
            for animal_id in self.collision_shapes
        }

        self.process_collisions()

    def process_collisions(self) -> None:
        for animal_id, shape in self.collision_shapes.items():
            entity_types = [
                ('jeep', self.board.jeeps),
                ('plant', self.board.plants),
                ('pond', self.board.ponds),
                ('animal', [a for a in self.board.animals if a.animal_id != animal_id and a.alive]),
                ('ranger', self.board.rangers),
                ('poacher', self.board.poachers),
                ('tourist', self.board.tourists),
            ]
            for entity_type, entities in entity_types:
                for entity in entities:
                    delta: Vector2 = entity.position - shape["position"]
                    sq_dist = delta.length_squared()
                    # detect nearby entities
                    if sq_dist <= shape["detection_radius"] ** 2:
                        distance = sq_dist ** 0.5
                        self.detected_entities[animal_id]["detected"].append({
                            "type": entity_type,
                            "entity": entity,
                            "distance": distance
                        })
                        # detect entity collision
                        min_dist = shape["collision_radius"] + COLLISION_RADIUS
                        if sq_dist <= min_dist ** 2:
                            self.detected_entities[animal_id]["collided"].append({
                                "type": entity_type,
                                "entity": entity,
                                "distance": distance
                            })
                            # collision response
                            distance = max(distance, EPSILON)
                            separation = delta * ((min_dist - distance) / distance)
                            shape["position"] -= separation
                            shape["animal"].position = shape["position"]
                            shape["animal"]._target = None
                            shape["in_collision"] = True
            # sort nearest entities
            self.detected_entities[animal_id]["detected"].sort(key=lambda e: e["distance"])
            self.detected_entities[animal_id]["collided"].sort(key=lambda e: e["distance"])

    def render(
        self,
        surface: Surface,
        offset_x: float,
        offset_y: float,
        tile_size: int,
        min_x: int,
        min_y: int
    ) -> None:
        labels = []
        half_tile = tile_size // 2

        # detection area
        for shape in self.collision_shapes.values():
            screen_pos = (
                offset_x + int((shape["position"].x - min_x) * tile_size) + half_tile,
                offset_y + int((shape["position"].y - min_y) * tile_size) + half_tile
            )
            detection_radius_px = int(shape["detection_radius"] * tile_size)
            draw.circle(surface, shape["detection_color"], screen_pos, detection_radius_px)
            draw.circle(surface, OUTLINE_COLOR, screen_pos, detection_radius_px, width=1)
            labels.append((str(shape["animal"].animal_id), screen_pos))

        # collision area
        for shape in self.collision_shapes.values():
            screen_pos = (
                offset_x + int((shape["position"].x - min_x) * tile_size) + half_tile,
                offset_y + int((shape["position"].y - min_y) * tile_size) + half_tile
            )
            collision_radius_px = int(shape["collision_radius"] * tile_size)
            draw.circle(
                surface,
                COLLISION_COLOR if shape["in_collision"] else shape["color"],
                screen_pos,
                collision_radius_px
            )
            draw.circle(surface, OUTLINE_COLOR, screen_pos, collision_radius_px, width=1)
            
            # direction line
            target = getattr(shape["animal"], "_target", None)
            if target and (dir_vec := target - shape["animal"].position).length_squared() > 0:
                dir_vec = dir_vec.normalize()
                end_pos = (
                    screen_pos[0] + int(dir_vec.x * detection_radius_px),
                    screen_pos[1] + int(dir_vec.y * detection_radius_px),
                )
                draw.line(surface, Color(0, 255, 0), screen_pos, end_pos, DIRECTION_LINE_WIDTH)

        # animal labels
        for label_text, (x, y) in labels:
            y -= int(COLLISION_RADIUS * tile_size) + 10
            text_surf = self.label.render(label_text, True, (255, 255, 255))
            outline_surf = self.label.render(label_text, True, (0, 0, 0))
            rect = text_surf.get_rect(center=(x, y))
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                surface.blit(outline_surf, rect.move(dx, dy))
            surface.blit(text_surf, rect)