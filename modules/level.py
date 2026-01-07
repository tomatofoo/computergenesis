from __future__ import annotations

import math
from numbers import Real
from typing import Self
from typing import Optional

import pygame as pg
from pygame.typing import Point
from pygame.typing import RectLike
from pygame.typing import ColorLike

from modules.entities import EntityManager
from modules.sound import SoundManager
from modules.utils import FALLBACK_SURF
from modules.utils import gen_tile_key


class ColumnTexture(object):
    def __init__(self: Self, surf: pg.Surface=FALLBACK_SURF) -> None:
        self._surf = surf
        self._transparency = (
            surf.get_colorkey() is not None
            or surf.get_alpha() is not None
        )

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
    def __init__(self: Self, surf: pg.Surface=FALLBACK_SURF) -> None:

        self._surf = surf
        self._width = surf.width
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
        # the one that's rendered, uses special tiles
        self._dynamic_tilemap = tilemap.copy()
        self._textures = textures

    def set_tile(self: Self,
                 pos: Point,
                 elevation: Optional[Real]=None,
                 height: Optional[Real]=None,
                 texture: Optional[int]=None,
                 semitile: Optional[dict]=None,
                 rect: Optional[list]=None,
                 top: Optional[ColorLike]=None,
                 bottom: Optional[ColorLike]=None,
                 change: int=2):
        # change dictates which tilemaps to change
        # 0 = static only
        # 1 = dynamic only
        # 2 = both
        
        # Default Values
        tile_key = gen_tile_key(pos)
        tile = self._tilemap.get(tile_key)
        if tile is None:
            if elevation is None:
                elevation = 0
            if height is None:
                height = 1
            if texture is None:
                texture = 0
        else:
            if elevation is None:
                elevation = tile['elevation']
            if height is None:
                height = tile['height']
            if texture is None:
                texture = tile['texture']
            if top is None:
                top = tile.get('top')
            if bottom is None:
                bottom = tile.get('bottom')
        if top is None:
            top = (0, 0, 0)
        if bottom is None:
            bottom = (0, 0, 0)
        
        # Set
        data = {
            'elevation': elevation,
            'height': height,
            'texture': texture,
            'semitile': semitile,
            'top': top,
            'bottom': bottom,
            'rect': rect,
        }
        if change != 1:
            self._tilemap[tile_key] = data
        if change:
            self._dynamic_tilemap[tile_key] = data

    def pop_tile(self: Self, pos: Point):
        return self._walls.pop(f'{pos[0]};{pos[1]}')

    @property
    def tilemap(self: Self) -> dict:
        return self._tilemap

    @property
    def dynamic_tilemap(self: Self) -> dict:
        return self._dynamic_tilemap

    @property
    def textures(self: Self) -> tuple:
        return self._textures


class Special(object):
    def __init__(self: Self, key: str) -> None:
        self._key = key
        self._manager = None

    @property
    def manager(self: Self) -> SpecialManager:
        return self._manager

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        pass


class SpecialManager(object):
    def __init__(self: Self, specials: set[Special]=set()) -> None:
        self._specials = set()
        self.specials = specials
        self._level = None

    @property
    def specials(self: Self) -> set[Special]:
        return self._specials

    @specials.setter
    def specials(self: Self, value: set[Special]) -> None:
        for special in self._specials:
            special._manager = None
        self._specials = value
        for special in value:
            special._manager = self

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        for special in self._specials:
            special.update(rel_game_speed, level_timer)


class Level(object):
    def __init__(self: Self,
                 floor: Optional[Floor | Sky],
                 ceiling: Optional[Floor | Sky],
                 walls: Walls,
                 specials: SpecialManager,
                 entities: EntityManager,
                 sounds: SoundManager,
                 ceiling_elevation: Real=1) -> None:

        self._floor = floor
        self._ceiling = ceiling
        self._ceiling_elevation = ceiling_elevation
        if not isinstance(ceiling, Floor):
            self._ceiling_elevation = math.inf
        self._walls = walls
        self._specials = specials
        self._entities = entities
        self._sounds = sounds
        specials._level = self
        entities._level = self
        sounds._level = self
        sounds.update()

    @property
    def floor(self: Self) -> Optional[Floor | Sky]:
        return self._floor

    @floor.setter
    def floor(self: Self, value: Optional[Floor | Sky]) -> None:
        self._floor = value

    @property
    def ceiling(self: Self) -> Optional[Floor | Sky]:
        return self._ceiling

    @ceiling.setter
    def ceiling(self: Self, value: Optional[Floor | Sky]) -> None:
        self._ceiling = value

    @property
    def walls(self: Self) -> Walls:
        return self._walls
    
    @walls.setter
    def walls(self: Self, value: Walls) -> None:
        self._walls = value

    @property
    def specials(self: Self) -> Optional[SpecialManager]:
        return self._specials
    
    @specials.setter
    def specials(self: Self, value: Optional[SpecialManager]) -> None:
        self._specials._level = None
        self._specials = value
        value._level = self

    @property
    def entities(self: Self) -> EntityManager:
        return self._entities

    @entities.setter
    def entities(self: Self, value: EntityManager) -> None:
        self._entities._level = None
        self._entities = value
        value._level = self

    @property
    def sounds(self: Self) -> SoundManager:
        return self._sounds

    @sounds.setter
    def sounds(self: Self, value: SoundManager) -> None:
        self._sounds._level = None
        self._sounds = value
        value._level = self
        value.update()

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        self._sounds.update()
        self._entities.update(rel_game_speed, level_timer)
        self._specials.update(rel_game_speed, level_timer)

