import math
from numbers import Real
from typing import Self
from collections.abc import Sequence

import pygame as pg
from pygame.typing import Point


_FALLBACK_SURF = pg.Surface((2, 2))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(1, 0, 1, 1))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(0, 1, 1, 1))


class WallTexture(object):
    def __init__(self: Self, obj: pg.Surface | str) -> None:
        surf = obj
        if isinstance(obj, str):
            try:
                surf = pg.image.load(obj)
            except FileNotFoundError:
                surf = _FALLBACK_SURF
        self._surf = surf
        self._lines = []
        self._width = surf.width
        height = surf.height
        for i in range(self._width):
            line = pg.Surface((1, height))
            line.blit(surf, (0, 0), area=pg.Rect(i, 0, 1, height))
            self._lines.append(line)

    def __getitem__(self: Self, dex: int) -> pg.Surface:
        return self._lines[dex]
    
    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def width(self: Self) -> Real:
        return self._width


class Floor(object):
    def __init__(self: Self,
                 obj: pg.Surface | str,
                 scale: Point=(1, 1)) -> None:

        surf = obj
        if isinstance(obj, str):
            try:
                surf = pg.image.load(obj)
            except FileNotFoundError:
                surf = _FALLBACK_SURF
        self._surf = surf
        self._scale = list(scale)
        self._array = pg.surfarray.array3d(surf)
    
    def __getitem__(self: Self, dex: object):
        return self._array[dex]

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf.copy()

    @surf.setter
    def surf(self: Self, value: pg.Surface) -> None:
        self._surf = value.copy()

    @property
    def width(self: Self) -> Real:
        return self._surf.width

    @property
    def height(self: Self) -> Real:
        return self._surf.height

    @property
    def scale(self: Self) -> tuple:
        return tuple(self._scale)


class Walls(object):
    def __init__(self: Self,
                 tilemap: dict,
                 textures: tuple[WallTexture]) -> None:

        self._tilemap = tilemap.copy()
        self._textures = list(textures)

    def set_tile(self: Self,
                 pos: Point,
                 elevation: Real,
                 height: Real,
                 texture: int):

        self._walls[f'{pos[0]};{pos[1]}'] = {
            'elevation': elevation,
            'height': height, 
            'texture': texture,
        }

    def remove_tile(self: Self, pos: Point):
        return self._walls.pop(f'{pos[0]};{pos[1]}')

    @property
    def tilemap(self: Self) -> dict:
        return self._tilemap.copy()

    @property
    def textures(self: Self) -> tuple:
        return tuple(self._textures)


class Level(object):
    def __init__(self: Self, floor: Floor, walls: tuple[Walls]) -> None:

        self._floor = floor
        self._walls = list(walls)

    @property
    def floor(self: Self) -> Floor:
        return self._floor

    @floor.setter
    def floor(self: Self, value: Floor) -> None:
        self._floor = value

    @property
    def walls(self: Self) -> tuple:
        return tuple(self._walls)
    
    @walls.setter
    def walls(self: Self, value: Walls) -> None:
        self._walls = list(value)
    
    def add_walls(self: Self, walls: Walls) -> None:
        self._walls.append(walls)

    def remove_walls(self: Self, dex: int) -> None:
        del self._walls[dex]

