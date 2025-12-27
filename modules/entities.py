import math
import bisect
from numbers import Real
from typing import Self
from typing import Optional

import pygame as pg
from pygame.typing import Point

from modules.weapons import Weapon
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
                 width: Real=0.5,
                 height: Real=1,
                 health: Real=100,
                 climb: Real=0.2, # min distance from top to be able to climb
                 gravity: Real=0,
                 textures: list[pg.Surface]=[FALLBACK_SURF],
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:

        self.yaw = 0
        self.velocity2 = (0, 0)
        self.elevation = 0
        self.elevation_velocity = 0
        self.yaw_velocity = 0
        self.textures = textures
        self._glowing = 0
        self._pos = pg.Vector2(pos)
        self._width = width # width of rect
        self._height = height
        self._render_width = render_width
        self._render_height = render_height
        self._climb = climb
        self._gravity = gravity
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
        tile = pg.Vector2(math.floor(self._pos.x), math.floor(self._pos.y))
        tiles = []
        for offset in self._TILE_OFFSETS:
            offset_tile = tile + offset
            tile_key = gen_tile_key(offset_tile)
            walls = self._manager._level._walls
            data = walls._tilemap.get(tile_key)
            if data is not None:
                obj = data.get('rect')
                if obj is None:
                    rect = pg.Rect(offset_tile.x, offset_tile.y, 1, 1)
                else:
                    rect = pg.FRect(
                        (offset_tile.x + obj[0], offset_tile.y + obj[1]),
                        (obj[2], obj[3]),
                    )
                tiles.append((
                    rect,
                    data['elevation'],
                    data['elevation'] + data['height'],
                ))
            entities = self._manager._sets.get(tile_key)
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
                if top - self._elevation > self._climb:
                    if self._velocity2.x > 0:
                        entity_rect.right = rect.left
                    elif self._velocity2.x < 0:
                        entity_rect.left = rect.right
                    self._pos.x = entity_rect.centerx
                else: # climbing up
                    self.elevation = top

        self._pos.y += self._velocity2.y * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2.y > 0:
                        entity_rect.bottom = rect.top
                    elif self._velocity2.y < 0:
                        entity_rect.top = rect.bottom
                    self._pos.y = entity_rect.centery
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
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if self._elevation_velocity > 0:
                    self.top = bottom
                    self._elevation_velocity = 0
                elif self._elevation_velocity < 0:
                    self.elevation = top
                    self._elevation_velocity = 0


