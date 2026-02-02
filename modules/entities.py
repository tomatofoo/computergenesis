from __future__ import annotations

import math
from numbers import Number
from numbers import Real
from typing import Self
from typing import Optional
from collections.abc import Sequence

import pygame as pg
from pygame.typing import Point

from .sound import Sound
from .weapons import Weapon
from .weapons import AmmoWeapon
from .weapons import MeleeWeapon
from .weapons import HitscanWeapon
from .weapons import MissileWeapon
from .inventory import Collectible
from .inventory import Inventory 
from .utils import SMALL
from .utils import FALLBACK_SURF
from .utils import gen_tile_key


class Entity(object):

    _TILE_OFFSETS = (
        (-1,  1), (0,  1), (1,  1),
        (-1,  0), (0,  0), (1,  0),
        (-1, -1), (0, -1), (1, -1),
    )

    def __init__(self: Self,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5, # collision width
                 height: Real=1, # collision height
                 health: Real=100,
                 climb: Real=0.2, # min distance from top to be able to climb
                 gravity: Real=0,
                 textures: list[pg.Surface]=[FALLBACK_SURF],
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        self.yaw = 0
        self.velocity2 = (0, 0)
        self.elevation = elevation
        self.elevation_velocity = 0
        self.yaw_velocity = 0
        self.textures = textures
        self._darkness = 1
        self._pos = pg.Vector2(pos)
        self._width = width # width of rect
        self._height = height
        self._climb = climb
        self._gravity = gravity
        self._attack_width = attack_width
        self._attack_height = attack_height
        if attack_width is None:
            self._attack_width = width
        if attack_height is None:
            self._attack_height = height
        self._render_width = render_width
        self._render_height = render_height
        if render_width is None:
            self._render_width = width
        if render_height is None:
            self._render_height = height
        self._health = health
        self._collisions = {
            'x': [0, 0],
            'y': [0, 0],
            'e': [0, 0],
        }
        self._manager = None
        self._remove = 0 # internal for when entity wants removal
        self._boost = pg.Vector2(0, 0)
        self._boost_friction = 0.90625
       
    @property
    def darkness(self: Self) -> float:
        return self._darkness

    @darkness.setter
    def darkness(self: Self, value: float) -> None:
        self._darkness = value
  
    @property
    def pos(self: Self) -> pg.Vector2:
        return self._pos

    @pos.setter
    def pos(self: Self, value: Point) -> None:
        old_key = self.tile_key
        self._pos = pg.Vector2(value)
        if self._manager:
            self._update_manager_sets(old_key, self.tile_key)

    @property
    def x(self: Self) -> Real:
        return self._pos[0]

    @x.setter
    def x(self: Self, value: Real) -> None:
        self._pos[0] = value

    @property
    def y(self: Self) -> Real:
        return self._pos[1]

    @y.setter
    def y(self: Self, value: Real) -> None:
        self._pos[1] = value

    # using .copy because this is used for camera
    @property
    def forward(self: Self) -> pg.Vector2:
        return self._yaw.copy()

    @property
    def right(self: Self) -> pg.Vector2:
        return self._semiplane.copy()

    @property
    def elevation(self: Self) -> Real:
        return self._elevation

    @elevation.setter
    def elevation(self: Self, value: Real) -> None:
        self._elevation = max(value, 0)

    @property
    def tile(self: Self) -> tuple[int]:
        return (int(math.floor(self._pos[0])),
                int(math.floor(self._pos[1])))

    @property
    def tile_key(self: Self) -> str:
        return gen_tile_key(self._pos)

    @property
    def vector3(self: Self) -> pg.Vector3:
        return pg.Vector3(self._pos[0], self._elevation, self._pos[1])

    @vector3.setter
    def vector3(self: Self, value: pg.Vector3) -> None:
        self._pos[0] += value[0]
        self._elevation += value[1]
        self._pos[1] += value[2]

    @property
    def yaw(self: Self) -> float:
        return self._yaw_value

    @yaw.setter
    def yaw(self: Self, value: Real) -> None:
        self._yaw_value = value
        self._yaw = pg.Vector2(0, 1).rotate(value)
        self._semiplane = pg.Vector2(-self._yaw[1], self._yaw[0])
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
    def attack_width(self: Self) -> Real:
        return self._attack_width

    @attack_width.setter
    def attack_width(self: Self, value: Real) -> None:
        self._attack_width = value

    @property
    def attack_height(self: Self) -> Real:
        return self._attack_height

    @attack_height.setter
    def attack_height(self: Self, value: Real) -> None:
        self._attack_height = value

    @property
    def render_width(self: Self) -> Real:
        return self._render_width

    @render_width.setter
    def render_width(self: Self, value: Real) -> None:
        self._render_width = value

    @property
    def render_height(self: Self) -> Real:
        return self._render_height

    @render_height.setter
    def render_height(self: Self, value: Real) -> None:
        self._render_height = value

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
    def climb(self: Self) -> Real:
        return self._climb

    @climb.setter
    def climb(self: Self, value: Real) -> None:
        self._climb = value

    @property
    def gravity(self: Self) -> Real:
        return self._gravity

    @gravity.setter
    def gravity(self: Self, value: Real) -> None:
        self._gravity = value

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
    def velocity3(self: Self) -> pg.Vector3:
        return pg.Vector3(
            self._velocity2[0],
            self._elevation_velocity,
            self._velocity2[1],
        )

    @velocity3.setter
    def velocity3(self: Self, value: pg.Vector3) -> None:
        self._velocity2 = pg.Vector2(value[0], value[2])
        self._elevation_velocity = value[1]

    @property
    def boost(self: Self) -> pg.Vector2:
        return self._boost

    @boost.setter
    def boost(self: Self, value: Point) -> None:
        self._boost = pg.Vector2(value)

    @property
    def boost_friction(self: Self) -> Real:
        return self._boost_friction

    @boost_friction.setter
    def boost_friction(self: Self, value: Real) -> None:
        self._boost_friction = value

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

    # layer of abstraction for directional sprites
    @property
    def texture(self: Self) -> pg.Surface:
        dex = int(
            # shifted by texture_angle / 2 because of segments
            (self._yaw_value
             - (self._manager._player._pos - self._pos).angle
             + self._texture_angle / 2
             - 90)
            % 360
            // self._texture_angle
        )
        return self._textures[dex]

    @property
    def collisions(self: Self) -> dict[str, tuple[int]]:
        return self._collisions

    @property
    def manager(self: Self) -> Optional[EntityManager]:
        return self._manager

    def _get_rects_around(self: Self) -> list:
        tile = pg.Vector2(math.floor(self._pos[0]), math.floor(self._pos[1]))
        tiles = []
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            tile_key = gen_tile_key(offset_tile)
            data = self._manager._level._walls._dynamic_tilemap.get(tile_key)
            if data is not None:
                obj = data.get('rect')
                if obj is None:
                    rect = pg.Rect(offset_tile[0], offset_tile[1], 1, 1)
                else:
                    rect = pg.FRect(
                        offset_tile[0] + obj[0],
                        offset_tile[1] + obj[1],
                        obj[2],
                        obj[3],
                    )
                tiles.append((
                    rect,
                    data['elevation'],
                    data['elevation'] + data['height'],
                    None,
                ))
            entities = self._manager._sets.get(tile_key)
            if entities:
                for entity in entities:
                    # the and not is cleaner than using union type
                    if (entity is not self and self._will_collide(entity)):
                        tiles.append((
                            entity.rect(),
                            entity._elevation,
                            entity.top,
                            entity,
                        ))
        return tiles

    def _will_collide(self: Self, entity: Self) -> bool:
        return not isinstance(entity, Missile | Item)

    def _dont_attack(self: Self, entity: Self) -> bool:
        return isinstance(entity, Missile | Item)

    def _update_manager_sets(self: Self, old_key: str, key: str) -> None:
        if old_key != key:
            self._manager._sets[old_key].remove(self)
            if not self._manager._sets[old_key]:
                self._manager._sets.pop(old_key)
            if not self._manager._sets.get(key):
                self._manager._sets[key] = set()
            self._manager._sets[key].add(self)
    
    def try_width(self: Self, value: Real) -> Real:
        lowest = math.inf
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            if self._elevation < top and self.top > bottom:
                left = rect.left - self._pos[0]
                right = self._pos[0] - rect.right
                if 0 < left < lowest:
                    lowest = left
                if 0 < right < lowest:
                    lowest = right
        return pg.math.clamp(lowest * 2, 0, value)

    def try_height(self: Self, value: Real) -> Real:
        lowest = math.inf
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            if entity_rect.colliderect(rect):
                height = bottom - self._elevation
                if 0 < height < lowest:
                    lowest = height
        return pg.math.clamp(lowest, 0, value)

    def melee_damage(self: Self, value: Real) -> None:
        self._health -= value
        if self._health <= 0:
            self.die()

    def hitscan_damage(self: Self, value: Real) -> None:
        self._health -= value
        if self._health <= 0:
            self.die()

    def missile_damage(self: Self, value: Real) -> None:
        self._health -= value
        if self._health <= 0:
            self.die()

    def splash_damage(self: Self, value: Real) -> None:
        self._health -= value
        if self._health <= 0:
            self.die()

    def die(self: Self) -> None:
        # TEMP TEMP TEMP TEMP
        if isinstance(self, EntityEx):
            self.state_object.textures = [[FALLBACK_SURF]]
        else:
            self.textures = [FALLBACK_SURF]

    def interaction(self: Self, entity: Self) -> None:
        pass

    def rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._width, self._width)
        rect.center = self._pos
        return rect

    def attack_rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._attack_width, self._attack_width)
        rect.center = self._pos
        return rect

    def render_rect(self: Self) -> pg.Rect:
        rect = pg.FRect(0, 0, self._render_width, self._render_width)
        rect.center = self._pos
        return rect

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        self._collisions = {
            'x': [0, 0],
            'y': [0, 0], # x/y will equal 2 when climb
            'e': [0, 0],
        }

        velocity2 = self._velocity2 + self._boost

        # Yaw
        if self._yaw_velocity:
            self.yaw += self._yaw_velocity * rel_game_speed

        # Boost
        vel_mult = self._boost_friction**rel_game_speed
        if self._boost.magnitude() >= SMALL:
            self._boost *= vel_mult
        else:
            self._boost.update(0, 0)

        # The +/-0.00001 is to account for floating-point precision errors
        self._pos[0] += velocity2[0] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                collision = 1 # if doing normal collision
                if top - self._elevation <= self._climb:
                    lowest = math.inf
                    # avoid namespace collisions by using these names
                    for r, b, t, e in self._get_rects_around():
                        if entity_rect.colliderect(r):
                            height = b - top
                            if 0 < height < lowest:
                                lowest = height
                    if lowest >= self._height:
                        collision = 0
                        self.elevation = top
                        if velocity2[0] > 0:
                            self._collisions['x'][1] = 2
                        elif velocity2[0] < 0:
                            self._collisions['x'][0] = 2
                if collision:
                    if velocity2[0] > 0:
                        entity_rect.right = rect.left - SMALL
                        self._collisions['x'][1] = 1
                    elif velocity2[0] < 0:
                        entity_rect.left = rect.right + SMALL
                        self._collisions['x'][0] = 1
                    self._pos[0] = entity_rect.centerx

        self._pos[1] += velocity2[1] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                collision = 1 # if doing normal collision
                if top - self._elevation <= self._climb:
                    lowest = math.inf
                    # avoid namespace collisions by using these names
                    for r, b, t, e in self._get_rects_around():
                        if entity_rect.colliderect(r):
                            height = b - top
                            if 0 < height < lowest:
                                lowest = height
                    if lowest >= self._height: # climb
                        collision = 0
                        self.elevation = top
                        if velocity2[1] > 0:
                            self._collisions['y'][1] = 2
                        elif velocity2[1] < 0:
                            self._collisions['y'][0] = 2
                if collision:
                    if velocity2[1] > 0:
                        entity_rect.bottom = rect.top - SMALL
                        self._collisions['y'][1] = 1
                    elif velocity2[1] < 0:
                        entity_rect.top = rect.bottom + SMALL
                        self._collisions['y'][0] = 1
                    self._pos[1] = entity_rect.centery

        # 3D collisions
        # x = v0t + 0.5at^2
        self.elevation += (
            self._elevation_velocity * rel_game_speed
            - 0.5 * self._gravity * rel_game_speed * rel_game_speed
        )
        self._elevation_velocity -= self._gravity * rel_game_speed
        if self._elevation <= 0:
            self._elevation_velocity = 0
            self._collisions['e'][0] = 1
        if self.top >= self._manager._level._ceiling_elevation:
            self.top = self._manager._level._ceiling_elevation
            self._elevation_velocity = 0
            self._collisions['e'][1] = 1
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._elevation_velocity > 0:
                    self.top = bottom
                    self._elevation_velocity = 0
                    self._collisions['e'][1] = 1
                elif self._elevation_velocity < 0:
                    self.elevation = top
                    self._elevation_velocity = 0
                    self._collisions['e'][0] = 1


