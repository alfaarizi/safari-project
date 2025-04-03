import pygame
from pygame.math import Vector2
from typing import List, Any

class Field:
    def __init__(
        self,
        position: Vector2,
        field_id: int = 0,
        terrain_type: str = "GRASS",
        elevation: float = 0.0,
        is_obstacle: bool = False,
        water_level: float = 0.0
    ):
        self.field_id = field_id
        self.position = position
        self.x = int(position.x)
        self.y = int(position.y)
        self.terrain_type = terrain_type.upper()
        self.elevation = elevation
        self.is_obstacle = is_obstacle
        self.water_level = water_level
        self.objects_on_field: List[Any] = []
        self.walkable = not is_obstacle and self.terrain_type != "WATER"
        self.color_map = {
            "GRASS": (34, 139, 34),
            "HILL": (139, 69, 19),
            "WATER": (28, 107, 160),
            "ROAD": (128, 128, 128),
            "FOREST": (0, 100, 0)
        }

    def add_object(self, obj: Any) -> None:
        self.objects_on_field.append(obj)

    def remove_object(self, obj: Any) -> None:
        if obj in self.objects_on_field:
            self.objects_on_field.remove(obj)

    def is_occupied(self) -> bool:
        return len(self.objects_on_field) > 0

    def update(self, delta_time: float) -> None:
        if self.terrain_type == "WATER":
            self.water_level = max(self.water_level - 0.1 * delta_time, 0.0)
        elif self.terrain_type == "GRASS":
            if self.water_level < 1.0:
                self.water_level = min(self.water_level + 0.05 * delta_time, 1.0)
        for obj in self.objects_on_field:
            if hasattr(obj, "update"):
                obj.update(delta_time)

    def draw(self, surface: pygame.Surface, tile_size: int, camera_offset: Vector2 = Vector2(0, 0)) -> None:
        rect = pygame.Rect(
            self.x * tile_size - camera_offset.x,
            self.y * tile_size - camera_offset.y,
            tile_size,
            tile_size
        )
        base_color = self.color_map.get(self.terrain_type, (0, 0, 0))
        pygame.draw.rect(surface, base_color, rect)
        if self.terrain_type == "WATER" and self.water_level > 0:
            overlay = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            overlay.fill((28, 107, 160, int(255 * min(self.water_level, 1.0))))
            surface.blit(overlay, rect.topleft)
        if self.is_occupied():
            font = pygame.font.SysFont(None, 20)
            text_surface = font.render(str(len(self.objects_on_field)), True, (255, 255, 255))
            surface.blit(text_surface, rect.topleft)

    def set_terrain_type(self, terrain_type: str) -> None:
        self.terrain_type = terrain_type.upper()
        self.walkable = not self.is_obstacle and self.terrain_type != "WATER"

    def set_elevation(self, elevation: float) -> None:
        self.elevation = elevation

    def set_obstacle(self, is_obstacle: bool) -> None:
        self.is_obstacle = is_obstacle
        self.walkable = not is_obstacle and self.terrain_type != "WATER"

    def __repr__(self) -> str:
        return (
            f"Field(id={self.field_id}, pos=({self.x}, {self.y}), "
            f"terrain={self.terrain_type}, elev={self.elevation}, "
            f"obstacle={self.is_obstacle}, objects={len(self.objects_on_field)})"
        )

