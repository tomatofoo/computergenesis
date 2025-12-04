from __future__ import annotations

import math
from numbers import Real
from typing import Self
from typing import Union

import numpy as np
import pygame as pg
from pygame.typing import Point

from modules.utils import gen_tile_key


_FALLBACK_SURF = pg.Surface((2, 2))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(1, 0, 1, 1))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(0, 1, 1, 1))


class ColumnTexture(object):
    def __init__(self: Self, surf: pg.Surface=_FALLBACK_SURF) -> None:
        self._surf = surf

    def __getitem__(self: Self, dex: int) -> pg.Surface:
        return self._surf.subsurface(pg.Rect(dex, 0, 1, self._surf.height))

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
                 surf: pg.Surface=_FALLBACK_SURF,
                 scale: Point=(1, 1)) -> None:

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

class Sky(object):
    def __init__(self: Self,
                 obj: pg.Surface | str,
                 height: Optional[int]=None) -> None:

        surf = obj
        if isinstance(obj, str):
            try:
                surf = pg.image.load(obj)
            except FileNotFoundError:
                surf = _FALLBACK_SURF
        self._surf = surf
        self._height = height
        if height == None:
            self._height = surf.height
    
    def scroll(self: Self,
               offset: Real,
               width: int,
               height: int) -> pg.Surface:

        surf = self._surf.copy()
        surf.scroll(int(offset), 0, pg.SCROLL_REPEAT)
        surf = pg.transform.scale(surf, (width, height))

        return surf