class EntityExState(object):
    def __init__(self: Self,
                 textures: tuple[tuple[pg.Surface]]=((FALLBACK_SURF,),),
                 animation_time: Real=1,
                 trigger: bool=0,
                 loop: Real=-1) -> None:
        # first dimension is direction
        # second dimension is animation
        # trigger: animtaion starts when state is triggered
        # if not then animation relies on level timer
        self.textures = textures
        self._trigger = trigger
        self._loop = loop # -1 for infinite
        self._animation_time = animation_time
        self._animation_timer = 0
        self._animation_dex = 0

    @property
    def textures(self: Self) -> tuple[tuple[pg.Surface]]:
        return self._textures

    @textures.setter
    def textures(self: Self, value: tuple[tuple[pg.Surface]]) -> None:
        self._textures = value
        self._length = len(value[0])

    @property
    def animation_time(self: Self) -> Real:
        return self._animation_time

    @animation_time.setter
    def animation_time(self: Self, value: Real) -> None:
        self._animation_time = value

    @property
    def trigger(self: Self) -> bool:
        return self._trigger

    @trigger.setter
    def trigger(self: Self, value: bool) -> None:
        self._trigger = value

    @property
    def loop(self: Self) -> Real:
        return self._loop

    @loop.setter
    def loop(self: Self, value: Real) -> None:
        self._loop = value

    def ended_loop(self: Self) -> bool:
        if self._loop < 0:
            return False
        return self._animation_timer >= self._animation_time * (self._loop + 1)

    def _update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        self._animation_timer = (
            self._animation_timer + rel_game_speed
            if self._trigger else level_timer
        )
        if self._loop > -1:
            self._animation_timer = min(
                self._animation_timer,
                self._animation_time * (self._loop + 1),
            )

    def _texture(self: Self, direction_dex: int) -> int:
        animation_dex = math.floor(
            self._animation_timer
            / self._animation_time
            * self._length
        ) % self._length
        return self._textures[direction_dex][animation_dex]

    def _reset(self: Self) -> None:
        self._animation_timer = 0
        self._animation_dex = 0


