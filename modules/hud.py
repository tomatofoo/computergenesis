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


class HUDWeapon(HUDElement):
    def __init__(self: Self,
                 default: list[pg.Surface],
                 attack: list[pg.Surface],
                 pos: Point,
                 bob_frequency: Real=0.08335,
                 bob_strength: Real=20,
                 default_frame_time: Real=0,
                 attack_frame_time: Real=15) -> None:

        self._default = default
        self._attack = attack
        self._default_frame_time = default_frame_time
        self._attack_frame_time = attack_frame_time
        self._surf = default[0]

        self._original_pos = pos
        self._pos = pos

        self._bob_frequency = bob_frequency
        self._bob_strength = bob_strength

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def pos(self: Self) -> tuple:
        return self._pos

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        self._pos = (
            (self._original_pos[0]
             + math.sin(level_timer * self._bob_frequency)
             * self._bob_strength),
            (self._original_pos[1]
             + abs(math.cos(level_timer * self._bob_frequency))
             * self._bob_strength / 2),
        )

# CUSTOM

