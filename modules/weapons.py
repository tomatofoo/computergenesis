from __future__ import annotations

from numbers import Real
from typing import Self

import pygame as pg

# Avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.entities import Missile


# This is a very weird file but it creates an abstraction layer

class Weapon(object):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 ground_textures: list[pg.Surface],
                 hold_textures: list[pg.Surface],
                 attack_textures: list[pg.Surface],
                 ground_animation_time: Real=1,
                 hold_animation_time: Real=1,
                 attack_animation_time: Real=1) -> None:
        self._range = attack_range
        self._damage = damage
        
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

    @property
    def damage(self: Self) -> Real:
        return self._damage

    @property
    def attack_range(self: Self) -> Real:
        return self._attack_range


class AmmoWeapon(Weapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 capacity: int,
                 ground_textures: list[pg.Surface],
                 hold_textures: list[pg.Surface],
                 attack_textures: list[pg.Surface],
                 ground_animation_time=1,
                 hold_animation_time=1,
                 attack_animation_time=1) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
        )

        self._ammo = 0

    @property
    def ammo(self: Self) -> int:
        return self._ammo

    @ammo.setter
    def ammo(self: Self, value: int) -> None:
        self._ammo = value

    @property
    def capacity(self: Self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self: Self, value: int) -> None:
        self._capacity = value


class MeleeWeapon(Weapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 ground_textures: list[pg.Surface],
                 hold_textures: list[pg.Surface],
                 attack_textures: list[pg.Surface],
                 ground_animation_time=1,
                 hold_animation_time=1,
                 attack_animation_time=1) -> None:
        super().__init__(
            damage=damage,
            attack_range=attack_range,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
        )


class HitscanWeapon(AmmoWeapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 capacity: int,
                 ground_textures: list[pg.Surface],
                 hold_textures: list[pg.Surface],
                 attack_textures: list[pg.Surface],
                 ground_animation_time=1,
                 hold_animation_time=1,
                 attack_animation_time=1) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            capacity=capacity,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
        )


class MissileWeapon(AmmoWeapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 capacity: int,
                 missile: Missile,
                 ground_textures: list[pg.Surface],
                 hold_textures: list[pg.Surface],
                 attack_textures: list[pg.Surface],
                 ground_animation_time=1,
                 hold_animation_time=1,
                 attack_animation_time=1) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            capacity=capacity,
            ground_textures=ground_textures,
            hold_textures=hold_textures,
            attack_textures=attack_textures,
            ground_animation_time=ground_animation_time,
            hold_animation_time=hold_animation_time,
            attack_animation_time=attack_animation_time,
        )


# CUSTOM

