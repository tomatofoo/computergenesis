from numbers import Real
from typing import Self

import pygame as pg

from .weapons import WeaponManager


class Collectible(object):
    def __init__(self: Self,
                 textures: list[pg.Surface],
                 animation_time: Real) -> None:
        self._textures = {
            'ground': textures,
        }
        self._animation_times = {
            'ground': animation_time,
        }


class Inventory(object):
    def __init__(self: Self,
                 weapons: WeaponManager=WeaponManager(),
                 collectibles: set[Collectible]=set()) -> None:
        self._weapons = {}
        for weapon in weapons:
            self._weapons[weapon._id] = weapon
        self._collectibles = collectibles

    def add(self: Self, obj: Collectible | Weapon) -> None:
        if isinstance(obj, Weapon):
            self.add_weapon(obj)
        elif isinstance(obj, Collectible):
            self.add_collectible(obj)
    
    def add_weapon(self: Self, weapon: Weapon) -> None:
        value = self._weapons.get(weapon._id)
        if value is None:
            self._weapons[weapon._id] = weapon
        else:
            value.ammo += weapon.ammo

    def pop_weapon(self: Self, id: str) -> Weapon:
        return self._weapons[id].pop()

    def add_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.add(collectible)

    def remove_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.remove(collectible)

