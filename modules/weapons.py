from numbers import Real
from typing import Self

import pygame as pg


# This is a very weird file but it creates an abstraction layer

class Weapon(object):
    def __init__(self: Self, damage: Real, attack_range: Real) -> None:
        self._range = attack_range
        self._damage = damage

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
                 capacity: int) -> None:

        super().__init__(damage=damage, attack_range=attack_range)
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
    def __init__(self: Self, damage: Real, attack_range: Real) -> None:
        super().__init__(damage=damage, attack_range=attack_range)


class HitscanWeapon(AmmoWeapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 capacity: int) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            capacity=capacity,
        )


class MissileWeapon(AmmoWeapon):
    def __init__(self: Self,
                 damage: Real,
                 attack_range: Real,
                 capacity: int) -> None:

        super().__init__(
            damage=damage,
            attack_range=attack_range,
            capacity=capacity,
        )



# CUSTOM

