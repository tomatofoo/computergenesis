from __future__ import annotations

import math
import copy
import bisect
from numbers import Real
from typing import Self
from typing import Optional

import pygame as pg

from .sound import Sound
from .utils import gen_tile_key

# Avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .entities import Entity


class Weapon(object):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 cooldown: Real,
                 ground_textures: Optional[list[pg.Surface]]=None,
                 hold_textures: Optional[list[pg.Surface]]=None,
                 attack_textures: Optional[list[pg.Surface]]=None,
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1,
                 pickup_sound: Optional[Sound]=None,
                 attack_sound: Optional[Sound]=None) -> None:
        self._range = attack_range
        self._damage = damage
        self._cooldown = cooldown

        self._textures = {
            'ground': ground_textures,
            'hold': hold_textures,
            'attack': attack_textures,
        }
        self._animation_times = {
            'ground': ground_animation_time,
            'hold': hold_animation_time,
            'attack': attack_animation_time,
        }
        self._sounds = {
            'pickup': pickup_sound,
            'attack': attack_sound,
        }

    @property
    def damage(self: Self) -> Real:
        return self._damage

    @damage.setter
    def damage(self: Self, value: Real) -> None:
        self._damage = value

    @property
    def attack_range(self: Self) -> Real:
        return self._attack_range

    @attack_range.setter
    def attack_range(self: Self, value: Real) -> None:
        self._attack_range = value

    @property
    def cooldown(self: Self) -> Real:
        return self._cooldown

    @cooldown.setter
    def cooldown(self: Self, value: Real) -> None:
        self._cooldown = value
    
    def _autoaim_hitscan(self: Self,
                 attacker: Entity,
                 attack_range: Real,
                 foa: Real,
                 precision: int=100,
                 roa: Real=0) -> Optional[Entity]:
        # if roa is 0 then use normal hitscanning
        # else is missile hitscanning; roa is radius for vertical autoaim

        ray = attacker._yaw.normalize()

        end_pos = list(attacker._pos)
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
        tilemap = attacker._manager._level._walls._tilemap
        closest = (math.inf, None)

        # ranges of slopes of walls relative to player
        # this determines if a shot will hit a wall
        tangent = math.tan(math.radians(foa) / 2)
        slope_range = 0
        slope_ranges = []
        amount = 0
        midheight = attacker.centere
        vector = attacker.vector3
        
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
            
            # for accurate slope ranges
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
            for offset in attacker._TILE_OFFSETS:
                tile_key = gen_tile_key(
                    (last_tile[0] + offset[0], last_tile[1] + offset[1]),
                )
                tentative = attacker._manager._sets.get(tile_key)
                if tentative != None:
                    entities |= tentative

            if entities:
                for entity in entities:
                    entity_dist = attacker._pos.distance_to(entity._pos)
                    if (entity._health <= 0
                        or not entity_dist
                        or attacker._dont_attack(entity)):
                        continue
                    
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
                    
                    # makes sure it doesn't go past range
                    if dist >= attack_range:
                        end_pos = attacker._pos + ray * attack_range
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


class AmmoWeapon(Weapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 cooldown: Real,
                 capacity: int,
                 ground_textures: Optional[list[pg.Surface]]=None,
                 hold_textures: Optional[list[pg.Surface]]=None,
                 attack_textures: Optional[list[pg.Surface]]=None,
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1,
                 pickup_sound: Optional[Sound]=None,
                 attack_sound: Optional[Sound]=None) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            cooldown=cooldown,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
            pickup_sound=pickup_sound,
            attack_sound=attack_sound,
        )
        
        self._capacity = capacity

    @property
    def capacity(self: Self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self: Self, value: int) -> None:
        self._capacity = value