# Extended Entity Class (states, animations)
class EntityEx(Entity):
    def __init__(self: Self,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5,
                 height: Real=1,
                 health: Real=100,
                 climb: Real=0.2,
                 gravity: Real=0,
                 states: dict[str, EntityExState]={'default': EntityExState()},
                 state: str='default',
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        super().__init__(
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            health=health,
            climb=climb,
            gravity=gravity,
            attack_width=attack_width,
            attack_height=attack_height,
            render_width=render_width,
            render_height=render_height,
        )
        self._state = state
        self._states = states

        del self._textures
        del self._texture_angle

    @property
    def state(self: Self) -> str:
        return self._state

    @state.setter
    def state(self: Self, value: str) -> None:
        self._state = value
        self._states[value]._reset()

    @property
    def states(self: Self) -> dict[str, EntityExState]:
        return self._states

    @states.setter
    def states(self: Self, value: dict[str, EntityExState]) -> None:
        self._states = value

    @property
    def state_object(self: Self) -> EntityExState:
        return self._states[self._state]

    @property
    def texture(self: Self) -> pg.Surface:
        state = self._states[self._state]
        texture_angle = 360 / len(state._textures)
        dex = int(
            # shifted by texture_angle / 2 because of segments
            (self._yaw_value
             - (self._manager._player._pos - self._pos).angle
             + texture_angle / 2
             - 90)
            % 360
            // texture_angle
        )
        return state._texture(dex)

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        self.state_object._update(rel_game_speed, level_timer)
        super().update(rel_game_speed, level_timer)


class Pathfinder(EntityEx): # A* pathfinder entity (imperfect path)

    _DIAGONAL = {(-1,  1), (1,  1), (-1, -1), (1, -1)}

    def __init__(self: Self,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5,
                 height: Real=1,
                 health: Real=100,
                 climb: Real=0.2,
                 gravity: Real=0,
                 states: dict[str, EntityExState]={'default': EntityExState()},
                 state: str='default',
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None,
                 straight_weight: Real=1,
                 diagonal_weight: Real=1.414,
                 elevation_weight: Real=1) -> None:

        super().__init__(
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            health=health,
            climb=climb,
            gravity=gravity,
            states=states,
            state=state,
            attack_width=attack_width,
            attack_height=attack_height,
            render_width=render_width,
            render_height=render_height,
        )
        self._weights = {
            'straight': straight_weight,
            'diagonal': diagonal_weight,
            'elevation': elevation_weight,
        }
        
        self._reset_cache()

    @property
    def straight_weight(self: Self) -> Real:
        return self._weights['straight']

    @straight_weight.setter
    def straight_weight(self: Self, value: Real) -> None:
        self._weights['straight'] = value

    @property
    def diagonal_weight(self: Self) -> Real:
        return self._weights['diagonal']

    @diagonal_weight.setter
    def diagonal_weight(self: Self, value: Real) -> None:
        self._weights['diagonal'] = value

    @property
    def elevation_weight(self: Self) -> Real:
        return self._weights['elevation']

    @elevation_weight.setter
    def elevation_weight(self: Self, value: Real) -> None:
        self._weights['elevation'] = value

    def _reset_cache(self: Self) -> None:
        self._g = {}
        self._h = {}
        self._elevations = {}

    def _get_g(self: Self, location: tuple[Point, int]) -> Number:
        g = self._g.get(location)
        if g is None:
            g = math.inf
            self._g[location] = g
        return g

    def _get_h(self: Self,
               location: tuple[Point, int],
               end: tuple[Point, int]) -> Number:
        h = self._h.get(location)
        if h is None:
            # Manhattan Distance
            # Won't give perfect path if I use this heuristic
            # But it is fast
            h = (
                (abs(location[0][0] - end[0][0])
                 + abs(location[0][1] - end[0][1]))
                * self._weights['straight']
                + abs(
                    self._get_elevation(location)
                    - self._get_elevation(end)
                ) * self._weights['elevation']
            )
            self._h[location] = h
        return h

    def _get_elevation(self: Self, location: tuple[Point, int]) -> Real:
        elevation = self._elevations.get(location)
        if elevation is None:
            tile = location[0]
            elevation = 0
            if location[1]: 
                tilemap = self._manager._level._walls._tilemap
                data = tilemap.get(gen_tile_key(tile))
                if data is not None:
                    elevation = data['height'] + data['elevation']
            self._elevations[location] = elevation
        return elevation

    def _cant(self: Self,
              data: Optional[dict],
              elevation: int,
              bottom: Real,
              climb: Real) -> bool:
        if data is None:
            if elevation:
                return True
            return False
        return (
            data['elevation'] < bottom + self._height if not elevation
            else data['elevation'] + data['height'] - bottom > climb
        )

    def _calculate(self: Self,
                   location: tuple[Point, int],
                   offset: tuple[int],
                   elevation: int,
                   climb: Real) -> tuple[tuple[Point, int], Number]:
        tile = location[0]
        neighbor = ((tile[0] + offset[0], tile[1] + offset[1]), elevation)
        bottom = self._get_elevation(location)

        # I'm aware of how weird this looks but it works
        tilemap = self._manager._level._walls._tilemap
        data = tilemap.get(gen_tile_key(neighbor[0]))
        if self._cant(data, elevation, bottom, climb):
            return (neighbor, math.inf)
        elif offset in self._DIAGONAL:
            data = tilemap.get(gen_tile_key((tile[0], tile[1] + offset[1])))
            if self._cant(data, elevation, bottom, climb):
                return (neighbor, math.inf)
            data = tilemap.get(gen_tile_key((tile[0] + offset[0], tile[1])))
            if self._cant(data, elevation, bottom, climb):
                return (neighbor, math.inf)
            weight = self._weights['diagonal']
        else:
            weight = self._weights['straight']
        difference = self._get_elevation(neighbor) - bottom
        if difference < 0:
            weight -= difference * self._weights['elevation']
        elif difference > self._climb:
            weight += (difference - self._climb) * self._weights['elevation']
        return (neighbor, weight)

    def pathfind(self: Self,
                 end: tuple[Point, int],
                 climb: Optional[Real]=None,
                 max_nodes: int=100) -> Optional[list[tuple[Point, int]]]:
        # Start
        tilemap = self._manager._level._walls._tilemap
        data = tilemap.get(self.tile_key)

        elevation = 0
        if data is not None:
            top = data['elevation'] + data['height']
            if self._elevation >= top:
                elevation = 1
        start = (self.tile, elevation)

        # Setup
        self._reset_cache()
        if climb is None:
            climb = self._climb 
        parent = {}
        visited = set()
        will = {start}
        self._g[start] = 0

        # Algorithm
        while will and len(visited) < max_nodes:
            # Find the node
            least = math.inf
            for tentative in will:
                f = self._get_g(tentative) + self._get_h(tentative, end)
                if f < least:
                    node = tentative
                    least = f
            will.remove(node)
            visited.add(node)

            if node == end:
                break

            # Check Neighbor
            for offset in self._TILE_OFFSETS:
                if offset == (0, 0):
                    continue
                for elevation in range(2): # 0 is ground; 1 is atop tile
                    neighbor, weight = self._calculate(
                        node, offset, elevation, climb,
                    )
                    tentative = self._get_g(node) + weight
                    if (tentative >= self._get_g(neighbor)
                        or neighbor in visited):
                        continue

                    self._g[neighbor] = tentative
                    parent[neighbor] = node
                    will.add(neighbor)
        else:
            return None
        
        # Trace path back
        path = []
        node = parent.get(end)
        if node is not None:
            path.append(node)
            while node != start:
                node = parent[node]
                path.append(node)
        return path


class Missile(EntityEx):
    def __init__(self: Self,
                 damage: Real,
                 blast_radius: Real=0.5,
                 width: Real=0.5,
                 height: Real=0.25,
                 states: dict[str, EntityExState]={
                     'default': EntityExState(),
                     'attack': EntityExState(loop=0, trigger=1),
                 },
                 state: str='default',
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:
        super().__init__(
            width=width,
            height=height,
            states=states,
            state=state,
            attack_width=attack_width,
            attack_height=attack_height,
            render_width=render_width,
            render_height=render_height,
        )
        self._damage = damage
        self._blast_radius = blast_radius
        self._entity = None
        self._entity_pos = (0, 0)

    @property
    def damage(self: Self) -> Real:
        return self._damage

    @damage.setter
    def damage(self: Self, value: Real) -> None:
        self._damage = value

    @property
    def blast_radius(self: Self) -> Real:
        return self._blast_radius

    @blast_radius.setter
    def blast_radius(self: Self, value: Real) -> None:
        self._blast_radius = value

    def launch(self: Self,
               entity: Optional[Entity],
               velocity: pg.Vector3,
               attack_range: Real) -> None:
        
        self.state = 'default'
        self._entity = entity
        self._entity_pos = entity._pos.copy()
        self._pos = entity._pos.copy()
        self.centere = entity.centere
        entity._manager.add_entity(self)
        self._range = attack_range
        self.yaw = entity._yaw_value
        self.velocity3 = velocity

    def attack(self: Self, entity: Optional[Entity]=None) -> None:
        self.velocity3 = (0, 0, 0)
        self.state = 'attack'
        if entity is not None and entity._health > 0:
            entity.missile_damage(self._damage)
        
        tile = pg.Vector2(math.floor(self._pos[0]), math.floor(self._pos[1]))
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            entities = self._manager._sets.get(gen_tile_key(offset_tile))
            if entities is not None:
                for entity in entities:
                    dist = entity._pos.distance_to(entity._pos)
                    if dist < self._blast_radius:
                        entity.splash_damage(
                            dist / self._blast_radius * self._damage / 2
                        )

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        # has to be at start
        self.state_object._update(rel_game_speed, level_timer)
        
        if ((self._state == 'attack' and self.state_object.ended_loop())
            or self._pos.distance_to(self._entity_pos) > self._range):
            self._remove = 1

        if self._state != 'attack':
            self._pos += self._velocity2 * rel_game_speed
            self._elevation += self._elevation_velocity * rel_game_speed
            for rect, bottom, top, entity in self._get_rects_around():
                if self._elevation < top and self.top > bottom:
                    if entity is None:
                        if self.rect().colliderect(rect):
                            self.attack()
                    elif self.attack_rect().colliderect(entity.attack_rect()):
                        self.attack(entity)
            if self._elevation <= 0: # has to be in != attack block
                self.attack()


class Item(EntityEx):
    def __init__(self: Self,
                 obj: object, 
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5,
                 height: Real=1,
                 gravity: Real=0,
                 loop: Real=-1,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        super().__init__(
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            gravity=gravity,
            render_width=render_width,
            render_height=render_height,
        )
        self._obj = obj
        self._loop = loop
        self._update_states()

    @property
    def loop(self: Self) -> Real:
        return self._loop

    @loop.setter
    def loop(self: Self, value: Real) -> None:
        self._loop = value
        self._states['default']._loop = value

    def _update_states(self: Self) -> None:
        self._states = {
            'default': EntityExState(
                textures=(self._obj._textures['ground'],),
                animation_time=self._obj._animation_times['ground'],
                loop=self._loop,
            ),
        }

    def _add_to_inventory(self: Self, inventory: Inventory) -> bool:
        return False

    def interaction(self: Self, entity: Entity) -> None:
        try: 
            self._remove = self._add_to_inventory(entity._inventory)
            if self._remove:
                sound = self._obj._sounds['pickup']
                if sound is not None:
                    sound.play(pos=entity.vector3)
        except AttributeError:
            pass


class CollectibleItem(Item):
    def __init__(self: Self,
                 collectible: Collectible, 
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5,
                 height: Real=1,
                 gravity: Real=0,
                 loop: Real=-1,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        super().__init__(
            obj=collectible,
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            gravity=gravity,
            loop=loop,
            render_width=render_width,
            render_height=render_height,
        )

    @property
    def collectible(self: Self) -> Collectible:
        return self._obj

    @collectible.setter
    def collectible(self: Self, value: Collectible) -> None: 
        self._obj = value
        self._update_states()

    def _add_to_inventory(self: Self, inventory: Inventory) -> bool:
        return inventory.add_collectible(self._obj)


class WeaponItem(Item):
    def __init__(self: Self,
                 weapon: Weapon,
                 number: int=0,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.5,
                 height: Real=1,
                 gravity: Real=0,
                 loop: Real=-1,
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        super().__init__(
            obj=weapon,
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            gravity=gravity,
            loop=loop,
            render_width=render_width,
            render_height=render_height,
        )
        self._number = number

    @property
    def weapon(self: Self) -> Weapon:
        return self._obj

    @weapon.setter
    def weapon(self: Self, value: Weapon) -> None: 
        self._obj = value
        self._update_states()

    @property
    def number(self: Self) -> int:
        return self._number

    @number.setter
    def number(self: Self, value: int) -> None:
        self._number = value

    def _add_to_inventory(self: Self, inventory: Inventory) -> bool:
        return inventory.add_weapon(self._obj, self._number)


class Player(Entity):
    def __init__(self: Self,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.4,
                 height: Real=0.6,
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 climb: Real=0.2,
                 gravity: Real=0.004,
                 foi: Real=60, # Field of Interaction
                 roi: Real=0.25, # Range of Interaction
                 foa: Real=60, # Field of Attack
                 roa: Real=0.75, # Radius of Autoaim (for missiles)
                 inventory: Inventory=Inventory(),
                 weapon: Optional[Weapon]=None) -> None:

        super().__init__(
            pos=pos,
            elevation=elevation,
            width=width,
            height=height,
            attack_width=attack_width,
            attack_height=attack_height,
            climb=climb,
            gravity=gravity,
        )

        self._climbing = 0

        self._forward_velocity = pg.Vector2(0, 0)
        self._right_velocity = pg.Vector2(0, 0)
        self._friction = 0.90625 # number used in doom
        
        # Camera settings
        self._settings = {
            'camera_offset': 0,
            'headbob_strength': 0,
            'headbob_frequency': 0,
            'weaponbob_strength': 0,
            'weaponbob_frequency': 0,
            'weapon_pos': (0, 0),
            'climb_speed': 0,
        }
        self._render_elevation = (
            self._elevation + self._settings['camera_offset']
        )
        
        # Interaction Stuff
        self._foi = foi
        self._roi = roi # Range of Interaction
        
        # Weapon / Inventory Stuff
        self._inventory = inventory
        self._foa = foa
        self._roa = roa
        self._weapon = weapon
        self._weapon_surf = pg.Surface((0, 0))
        self._weapon_attacking = 0
        self._weapon_attack_timer = 0
        self._weapon_cooldown_timer = 0 # time until next available shot
        self._render_weapon_pos = list(self._settings['weapon_pos'])
        
        # delete variables we don't need from entity init
        del self._textures
        del self._texture_angle
        del self._darkness
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
        return pg.Vector3(self._pos[0], self._render_elevation, self._pos[1])

    @property
    def velocity2(self: Self) -> pg.Vector2:
        return self._velocity2

    @velocity2.setter
    def velocity2(self: Self, value: Point) -> None:
        self._velocity2 = pg.Vector2(value)
        self._forward_velocity = self._velocity2.project(self._yaw)
        self._right_velocity = self._velocity2.project(self._semiplane)

    @property
    def friction(self: Self) -> Real:
        return self._fricion

    @friction.setter
    def friction(self: Self, value: Real) -> None:
        self._friction = value

    @property
    def inventory(self: Self) -> Inventory:
        return self._inventory

    @inventory.setter
    def inventory(self: Self, value: Inventory) -> None:
        self._inventory = value

    @property
    def weapon(self: Self) -> Optional[Weapon]:
        return self._weapon
    
    @weapon.setter
    def weapon(self: Self, value: Optional[Weapon]) -> None:
        self._weapon = value
        self._weapon_attacking = 0
        self._weapon_attack_timer = 0
    
    @property
    def foi(self: Self) -> Real:
        return self._foi

    @foi.setter
    def foi(self: Self, value: Real) -> None:
        self._foi = value

    @property
    def roi(self: Self) -> Real:
        return self._roi

    @roi.setter
    def roi(self: Self, value: Real) -> None:
        self._roi = value

    @property
    def foa(self: Self) -> Real:
        return self._foa

    @foa.setter
    def foa(self: Self, value: Real) -> None:
        self._foa = value

    @property
    def roa(self: Self) -> Real:
        return self._roa

    @roa.setter
    def roa(self: Self, value: Real) -> None:
        self._roa = value

    def update(self: Self,
               rel_game_speed: Real,
               level_timer: Real,
               forward: Real,
               right: Real,
               yaw: Real,
               up: Optional[Real]=None) -> None:

        self._collisions = {
            'x': [0, 0],
            'y': [0, 0],
            'e': [0, 0],
        }
        
        # Velocities
        self._yaw_velocity = yaw
        if forward:
            self._forward_velocity.update(self._yaw * forward)
        if right:
            self._right_velocity.update(self._semiplane * right)
        self._velocity2 = self._forward_velocity + self._right_velocity
        speed = self._velocity2.magnitude()
        bob_update = speed >= SMALL
        if up is not None:
            self._elevation_velocity = up
        
        # UPDATE
        super().update(rel_game_speed, level_timer)
        
        # Friction
        vel_mult = self._friction**rel_game_speed
        if self._forward_velocity.magnitude() >= SMALL:
            self._forward_velocity *= vel_mult
        else:
            self._forward_velocity.update(0, 0)
        if self._right_velocity.magnitude() >= SMALL:
            self._right_velocity *= vel_mult
        else:
            self._right_velocity.update(0, 0)

        # test if climbing
        if 2 in self._collisions['x'] or 2 in self._collisions['y']:
            self._climbing = 1

        # climbing animation / headbob
        factor = min(speed * 20, 2)
        elevation = self._elevation + self._settings['camera_offset']
        if self._climbing:
            difference = elevation - self._render_elevation
            mult = (1 - (1 - self._settings['climb_speed'])**rel_game_speed)
            self._render_elevation += difference * mult
            if difference < SMALL:
                self._climbing = 0
        else:
            self._render_elevation = elevation
            if (bob_update # allowing stuff above and below player on purpose
                and (self._collisions['e'][0] or self._collisions['e'][1])):
                self._render_elevation += (
                    math.sin(level_timer * self._settings['headbob_frequency'])
                    * self._settings['headbob_strength']
                    * factor
                )
        # Weapon update
        if self._weapon is not None:
            self._weapon_cooldown_timer -= rel_game_speed
            if bob_update:
                self._render_weapon_pos = [
                    self._settings['weapon_pos'][0] + (
                        math.sin(
                            level_timer * self._settings['weaponbob_frequency']
                        )
                        * self._settings['weaponbob_strength']
                        * factor
                    ),
                    self._settings['weapon_pos'][1] + abs(
                        math.cos(
                            level_timer * self._settings['weaponbob_frequency']
                        )
                        * self._settings['weaponbob_strength']
                        * factor / 2
                    ),
                ]
            if self._weapon_attacking:
                animation_time = self._weapon._animation_times['attack']
                self._weapon_attack_timer += rel_game_speed
                dex = math.floor(
                    self._weapon_attack_timer
                    / animation_time
                    * len(self._weapon._textures['attack'])
                )
                if self._weapon_attack_timer < animation_time:
                    self._weapon_surf = self._weapon._textures['attack'][dex]
                else:
                    self._weapon_attacking = 0
                    self._weapon_attack_timer = 0
            else:
                length = len(self._weapon._textures['hold'])
                dex = math.floor(
                    level_timer
                    / self._weapon._animation_times['hold']
                    * length
                ) % length
                self._weapon_surf = self._weapon._textures['hold'][dex]

    def interact(self: Self, precision: int=100) -> bool:
        # returns true if interacted with something
        # can interact through walls btw
        ray = self._yaw.normalize()

        end_pos = list(self._pos)
        last_end_pos = end_pos.copy()
        slope = ray[1] / ray[0] if ray[0] else math.inf
        tile = [math.floor(end_pos[0]), math.floor(end_pos[1])]
        tile_key = gen_tile_key(tile)
        last_tile = tile
        dir = (ray[0] > 0, ray[1] > 0)
        # step for tile (for each displacement)
        step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
        step_y = dir[1] * 2 - 1 
        dist = 0 # equals depth when ray is in perfet center
        tilemap = self._manager._level._walls._tilemap

        closest = (math.inf, None)
        tangent = math.tan(math.radians(self._foi) / 2)
        top = self.top
        vector = self.vector3

        while dist < self._roi:
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
                side = 1
            else:
                tile[1] += step_y
                end_pos[0] += disp_y / slope if slope else math.inf
                end_pos[1] += disp_y
                dist += len_y
                side = 0
            
            # account for entities partially in the tile but not in set
            # i think it should work for entities that are at most 2 units wide
            # since TILE_OFFSETS is 3x3
            entities = set()
            for offset in self._TILE_OFFSETS:
                tile_key = gen_tile_key(
                    (last_tile[0] + offset[0], last_tile[1] + offset[1]),
                )
                tentative = self._manager._sets.get(tile_key)
                if tentative != None:
                    entities |= tentative
                
            if entities:
                # makes sure it doesn't go past range
                if dist >= self._roi:
                    end_pos = self._pos + ray * self._roi
                for entity in entities:
                    # Slope calculation (uses lowest magnitude slope)
                    entity_slope = 0
                    entity_top = entity.top
                    entity_dist = self._pos.distance_to(entity._pos)
                    if self._elevation > entity_top:
                        entity_slope = (
                            (entity_top - self._elevation) / entity_dist
                        ) if entity_dist else -math.inf
                    elif top < entity._elevation:
                        entity_slope = (
                            (entity._elevation - top) / entity_dist
                        ) if entity_dist else math.inf
                    # Checks
                    if entity_slope < -tangent or entity_slope > tangent:
                        continue
                    rect = entity.rect()
                    rect.update(
                        rect[0] * precision,
                        rect[1] * precision,
                        rect[2] * precision,
                        rect[3] * precision,
                    )
                    if rect.clipline(
                        last_end_pos[0] * precision,
                        last_end_pos[1] * precision,
                        end_pos[0] * precision,
                        end_pos[1] * precision,
                    ):
                        entity_dist = vector.distance_to(entity.vector3)
                        if entity_dist < closest[0]:
                            closest = (entity_dist, entity)

            tile_key = gen_tile_key(tile)
            special = self._manager._level._specials.get(tile_key)
            if special is not None:
                data = tilemap[tile_key]
                if dist:
                    bottom_slope = (data['height'] - midheight) / dist
                    top_slope = (
                        (data['height'] + data['elevation'] - midheight) / dist
                    )
                elif data['height'] <= midheight <= data['elevation']:
                    bottom_slope = 0
                    top_slope = 0
                if bottom_slope >= -tangent and top_slope <= tangent:
                    # kinda slick boolean operation to determine side
                    special.interaction(self, side + (not dir[not side]) * 2)
                    return True
            last_tile = tile
            last_end_pos = end_pos.copy()

        if closest[1] is not None:
            closest[1].interaction(self)
            return True
        return False

    def attack(self: Self) -> int:
        # return values
        # -1: can't attack
        # 0: can attack but can't hit
        # 1: can attack and did hit

        if self._weapon is None:
            return 0
        elif self._weapon_cooldown_timer > 0:
            return 0
        elif (isinstance(self._weapon, AmmoWeapon | MeleeWeapon)
              and self._inventory._weapons[self._weapon] <= 0):
            return 0
        else:
            sound = self._weapon._sounds['attack']
            if sound is not None:
                sound.play()
            self._weapon_attacking = 1
            self._weapon_cooldown_timer = self._weapon._cooldown
            if isinstance(self._weapon, MeleeWeapon):
                if self._weapon.autoaim_attack(self, self._foa):
                    self._inventory.change_weapon_number(self._weapon, -1)
                    return 2
                return 1
            elif isinstance(self._weapon, HitscanWeapon):
                self._inventory.change_weapon_number(self._weapon, -1)
                return self._weapon.autoaim_attack(self, self._foa) + 1
            elif isinstance(self._weapon, MissileWeapon):
                self._inventory.change_weapon_number(self._weapon, -1)
                return self._weapon.autoaim_attack(
                    self,
                    self._foa,
                    self._roa,
                ) + 1


class EntityManager(object):
    
    def __init__(self: Self, player: Player, entities: set[Entity]=set()) -> None:
        self._player = player
        player._manager = self
        self._entities = entities
        self._sets = {}
        for entity in entities:
            self._add_to_sets(entity)
            entity._manager = self
        self._level = None

        # _sets is a dictionary where each key is a tile position and the value
        # is the set of all entities in that position

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player) -> None:
        self._player = value

    @property
    def entities(self: Self) -> set:
        return self._entities

    @entities.setter
    def entities(self: Self, value: set) -> None:
        for entity in self._entities:
            entity._manager = None

        self._entities = value
        self._sets = {}
        for entity in value:
            self._add_to_sets(entity)
            entity._manager = self

    def _add_to_sets(self: Self, entity: Entity) -> None:
        key = gen_tile_key(entity._pos)
        if self._sets.get(key) is None:
            self._sets[key] = set()
        self._sets[key].add(entity)

    def add_entity(self: Self, entity: Entity) -> None:
        self._entities.add(entity)
        self._add_to_sets(entity)
        entity._manager = self

    def remove_entity(self: Self, entity: Entity) -> None:
        key = gen_tile_key(entity._pos)
        self._sets[key].remove(entity) # remove from set
        entity._manager = None
        self._entities.remove(entity)

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        remove = set()
        for entity in self._entities:
            old_key = gen_tile_key(entity._pos)
            entity.update(rel_game_speed, level_timer)
            key = gen_tile_key(entity._pos)
            entity._update_manager_sets(old_key, key)
            if entity._remove:
                remove.add(entity)
        for entity in remove:
            self.remove_entity(entity)


# CUSTOM

