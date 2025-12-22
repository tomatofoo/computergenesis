from numbers import Real
from typing import Self

import pygame as pg
from pygame.typing import Point


class HUDElement(object):
    def __init__(self: Self, surf: pg.Surface) -> None:
        self._surf = surf

    @property
    def surf(self: Self) -> None:
        return self._surf

    def update(self: Self, rel_game_speed: Real) -> None:
        pass


class HUD(object):
    def __init__(self: Self,
                 elements: dict[object, list[Point, HUDElement]]]) -> None:
        self._elements = elements

    def update(self: Self, rel_game_speed: Real) -> None:
        for _, element in self._elements.values():
            element.update(rel_game_speed)

    def render(self: Self, surf: pg.Surface) -> None:
        for pos, element in self._elements.values():
            surf.blit(element.surf, pos)


