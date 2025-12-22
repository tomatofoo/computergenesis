from numbers import Real
from typing import Self

import pygame as pg


class HUDElement(object):
    def __init__(self: Self, surf: pg.Surface) -> None:
        self._surf = surf

    def update(self: Self) -> None:
        pass


class HUD(object):
    def __init__(self: Self, ) -> None:
        pass