class Player(Entity):
    def __init__(self: Self,
                 pos: Point=(0, 0),
                 width: Real=0.5,
                 height: Real=1,
                 climb: Real=0.2,
                 gravity: Real=0.004,
                 foa: Real=60, # Field of Attack
                 weapon: Optional[Weapon]=None) -> None:

        super().__init__(
            pos=pos,
            width=width,
            height=height,
            climb=climb,
            gravity=gravity,
        )

        self._climbing = 0

        self._forward_velocity = pg.Vector2(0, 0)
        self._right_velocity = pg.Vector2(0, 0)
        # offset for camera's viewpoint
        self._camera_offset = 0.5
        self._render_elevation = self._elevation + self._camera_offset
        
        self._settings = {
            'headbob_strength': 0,
            'headbob_frequency': 0,
            'weaponbob_strength': 0,
            'weaponbob_frequency': 0,
            'weapon_pos': (0, 0),
            'climb_speed': 0,
        }
        # Weapon Stuff
        self._foa = foa
        self._weapon = weapon
        self._weapon_surf = pg.Surface((0, 0))
        self._weapon_attacking = 0
        self._weapon_attack_time = 0
        self._weapon_cooldown_time = 0 # time until next available shot
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
        return pg.Vector3(self._pos.x, self._render_elevation, self._pos.y)

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

        self._pos.x += self._velocity2.x * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2.x > 0:
                        entity_rect.right = rect.left
                    elif self._velocity2.x < 0:
                        entity_rect.left = rect.right
                    self._pos.x = entity_rect.centerx
                else: # climbing up
                    self.elevation = top
                    self._climbing = 1

        self._pos.y += self._velocity2.y * rel_game_speed
        entity_rect = self.rect()
        for rect, bottom, top in self._get_rects_around():
            vertical = self._elevation < top and self.top > bottom
            horizontal = entity_rect.colliderect(rect)
            if vertical and horizontal:
                if top - self._elevation > self._climb:
                    if self._velocity2.y > 0:
                        entity_rect.bottom = rect.top
                    elif self._velocity2.y < 0:
                        entity_rect.top = rect.bottom
                    self._pos.y = entity_rect.centery
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
        for rect, bottom, top in self._get_rects_around():
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
        mag = self._velocity2.magnitude()
        elevation = self._elevation + self._camera_offset
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
                    * min(mag * 20, 2)
                )
        # Weapon update
        if self._weapon is not None:
            self._weapon_cooldown_time -= rel_game_speed
            if bob_update:
                self._render_weapon_pos = [
                    self._settings['weapon_pos'][0] + (
                        math.sin(
                            level_timer * self._settings['weaponbob_frequency']
                        )
                        * self._settings['weaponbob_strength']
                        * min(mag * 20, 2)
                    ),
                    self._settings['weapon_pos'][1] + abs(
                        math.cos(
                            level_timer * self._settings['weaponbob_frequency']
                        )
                        * self._settings['weaponbob_strength']
                        * min(mag * 20, 2) / 2
                    ),
                ]
            if self._weapon_attacking:
                animation_time = self._weapon._animation_times['attack']
                self._weapon_attack_time += rel_game_speed
                dex = math.floor(
                    self._weapon_attack_time
                    / animation_time
                    * len(self._weapon._textures['attack'])
                )
                if self._weapon_attack_time < animation_time:
                    self._weapon_surf = self._weapon._textures['attack'][dex]
                else:
                    self._weapon_attacking = 0
                    self._weapon_attack_time = 0
            else:
                length = len(self._weapon._textures['hold'])
                dex = math.floor(
                    level_timer
                    / self._weapon._animation_times['hold']
                    * length
                )
                dex %= length
                self._weapon_surf = self._weapon._textures['hold'][dex]

    def attack(self: Self) -> bool:
        if self._weapon is not None and self._weapon_cooldown_time <= 0:
            self._weapon_attacking = 1
            self._weapon_cooldown_time = self._weapon._cooldown
            if isinstance(self._weapon, MeleeWeapon):
                self.melee_attack(
                    damage=self._weapon._damage,
                    attack_range=self._wepaon._range,
                    foa=self._foa,
                )
            elif isinstance(self._weapon, HitscanWeapon):
                self.hitscan_attack(
                    damage=self._weapon._damage,
                    attack_range=self._weapon._range,
                    foa=self._foa,
                )
                self._weapon._ammo -= 1
            elif isinstance(self._weapon, MissileWeapon):
                self.missile_attack(
                    damage=self._weapon._damage,
                    attack_range=self._wepaon._range,
                    foa=self._foa,
                )
                self._weapon._ammo -= 1
            return True
        return False

    def melee_attack(self: Self,
                     damage: Real,
                     attack_range: Real,
                     foa: Real,
                     precision: int=2) -> None:
        pass
        
    def hitscan_attack(self: Self,
                       damage: Real,
                       attack_range: Real,
                       foa: Real,
                       precision: int=2) -> None:

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
        # this determines if a shot will hit a wall
        tangent = math.tan(math.radians(foa) / 2)
        slope_ranges = []
        amount = 0
        midheight = self.centere
        vector = self.vector3

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

            entities = self._manager._sets.get(last_tile)
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
            # allows shooting through semitiles
            if data is not None and data.get('semitile') is None:
                center = (tile[0] + 0.5, tile[1] + 0.5)
                center_dist = self._pos.distance_to(center)
                if center_dist:
                    bottom = data['elevation']
                    top = bottom + data['height']
                    slope_range = [
                        max((bottom - midheight) / center_dist, -tangent),
                        min((top - midheight) / center_dist, tangent),
                    ]
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

            last_tile = tile_key
            last_end_pos = end_pos.copy()
        
        entity = closest[1]
        if entity is not None:
            entity.hitscan_damage(damage)
            entity.textures = [FALLBACK_SURF]

    def missile_attack(self: Self,
                       damage: Real,
                       attack_range: Real,
                       foa: Real,
                       precision: int=2) -> None:
        pass


class EntityManager(object):
    
    def __init__(self: Self, 
                 player: Player, 
                 entities: set[Entity]) -> None:
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

    def add_entity(self: Self, entity: Entity) -> None:
        self._entities.add(entity)
        self._add_to_sets(entity)

    def remove_entity(self: Self, entity: Entity) -> None:
        key = gen_tile_key(entity._pos)
        self._sets[key].remove(entity) # remove from set
        entity._manager = None
        self._entities.remove(entity)

    def update(self: Self, rel_game_speed: Real, level_timer: Real) -> None:
        for entity in self._entities:
            old_key = gen_tile_key(entity._pos)
            entity.update(rel_game_speed, level_timer)
            key = gen_tile_key(entity._pos)
            entity._update_manager_sets(old_key, key)


class Missile(Entity):
    def __init__(self: Self,
                 width: Real=1,
                 height: Real=0.5,
                 textures: list[pg.Surface]=[FALLBACK_SURF],
                 render_width: Optional[Real]=None,
                 render_height: Optional[Real]=None) -> None:
        super().__init__(
            width=width,
            height=height,
            health=-1,
            climb=0,
            gravity=0,
            textures=textures,
            render_width=render_width,
            render_height=render_height,
        )

# CUSTOM

