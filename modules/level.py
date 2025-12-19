from __future__ import annotations

import math
import bisect
from numbers import Real
from typing import Self
from typing import Union
from typing import Optional

import numpy as np
import pygame as pg
from pygame.typing import Point
from pygame.typing import ColorLike

from modules.utils import gen_tile_key


_FALLBACK_SURF = pg.Surface((2, 2))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(1, 0, 1, 1))
pg.draw.rect(_FALLBACK_SURF, (255, 0, 255), pg.Rect(0, 1, 1, 1))


class ColumnTexture(object):
    def __init__(self: Self, surf: pg.Surface=_FALLBACK_SURF) -> None:
        self._surf = surf

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
                 surf: pg.Surface=_FALLBACK_SURF,
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
                 surf: pg.Surface=_FALLBACK_SURF,
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


class Entity(object):

    _TILE_OFFSETS = (
        (-1, 1), (0, 1), (1, 1),
        (-1, 0), (0, 0), (1, 0),
        (-1, -1), (0, -1), (1, -1),
    )

    def __init__(self: Self, 
                 width: Real=0.5,
                 height: Real=1,
                 health: Real=100,
                 climb: Real=0.3,
                 textures: list[pg.Surface]=[_FALLBACK_SURF],
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        self.yaw = 0
        self.velocity2 = (0, 0)
        self.elevation_velocity = 0
        self.yaw_velocity = 0
        self.elevation = 0
        self.textures = textures
        self._glowing = 0
        self._pos = pg.Vector2(0, 0)
        self._width = width # width of rect
        self._height = height
        self._render_width = render_width
        self._render_height = render_height
        if render_width is None:
            self._render_width = width
        if render_height is None:
            self._render_height = height
        self._health = health
        self._manager = None

    @property
    def glowing(self: Self) -> int:
        return self._glowing

    @glowing.setter
    def glowing(self: Self, value: bool) -> None:
        self._glowing = value
  
    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos

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
        return self._pos
    
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
    def top(self: Self) -> Real:
        return self._elevation + self._height

    @top.setter
    def top(self: Self, value: Real) -> None:
        self._elevation = value - self._height

    @property
    def centere(self: Self) -> Real:
        return self._elevation + self._height / 2
    
    @centere.setter
    def centere(self: Self, value: Real) -> None:
        self._elevation = value - self._height / 2

    @property
    def health(self: Self) -> Real:
        return self._health

    @health.setter
    def health(self: Self, value: Real) -> None:
        self._health = value

    @property
    def velocity2(self: Self) -> pg.Vector2:
        return self._velocity2

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
    def textures(self: Self) -> list[pg.Surface]:
        # might be dangerous because won't change texture angle
        # if user appends etc
        return self._textures

    @textures.setter
    def textures(self: Self, value: list[pg.Surface]) -> None:
        self._textures = value
        self._texture_angle = 360 / len(value)

    @property
    def manager(self: Self) -> EntityManager:
        if self._manager is None:
            raise ValueError('Must assign manager to this entity')
        return self._manager

    def _get_rects_around(self: Self) -> list:
        tile = pg.Vector2(math.floor(self._pos.x), math.floor(self._pos.y))
        tiles = []
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            tile_key = gen_tile_key(offset_tile)
            walls = self.manager._level._walls
            data = walls._tilemap.get(tile_key)
            if data is not None:
                tiles.append((
                    pg.Rect(offset_tile.x, offset_tile.y, 1, 1),
                    data['elevation'],
                    data['elevation'] + data['height'],
                ))
            entities = self.manager._sets.get(tile_key)
            if entities:
                for entity in entities:
                    tiles.append((
                        entity.rect(),
                        entity._elevation,
                        entity.top,
                    ))
        return tiles

    def _update_manager_sets(self: Self, old_key: str, key: str) -> None:
        if old_key != key:
            self._manager._sets[old_key].remove(self)
            if not self._manager._sets[old_key]:
                self._manager._sets.pop(old_key)
            if not self._manager._sets.get(key):
                self._manager._sets[key] = set()
            self._manager._sets[key].add(self)

    def damage(self: Self, value: Real) -> None:
        self._health -= value
        if self._health <= 0:
            self.die()

    def die(self: Self) -> None:
        pass

    def rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._width, self._width)
        rect.center = self._pos
        return rect
    
    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        if self._yaw_velocity:
            self.yaw += self._yaw_velocity * rel_game_speed

        self._pos.x += self._velocity2.x * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._velocity2.x > 0:
                    entity_rect.right = rect.left
                elif self._velocity2.x < 0:
                    entity_rect.left = rect.right
                self._pos.x = entity_rect.centerx

        self._pos.y += self._velocity2.y * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._velocity2.y > 0:
                    entity_rect.bottom = rect.top
                elif self._velocity2.y < 0:
                    entity_rect.top = rect.bottom
                self._pos.y = entity_rect.centery
        
        # 3D collisions
        self.elevation += self._elevation_velocity * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._elevation_velocity > 0:
                    self.top = bottom
                elif self._elevation_velocity < 0:
                    self.elevation = top


