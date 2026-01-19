from numbers import Real
from typing import Self

import pygame as pg

from .weapons import Weapon
from .weapons import MeleeWeapon
from .weapons import AmmoWeapon


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
    def __init__(self: Self, collectibles: set[Collectible]=set()) -> None:
        self._weapons = {}
        self._collectibles = collectibles

    @property
    def collectibles(self: Self) -> set[Collectible]:
        return self._collectibles
    
    @collectibles.setter
    def collectibles(self: Self, value: set[Collectible]) -> None:
        self._collectibles = value

    def add_weapon(self: Self,
                   weapon: Weapon,
                   number: Optional[int]=None) -> bool:
        value = self._weapons.get(weapon)
        if value is None:
            self._weapons[weapon] = number
            return True
        elif ((isinstance(weapon, MeleeWeapon)
               and value + number <= weapon._durability)
              or (isinstance(weapon, AmmoWeapon)
                  and value + number <= weapon._capacity)):
            self._weapons[weapon] += number
            return True
        return False

    def remove_weapon(self: Self, weapon: Weapon) -> None:
        self._weapons.pop(weapon)

    def add_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.add(collectible)

    def remove_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.remove(collectible)

