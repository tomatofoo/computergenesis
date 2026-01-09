import math
from numbers import Real
from typing import Self

import pygame as pg
from pygame.typing import Point


class HUDElement(object):
    def __init__(self: Self, surf: pg.Surface, pos: Point) -> None:
        self._surf = surf
        self._pos = pos

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def pos(self: Self) -> Point:
        return self._pos

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        pass


class HUD(object):
    def __init__(self: Self, elements: list[HUDElement]) -> None:
        self._elements = elements

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        for element in self._elements:
            element.update(rel_game_speed, level_timer)

    def render(self: Self, surf: pg.Surface) -> None:
        for element in self._elements:
            surf.blit(element.surf, element.pos)


# CUSTOM