class Player(Entity):
    def __init__(self: Self,
                 width: Real=0.5,
                 height: Real=1,
                 melee_range: Real=0.2,
                 yaw_sensitivity: Real=0.125,
                 mouse_enabled: bool=1,
                 keyboard_look_enabled: bool=1) -> None:

        super().__init__(width, height)
        self._melee_range = melee_range

        self._forward_velocity = pg.Vector2(0, 0)
        self._right_velocity = pg.Vector2(0, 0)
        # offset for camera's viewpoint
        self._camera_offset = 0.5
        self._render_elevation = self._elevation + self._camera_offset
        
        self._settings = {
            'bob_strength': 0,
            'bob_frequency': 0,
        }
        
        # delete variables we don't need from entity init
        del self._textures
        del self._texture_angle
        del self._glowing
        del self._render_width
        del self._render_height

    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos

    @pos.setter
    def pos(self: Self, value: Point) -> None:
        self._pos = pg.Vector2(value)

    @property
    def _render_vector3(self: Self) -> pg.Vector3:
        return pg.Vector3(self._pos.x, self._render_elevation, self._pos.y)

    @property
    def velocity2(self: Self) -> pg.Vector2:
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
               yaw: Real,
               up: Real=0) -> None:

        if forward:
            self._forward_velocity.update(self._yaw * forward)
        if right:
            self._right_velocity.update(self._semiplane * right)

        self._elevation_velocity = up
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

    def shoot(self: Self,
              damage: Real,
              shot_range: Real=20,
              foa: Real=60, # field of attack
              precision: int=2):

        # Hitscan gunshot

        # NOTE: this algorithm allows shooting through 
        # vertical corners of walls
        # e.g floor and wall together create a corner

        ray = tuple(self._yaw.normalize())

        end_pos = list(self._pos)
        last_end_pos = end_pos.copy()
        slope = ray[1] / ray[0] if ray[0] else math.inf
        tile = [math.floor(end_pos[0]), math.floor(end_pos[1])]
        tile_key = gen_tile_key(tile)
        last_tile = tile_key
        dir = (ray[0] > 0, ray[1] > 0)
        # step for tile (for each displacement)
        step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
        step_y = dir[1] * 2 - 1 
        dist = 0 # equals depth when ray is in perfet center
        tilemap = self._manager._level._walls._tilemap
        closest = (math.inf, None)

        # ranges of slopes of walls relative to player
        tangent = math.tan(math.radians(foa) / 2)
        slope_ranges = []
        amount = 0
        midheight = self.centere
        vector = self.vector3

        # keep on changing end_pos until hitting a wall (DDA)
        while dist < shot_range and dist < closest[0]:
            # displacements until hit tile
            disp_x = tile[0] + dir[0] - end_pos[0]
            disp_y = tile[1] + dir[1] - end_pos[1]

            len_x = abs(disp_x / ray[0]) if ray[0] else math.inf
            len_y = abs(disp_y / ray[1]) if ray[1] else math.inf
            if len_x < len_y:
                tile[0] += step_x
                end_pos[0] += disp_x
                end_pos[1] += disp_x * slope
                dist += len_x
            else:
                tile[1] += step_y
                end_pos[0] += disp_y / slope if slope else math.inf
                end_pos[1] += disp_y
                dist += len_y

            entities = self.manager._sets.get(last_tile)
            if entities:
                for entity in entities:
                    entity_dist = self._pos.distance_to(entity._pos)
                    if entity._health <= 0 or not entity_dist:
                        continue
                    
                    # checks if entity is outside foa and checks (somewhat 
                    # inaccurately) if shooting at entity will hit tile
                    entity_slope = (entity.centere - midheight) / entity_dist
                    dont_check = 1
                    if -tangent <= entity_slope <= tangent:
                        for i in range(amount + 1):
                            end = slope_ranges[i - 1][1] if i else -math.inf
                            if i < amount:
                                start = slope_ranges[i][0]
                            else: 
                                start = math.inf
                            if end <= entity_slope <= start:
                                dont_check = 0
                                break
                    if dont_check:
                        continue

                    mult = 10**precision
                    rect = entity.rect()
                    rect.update(
                        rect.x * mult,
                        rect.y * mult,
                        rect.w * mult,
                        rect.h * mult,
                    )
                    if rect.clipline(
                        last_end_pos[0] * mult,
                        last_end_pos[1] * mult,
                        end_pos[0] * mult,
                        end_pos[1] * mult,
                    ):
                        entity_dist = vector.distance_to(entity.vector3)
                        if entity_dist < closest[0]:
                            closest = (entity_dist, entity)

            tile_key = gen_tile_key(tile)
            data = tilemap.get(tile_key)
            if data is not None:
                center = (tile[0] + 0.5, tile[1] + 0.5)
                center_dist = self._pos.distance_to(center)
                if center_dist:
                    bottom = data['elevation']
                    top = bottom + data['height']
                    slope_range = [
                        (bottom - midheight) / center_dist,
                        (top - midheight) / center_dist,
                    ]
                    bisect.insort_left(slope_ranges, slope_range)
                    amount = 0
                    arr = []
                    # condense range of slopes
                    # https://stackoverflow.com/a/15273749
                    for start, end in slope_ranges:
                        if arr and arr[-1][1] >= start:
                            arr[-1][1] = max(arr[-1][1], end)
                        else:
                            arr.append([start, end])
                            amount += 1
                    slope_ranges = arr

            last_tile = tile_key
            last_end_pos = end_pos.copy()
        
        entity = closest[1]
        if entity is not None:
            entity.damage(damage)
            entity.textures = [_FALLBACK_SURF]


class EntityManager(object):
    
    def __init__(self: Self, 
                 player: Player, 
                 entities: dict[object, Entity]) -> None:
        self._player = player
        player._manager = self
        self._entities = entities
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
        return self._entities

    @entities.setter
    def entities(self: Self, value: dict) -> None:
        for entity in self._entities.values():
            entity._manager = None

        self._entities = value
        self._sets = {}
        for entity in value.values():
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
        if self._level is None:
            raise ValueError('Must assign level to manager')
        return self._level

    def _add_to_sets(self: Self, entity: Entity) -> None:
        key = gen_tile_key(entity._pos)
        if self._sets.get(key) is None:
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

