
from pygame.math import Vector2
from my_safari_project.model.road import Road, RoadType
from my_safari_project.model.field import Field

def test_road_neighbors():
    r1 = Road(Vector2(1,1), RoadType.STRAIGHT_H)
    r2 = Vector2(2,1)
    r1.add_neighbor(r2)
    assert r2 in r1.neighbors

def test_field_add_and_remove_object():
    field = Field(Vector2(1, 1))
    obj = object()
    field.add_object(obj)
    assert field.is_occupied()
    field.remove_object(obj)
    assert not field.is_occupied()