class Walls(object):
    def __init__(self: Self,
                 tilemap: dict,
                 textures: tuple[ColumnTexture]) -> None:

        self._tilemap = tilemap.copy()
        self._textures = list(textures)

    def set_tile(self: Self,
                 pos: Point,
                 elevation: Real,
                 height: Real,
                 texture: int):

        self._tilemap[f'{pos[0]};{pos[1]}'] = {
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


class Entity(object):

    _TILE_OFFSETS = (
        (-1, 1), (0, 1), (1, 1),
        (-1, 0), (0, 0), (1, 0),
        (-1, -1), (0, -1), (1, -1),
    )

    def __init__(self: Self, 
                 width: Real=0.5,
                 height: Real=1,
                 texture: pg.Surface=_FALLBACK_SURF) -> None:

        self.texture = texture
        self.yaw = 0
        self.velocity2 = (0, 0)
        self.elevation_velocity = 0
        self.yaw_velocity = 0
        self.elevation = 0
        self._pos = pg.Vector2(0, 0)
        self._width = width # width of rect
        self._height = height
        self._manager = None
  
    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos.copy()

    @pos.setter
    def pos(self: Self, value: Point) -> None:
        old_key = gen_tile_key(self._pos)
        self._pos = pg.Vector2(value)
        key = gen_tile_key(self._pos)
        if self._manager:
            self._update_manager_sets(old_key, key)

    @property
    def x(self: Self) -> Real:
        return self._pos.x

    @x.setter
    def x(self: Self, value: Real) -> None:
        self._pos.x = value

    @property
    def y(self: Self) -> Real:
        return self._pos.y

    @y.setter
    def y(self: Self, value: Real) -> None:
        self._pos.y = value

    @property
    def forward(self: Self) -> pg.Vector2:
        return self._yaw

    @property
    def right(self: Self) -> pg.Vector2:
        return self._plane

    @property
    def elevation(self: Self) -> Real:
        return self._elevation

    @elevation.setter
    def elevation(self: Self, value: Real) -> None:
        self._elevation = max(value, 0)

    @property
    def tile(self: Self) -> None:
        return (int(math.floor(self._pos[0])),
                int(math.floor(self._pos[1])))

    @property
    def vector2(self: Self) -> pg.Vector2:
        return self._pos.copy()
    
    @property
    def vector3(self: Self) -> pg.Vector3:
        return pg.Vector3(self._pos.x, self._elevation, self._pos.y)

    @property
    def yaw(self: Self) -> float:
        return self._yaw_value

    @yaw.setter
    def yaw(self: Self, value: Real) -> None:
        self._yaw_value = value
        self._yaw = pg.Vector2(0, 1).rotate(value)
        self._semiplane = pg.Vector2(-self._yaw.y, self._yaw.x)
        # -1 because direction is flipped
        # the plane is for the camera but it is also the right vector

    @property
    def width(self: Self) -> Real:
        return self._width

    @width.setter
    def width(self: Self, value: Real) -> None:
        self._width = value

    @property
    def height(self: Self) -> Real:
        return self._height

    @height.setter
    def height(self: Self, value: Real) -> None:
        self._height = value

    @property
    def velocity2(self: Self) -> pg.Vector2:
        return self._velocity2.copy()

    @velocity2.setter
    def velocity2(self: Self, value: Point) -> None:
        self._velocity2 = pg.Vector2(value)

    @property
    def elevation_velocity(self: Self) -> Real:
        return self._elevation_velocity

    @elevation_velocity.setter
    def elevation_velocity(self: Self, value: Real) -> None:
        self._elevation_velocity = value

    @property
    def yaw_velocity(self: Self) -> Real:
        return self._yaw_velocity

    @yaw_velocity.setter
    def yaw_velocity(self: Self, value: Real) -> None:
        self._yaw_velocity = value

    @property
    def texture(self: Self) -> ColumnTexture:
        return self._texture

    @texture.setter
    def texture(self: Self, value: ColumnTexture) -> None:
        self._texture = value

    @property
    def manager(self: Self) -> EntityManager:
        if self._manager == None:
            raise ValueError('Must assign manager to this entity')
        return self._manager

    def _get_rects_around(self: Self) -> list:
        tile = pg.Vector2(math.floor(self._pos.x), math.floor(self._pos.y))
        tiles = []
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            level_string = f'{int(offset_tile.x)};{int(offset_tile.y)}'
            walls = self.manager._level._walls
            if walls._tilemap.get(level_string) != None:
                tiles.append(pg.Rect(offset_tile.x, offset_tile.y, 1, 1))
        return tiles

    def _update_manager_sets(self: Self, old_key: str, key: str) -> None:
        if old_key != key:
            self._manager._sets[old_key].remove(self)
            if not self._manager._sets[old_key]:
                self._manager._sets.pop(old_key)
            if not self._manager._sets.get(key):
                self._manager._sets[key] = set()
            self._manager._sets[key].add(self)

    def rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._width, self._width)
        rect.center = self._pos
        return rect
    
    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        # I'm not sure if there is a reason that these 
        # aren't being multiplied by delta time
        self._elevation += self._elevation_velocity * rel_game_speed
        if self._yaw_velocity:
            self.yaw += self._yaw_velocity * rel_game_speed
         
        self._pos.x += self._velocity2.x * rel_game_speed
        entity_rect = self.rect()
        for rect in self._get_rects_around():
            if entity_rect.colliderect(rect):
                if self._velocity2.x > 0:
                    entity_rect.right = rect.left
                elif self._velocity2.x < 0:
                    entity_rect.left = rect.right
                self._pos.x = entity_rect.centerx
        self._pos.y += self._velocity2.y * rel_game_speed
        entity_rect = self.rect()
        for rect in self._get_rects_around():
            if entity_rect.colliderect(rect):
                if self._velocity2.y > 0:
                    entity_rect.bottom = rect.top
                elif self._velocity2.y < 0:
                    entity_rect.top = rect.bottom
                self._pos.y = entity_rect.centery


