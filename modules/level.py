from numbers import Real
from typing import Self
from typing import Union
from typing import Optional

import pygame as pg
from pygame.typing import Point
from pygame.typing import ColorLike

from modules.entities import EntityManager
from modules.utils import FALLBACK_SURF


class ColumnTexture(object):
    def __init__(self: Self, surf: pg.Surface=FALLBACK_SURF) -> None:
        self._surf = surf
        self._alpha = surf.get_alpha()

    def __getitem__(self: Self, dex: int) -> pg.Surface:
        return self._surf.subsurface((dex, 0, 1, self._surf.height))

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def width(self: Self) -> int:
        return self._surf.width

    @property
    def height(self: Self) -> int:
        return self._surf.height


class Floor(object):
    def __init__(self: Self,
                 surf: pg.Surface=FALLBACK_SURF,
                 scale: Point=(1, 1)) -> None:

        self.surf = surf
        self.scale = scale
        self._array = pg.surfarray.array3d(surf)
    
    def __getitem__(self: Self, dex: object):
        return self._array[dex]

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @surf.setter
    def surf(self: Self, value: pg.Surface) -> None:
        self._surf = value

    @property
    def scale(self: Self) -> tuple:
        return self._scale

    @scale.setter
    def scale(self: Self, value: Point) -> None:
        self._scale = tuple(value)

    @property
    def width(self: Self) -> Real:
        return self._surf.width

    @property
    def height(self: Self) -> Real:
        return self._surf.height


class Sky(object):
    def __init__(self: Self,
                 surf: pg.Surface=FALLBACK_SURF,
                 height: Optional[int]=None) -> None:

        self._surf = surf
        self._height = height
        if height is None:
            self._height = surf.height
    
    def scroll(self: Self,
               offset: Real,
               width: int,
               height: int) -> pg.Surface:

        surf = self._surf.copy()
        surf = pg.transform.scale(surf, (width, height))
        surf.scroll(int(offset), 0, pg.SCROLL_REPEAT)

        return surf


class Walls(object):
    def __init__(self: Self,
                 tilemap: dict,
                 textures: list[ColumnTexture]) -> None:

        self._tilemap = tilemap
        self._textures = textures

    def set_tile(self: Self,
                 pos: Point,
                 elevation: Real,
                 height: Real,
                 texture: int,
                 top: ColorLike=(0, 0, 0),
                 bottom: ColorLike=(0, 0, 0)):

        self._tilemap[f'{pos[0]};{pos[1]}'] = {
            'elevation': elevation,
            'height': height,
            'texture': texture,
            'top': top,
            'bottom': bottom,
        }

    def remove_tile(self: Self, pos: Point):
        return self._walls.pop(f'{pos[0]};{pos[1]}')

    @property
    def tilemap(self: Self) -> dict:
        return self._tilemap

    @property
    def textures(self: Self) -> tuple:
        return self._textures


class Level(object):
    def __init__(self: Self,
                 floor: Optional[Union[Floor, Sky]],
                 ceiling: Optional[Union[Floor, Sky]],
                 walls: Walls,
                 entities: EntityManager) -> None:

        self._floor = floor
        self._ceiling = ceiling
        self._walls = walls
        self._entities = entities
        entities._level = self

    @property
    def floor(self: Self) -> Optional[Union[Floor, Sky]]:
        return self._floor

    @floor.setter
    def floor(self: Self, value: Optional[Union[Floor, Sky]]) -> None:
        self._floor = value

    @property
    def ceiling(self: Self) -> Optional[Union[Floor, Sky]]:
        return self._ceiling

    @ceiling.setter
    def ceiling(self: Self, value: Optional[Union[Floor, Sky]]) -> None:
        self._ceiling = value

    @property
    def walls(self: Self) -> Walls:
        return self._walls
    
    @walls.setter
    def walls(self: Self, value: Walls) -> None:
        self._walls = value

    @property
    def entities(self: Self) -> EntityManager:
        return self._entities

    @entities.setter
    def entities(self: Self, value: EntityManager) -> None:
        self._entities._level = None
        self._entities = value
        value._level = self
    
    def add_walls(self: Self, walls: Walls) -> None:
        self._walls.append(walls)

    def remove_walls(self: Self, dex: int) -> None:
        return self._walls.pop(dex)