class MeleeWeapon(Weapon): # also hitscan btw
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 cooldown: Real,
                 durability: int,
                 ground_textures: Optional[list[pg.Surface]]=None,
                 hold_textures: Optional[list[pg.Surface]]=None,
                 attack_textures: Optional[list[pg.Surface]]=None,
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1,
                 pickup_sound: Optional[Sound]=None,
                 attack_sound: Optional[Sound]=None) -> None:
        super().__init__(
            damage=damage,
            attack_range=attack_range,
            cooldown=cooldown,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
            pickup_sound=pickup_sound,
            attack_sound=attack_sound,
        )
        self._durability = durability

    @property
    def durability(self: Self) -> int:
        return self._durability

    @durability.setter
    def durability(self: Self, value: int) -> None:
        self._durability = durability

    def autoaim_attack(self: Self, attacker: Entity, foa: Real):
        entity = self._autoaim_hitscan(attacker, self._range, foa)
        if entity is not None:
            entity.melee_damage(self._damage)
            return True
        return False


class HitscanWeapon(AmmoWeapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 cooldown: Real,
                 capacity: int,
                 ground_textures: Optional[list[pg.Surface]]=None,
                 hold_textures: Optional[list[pg.Surface]]=None,
                 attack_textures: Optional[list[pg.Surface]]=None,
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1,
                 pickup_sound: Optional[Sound]=None,
                 attack_sound: Optional[Sound]=None) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            cooldown=cooldown,
            capacity=capacity,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
            pickup_sound=pickup_sound,
            attack_sound=attack_sound,
        )

    def autoaim_attack(self: Self, attacker: Entity, foa: Real) -> bool:
        entity = self._autoaim_hitscan(attacker, self._range, foa)
        if entity is not None:
            entity.hitscan_damage(self._damage)
            return True
        return False


class MissileWeapon(AmmoWeapon):
    def __init__(self: Self,
                 missile: Missile,
                 attack_range: Real,
                 capacity: int,
                 cooldown: Real,
                 speed: Real,
                 ground_textures: Optional[list[pg.Surface]]=None,
                 hold_textures: Optional[list[pg.Surface]]=None,
                 attack_textures: Optional[list[pg.Surface]]=None,
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1,
                 pickup_sound: Optional[Sound]=None,
                 attack_sound: Optional[Sound]=None) -> None:

        super().__init__(
            damage=missile._damage,
            attack_range=attack_range,
            cooldown=cooldown,
            capacity=capacity,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
            pickup_sound=pickup_sound,
            attack_sound=attack_sound,
        )

        self._missile = missile
        self._speed = speed

    @property
    def missile(self: Self) -> Missile:
        return self._missile

    @missile.setter
    def missile(self: Self, value: Missile) -> None:
        self._missile = value
        self._damage = value._damage
    
    @property
    def damage(self: Self) -> Real:
        return self._missile._damage

    @damage.setter
    def damage(self: Self, value: Real) -> None:
        self._missile._damage = value

    @property
    def speed(self: Self) -> Real:
        return self._speed

    @speed.setter
    def speed(self: Self, value: Real) -> None:
        self._speed = value

    def autoaim_attack(self: Self,
                       attacker: Entity,
                       foa: Real,
                       roa: Real) -> None:
        # unlike melee and hitscan, missile attack will return true if a hit is
        # predicted (not guaranteed)
        attacker.boost = -attacker._yaw.normalize() * 0.5
        attacker._elevation_velocity += 0.1

        entity, could_hit = self._autoaim_hitscan(
            attacker,
            self._range,
            foa,
            roa=roa,
        )
        missile = copy.deepcopy(self._missile)
        if entity is None:
            vector = pg.Vector3(attacker._yaw[0], 0, attacker._yaw[1])
        else:
            vector = pg.Vector3(
                0,
                entity.centere - attacker.centere,
                attacker._pos.distance_to(entity._pos),
            ).rotate_y(-attacker._yaw_value)
        missile.launch(
            attacker,
            vector.normalize() * self._speed,
            self._range,
        )
        return could_hit


# CUSTOM