class Player(Entity):
    def __init__(self: Self,
                 width: Real=0.5,
                 height: Real=1,
                 yaw_sensitivity: Real=0.125,
                 mouse_enabled: bool=1,
                 keyboard_look_enabled: bool=1) -> None:

        super().__init__(width)
        self._forward_velocity = pg.Vector2(0, 0)
        self._right_velocity = pg.Vector2(0, 0)
        # offset for camera's viewpoint
        self._camera_offset = 0.5
        self._render_elevation = self._elevation + self._camera_offset
        
        self._settings = {
            'bob_strength': 0,
            'bob_frequency': 0,
        }

    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos.copy()

    @pos.setter
    def pos(self: Self, value: Point) -> None:
        self._pos = pg.Vector2(value)

    @property
    def _render_vector3(self: Self) -> pg.Vector3:
        return pg.Vector3(self._pos.x, self._render_elevation, self._pos.y)

    @property
    def velocity2(self: Self) ->  pg.Vector2:
        return self._velocity2

    @velocity2.setter
    def velocity2(self: Self, value: Point) -> None:
        self._velocity2 = pg.Vector2(value)
        self._forward_velocity = self._velocity2.project(self._yaw)
        self._right_velocity = self._velocity2.project(self._semiplane)

    def update(self: Self,
               rel_game_speed: Real,
               level_timer: Real,
               forward: Real,
               right: Real,
               yaw: Real) -> None:

        if forward:
            self._forward_velocity.update(self._yaw * forward)
        if right:
            self._right_velocity.update(self._semiplane * right)
        
        self._yaw_velocity = yaw

        vel_mult = 0.90625**rel_game_speed # number used in Doom
        elevation_update = 0
        if self._forward_velocity.magnitude() >= 0.001:
            elevation_update = 1
            self._forward_velocity *= vel_mult
        else:
            self._forward_velocity.update(0, 0)
        if self._right_velocity.magnitude() >= 0.001:
            elevation_update = 1
            self._right_velocity *= vel_mult
        else:
            self._right_velocity.update(0, 0)
        
        self._render_elevation = self._elevation + self._camera_offset
        if elevation_update:
            self._render_elevation += (
                math.sin(level_timer * self._settings['bob_frequency'])
                * self._settings['bob_strength']
                * min(self._velocity2.magnitude() * 20, 2)
            )

        self._velocity2 = self._forward_velocity + self._right_velocity
        super().update(rel_game_speed, level_timer)
        

class EntityManager(object):
    
    def __init__(self: Self, 
                 player: Player, 
                 entities: dict[object, Entity]) -> None:
        self._player = player
        player._manager = self
        self._entities = entities.copy()
        self._sets = {}
        for entity in entities.values():
            self._add_to_sets(entity)
            entity._manager = self
        self._level = None

        # _sets is a dictionary where each key is a tile position and the value
        # is the set of all entities in that position

    def __getitem__(self: Self, key: object) -> Entity:
        return self._entities[key]
    
    @property
    def entities(self: Self) -> dict:
        return self._entities.copy()

    @entities.setter
    def entities(self: Self, value: dict) -> None:
        for entity in self._entities.values():
            entity._manager = None

        self._entities = value.copy()
        self._sets = {}
        for entity in self._entities.values():
            self._add_to_sets(entity)
            entity._manager = self

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player) -> None:
        self._player = value

    @property
    def level(self: Self) -> Level:
        if self._level == None:
            raise ValueError('Must assign level to manager')
        return self._level

    def _add_to_sets(self: Self, entity: Entity) -> None:
        key = gen_tile_key(entity._pos)
        if self._sets.get(key) == None:
            self._sets[key] = set()
        self._sets[key].add(entity)

    def add_entity(self: Self, entity: Entity, id: object) -> None:
        self._entities[id] = entity
        self._add_to_sets(entity)

    def remove_entity(self: Self, id: object) -> None:
        entity = self._entities[id]
        key = gen_tile_key(entity._pos)
        self._sets[key].remove(entity) # remove from set
        entity._manager = None
        return self._entities.pop(id)

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        for entity in self._entities.values():
            old_key = gen_tile_key(entity._pos)
            entity.update(rel_game_speed, level_timer)
            key = gen_tile_key(entity._pos)
            entity._update_manager_sets(old_key, key)

