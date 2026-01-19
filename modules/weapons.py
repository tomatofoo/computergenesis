from __future__ import annotations

from numbers import Real
from typing import Self
from typing import Optional

import pygame as pg

from .sound import Sound

# Avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .entities import Entity


# This is a very weird file but it creates an abstraction layer

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
            attack_sound=attack_sound,
        )
        self._durability = durability

    @property
    def durability(self: Self) -> int:
        return self._durability

    @durability.setter
    def durability(self: Self, value: int) -> None:
        self._durability = durability


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
            attack_sound=attack_sound,
        )


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


# CUSTOM

