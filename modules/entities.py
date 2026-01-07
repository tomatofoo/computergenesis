from __future__ import annotations

import math
import copy
import bisect
from numbers import Real
from typing import Self
from typing import Optional
from collections.abc import Sequence

import pygame as pg
from pygame.typing import Point

from modules.weapons import Weapon
from modules.weapons import AmmoWeapon
from modules.weapons import MeleeWeapon
from modules.weapons import HitscanWeapon
from modules.weapons import MissileWeapon
from modules.utils import FALLBACK_SURF
from modules.utils import gen_tile_key


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
        self._glowing = 0
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
        self._manager = None
        self._remove = 0 # internal for when entity wants removal
        self._dont_collide = set() # internal for no collision
       
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
    def tile(self: Self) -> tuple[int]:
        return (int(math.floor(self._pos[0])),
                int(math.floor(self._pos[1])))

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
    def manager(self: Self) -> EntityManager:
        if self._manager is None:
            raise ValueError('Must assign manager to this entity')
        return self._manager

    def _get_rects_around(self: Self) -> list:
        tile = pg.Vector2(math.floor(self._pos[0]), math.floor(self._pos[1]))
        tiles = []
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            tile_key = gen_tile_key(offset_tile)
            walls = self._manager._level._walls
            data = walls._tilemap.get(tile_key)
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
                    # referencing Missile before declaration works somehow
                    if (entity not in self._dont_collide
                        and self not in entity._dont_collide
                        and not isinstance(entity, Missile)):
                        tiles.append((
                            entity.rect(),
                            entity._elevation,
                            entity.top,
                            entity,
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
        if self._yaw_velocity:
            self.yaw += self._yaw_velocity * rel_game_speed
        
        self._pos[0] += self._velocity2[0] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2[0] > 0:
                        entity_rect.right = rect.left
                    elif self._velocity2[0] < 0:
                        entity_rect.left = rect.right
                    self._pos[0] = entity_rect.centerx
                else: # climbing up
                    self.elevation = top

        self._pos[1] += self._velocity2[1] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2[1] > 0:
                        entity_rect.bottom = rect.top
                    elif self._velocity2[1] < 0:
                        entity_rect.top = rect.bottom
                    self._pos[1] = entity_rect.centery
                else: # climbing up
                    self.elevation = top

        # 3D collisions
        self.elevation += self._elevation_velocity * rel_game_speed
        self._elevation_velocity -= self._gravity * rel_game_speed
        if self._elevation <= 0:
            self._elevation_velocity = 0
        if self.top >= self._manager._level._ceiling_elevation:
            self.top = self._manager._level._ceiling_elevation
            self._elevation_velocity = 0
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._elevation_velocity > 0:
                    self.top = bottom
                    self._elevation_velocity = 0
                elif self._elevation_velocity < 0:
                    self.elevation = top
                    self._elevation_velocity = 0


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


class Missile(EntityEx):
    def __init__(self: Self,
                 damage: Real,
                 blast_radius: Real=0.5,
                 width: Real=0.5,
                 height: Real=0.25,
                 states: dict[str, EntityExState]={
                     'default': EntityExState(),
                     'attack': EntityExState(),
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
                    elif not isinstance(entity, Missile):
                        if (entity is not self._entity
                            and entity is not self
                            and self.attack_rect().colliderect(rect)):
                            self.attack(entity)
            if self._elevation <= 0: # has to be in != attack block
                self.attack()


class Player(Entity):
    def __init__(self: Self,
                 pos: Point=(0, 0),
                 elevation: Real=0,
                 width: Real=0.4,
                 height: Real=0.75,
                 attack_width: Optional[Real]=None,
                 attack_height: Optional[Real]=None,
                 climb: Real=0.2,
                 gravity: Real=0.004,
                 foa: Real=60, # Field of Attack
                 roa: Real=0.75, # Radius of Autoaim (for missiles)
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

        # Weapon Stuff
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
    def weapon(self: Self) -> Optional[Weapon]:
        return self._weapon
    
    @weapon.setter
    def weapon(self: Self, value: Optional[Weapon]) -> None:
        self._weapon = value
        self._weapon_attacking = 0
        self._weapon_attack_timer = 0

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

        if forward:
            self._forward_velocity.update(self._yaw * forward)
        if right:
            self._right_velocity.update(self._semiplane * right)
        
        self._yaw_velocity = yaw

        vel_mult = 0.90625**rel_game_speed # number used in Doom
        bob_update = 0
        if self._forward_velocity.magnitude() >= 0.001:
            bob_update = 1
            self._forward_velocity *= vel_mult
        else:
            self._forward_velocity.update(0, 0)
        if self._right_velocity.magnitude() >= 0.001:
            bob_update = 1
            self._right_velocity *= vel_mult
        else:
            self._right_velocity.update(0, 0)
        
        self._velocity2 = self._forward_velocity + self._right_velocity

        if self._yaw_velocity:
            self.yaw += self._yaw_velocity * rel_game_speed

        self._pos[0] += self._velocity2[0] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2[0] > 0:
                        entity_rect.right = rect.left
                    elif self._velocity2[0] < 0:
                        entity_rect.left = rect.right
                    self._pos[0] = entity_rect.centerx
                else: # climbing up
                    self.elevation = top
                    self._climbing = 1

        self._pos[1] += self._velocity2[1] * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2[1] > 0:
                        entity_rect.bottom = rect.top
                    elif self._velocity2[1] < 0:
                        entity_rect.top = rect.bottom
                    self._pos[1] = entity_rect.centery
                else: # climbing up
                    self.elevation = top
                    self._climbing = 1
        
        # 3D collisions
        self._elevation_velocity -= self._gravity * rel_game_speed
        if up is not None:
            self._elevation_velocity = up
        self.elevation += self._elevation_velocity * rel_game_speed
        if self._elevation <= 0:
            self._elevation_velocity = 0
        if self.top >= self._manager._level._ceiling_elevation:
            self.top = self._manager._level._ceiling_elevation
            self._elevation_velocity = 0
        entity_rect = self.rect()
        for rect, bottom, top, entity in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._elevation_velocity > 0:
                    self.top = bottom
                    self._elevation_velocity = 0
                elif self._elevation_velocity < 0:
                    self.elevation = top
                    self._elevation_velocity = 0
        
        # climbing animation / headbob
        factor = min(self._velocity2.magnitude() * 20, 2)
        elevation = self._elevation + self._settings['camera_offset']
        if self._climbing:
            difference = elevation - self._render_elevation
            mult = (1 - (1 - self._settings['climb_speed'])**rel_game_speed)
            self._render_elevation += difference * mult
            if difference < 0.001:
                self._climbing = 0
        else:
            self._render_elevation = elevation
            # yes it will headbob while falling but I'm okay with that
            if bob_update:
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

    def attack(self: Self) -> int:
        # return values
        # -1: can't attack
        # 0: can attack but can't hit
        # 1: can attack and did hit

        if self._weapon is None:
            return 0
        elif self._weapon_cooldown_timer > 0:
            return 0
        elif isinstance(self._weapon, AmmoWeapon) and self._weapon._ammo <= 0:
            return 0
        else:
            sound = self._weapon._sounds['attack']
            if sound is not None:
                sound.play()
            self._weapon_attacking = 1
            self._weapon_cooldown_timer = self._weapon._cooldown
            if isinstance(self._weapon, MeleeWeapon):
                if self.melee_attack(
                    damage=self._weapon._damage,
                    attack_range=self._weapon._range,
                    foa=self._foa,
                ):
                    self._weapon._durability -= 1
                    return 2
                return 1
            elif isinstance(self._weapon, HitscanWeapon):
                self._weapon._ammo -= 1
                return self.hitscan_attack(
                    damage=self._weapon._damage,
                    attack_range=self._weapon._range,
                    foa=self._foa,
                ) + 1
            elif isinstance(self._weapon, MissileWeapon):
                self._weapon._ammo -= 1
                return self.missile_attack(
                    missile=self._weapon._missile,
                    attack_range=self._weapon._range,
                    foa=self._foa,
                    roa=self._roa,
                    speed=self._weapon._speed,
                ) + 1

    def _hitscan(self: Self,
                 attack_range: Real,
                 foa: Real,
                 precision: int=100,
                 roa: Real=0) -> Optional[Entity]:
        # if roa is 0 then use normal hitscanning
        # else is missile hitscanning; roa is radius for vertical autoaim

        # NOTE: this algorithm allows attacking through 
        # vertical corners of walls
        # e.g floor and wall together create a corner

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

        # ranges of slopes of walls relative to player
        # this determines if a shot will hit a wall
        tangent = math.tan(math.radians(foa) / 2)
        slope_range = 0
        slope_ranges = []
        amount = 0
        midheight = self.centere
        vector = self.vector3
        
        could_hit = 0 # when roa is supplied

        # keep on changing end_pos until hitting a wall (DDA)
        while dist < attack_range and dist < closest[0]:
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
            
            if slope_range:
                if back[0]:
                    slope_range[0] = max(
                        (bottom - midheight) / dist, -tangent,
                    )
                if back[1]:
                    slope_range[1] = min(
                        (top - midheight) / dist, tangent,
                    )
                # ^ less lines than putting inside function
                if slope_range[0] < slope_range[1]:
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
                for entity in entities:
                    entity_dist = self._pos.distance_to(entity._pos)
                    if (entity._health <= 0
                        or not entity_dist
                        or isinstance(entity, Missile)):
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
                    
                    if dist >= attack_range:
                        end_pos = self._pos + ray * attack_range
                    rect = entity.attack_rect()
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
                        if not roa or could_hit:
                            if entity_dist < closest[0]:
                                closest = (entity_dist, entity)
                        else:
                            closest = (entity_dist, entity)
                            could_hit = 1

                    if roa and not could_hit:
                        entity_dist = vector.distance_to(entity.vector3)
                        if (entity_dist < closest[0]
                            and entity._pos.distance_to(end_pos) < roa):
                            closest = (entity_dist, entity)

            tile_key = gen_tile_key(tile)
            data = tilemap.get(tile_key)
            # allows shooting through semitiles
            if data is not None and data.get('semitile') is None:
                bottom = data['elevation']
                top = bottom + data['height']
                back = [midheight < bottom, midheight > top]
                # ^ use back of tile for slope rather than front (bottom, top)
                slope_range = [None, None]
                if not back[0]:
                    slope_range[0] = max(
                        (bottom - midheight) / dist, -tangent,
                    )
                if not back[1]:
                    slope_range[1] = min(
                        (top - midheight) / dist, tangent,
                    )
                # you either use the back or front of the tile for the slope

            last_tile = tile
            last_end_pos = end_pos.copy()

        return (closest[1], could_hit) if roa else closest[1]

    def melee_attack(self: Self,
                     damage: Real,
                     attack_range: Real,
                     foa: Real,
                     precision: int=100) -> bool:
        entity = self._hitscan(attack_range, foa, precision)
        if entity is not None:
            entity.melee_damage(damage)
            return True
        return False
        
    def hitscan_attack(self: Self,
                       damage: Real,
                       attack_range: Real,
                       foa: Real,
                       precision: int=100) -> bool:
        entity = self._hitscan(attack_range, foa, precision)
        if entity is not None:
            entity.hitscan_damage(damage)
            return True
        return False

    def missile_attack(self: Self,
                       missile: Missile,
                       attack_range: Real,
                       foa: Real,
                       roa: Real, # radius of autoaim
                       speed: Real,
                       precision: int=100) -> None:
        # unlike melee and hitscan, missile attack will return true if a hit is
        # predicted (not guaranteed)
        # (i.e. the monstor could move and it wouldn't hit)
        entity, could_hit = self._hitscan(
            attack_range,
            foa,
            precision,
            roa,
        )
        missile = copy.deepcopy(missile)
        if entity is None:
            vector = pg.Vector3(self._yaw[0], 0, self._yaw[1])
        else:
            vector = pg.Vector3(
                0,
                entity.centere - self.centere,
                self._pos.distance_to(entity._pos),
            ).rotate_y(-self._yaw_value)
        missile.launch(
            self,
            vector.normalize() * speed,
            attack_range,
        )
        return could_hit
        

class EntityManager(object):
    
    def __init__(self: Self, player: Player, entities: set[Entity]) -> None:
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

