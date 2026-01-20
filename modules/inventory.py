from numbers import Real
from typing import Self
from typing import Optional

import pygame as pg

from .sound import Sound
from .weapons import Weapon
from .weapons import MeleeWeapon
from .weapons import AmmoWeapon


class Collectible(object):
    def __init__(self: Self,
                 textures: list[pg.Surface],
                 animation_time: Real,
                 pickup_sound: Optional[Sound]=None) -> None:
        self._textures = {
            'ground': textures,
        }
        self._animation_times = {
            'ground': animation_time,
        }
        self._sounds = {
            'pickup': pickup_sound,
        }


class Inventory(object):
    def __init__(self: Self,
                 collectibles: set[Collectible]=set(),
                 weapons: dict[Weapon, int]={}) -> None:
        self._collectibles = collectibles
        self._weapons = weapons

    @property
    def collectibles(self: Self) -> set[Collectible]:
        return self._collectibles
    
    @collectibles.setter
    def collectibles(self: Self, value: set[Collectible]) -> None:
        self._collectibles = value

    @property
    def weapons(self: Self) -> dict[Weapon, int]:
        return self._weapons

    @weapons.setter
    def weapons(self: Self, value: dict[Weapon, int]) -> None:
        self._weapons = value

    def add_weapon(self: Self,
                   weapon: Weapon,
                   number: int=0) -> bool:
        value = self._weapons.get(weapon)
        if value is None:
            self._weapons[weapon] = number
            return True
        elif isinstance(weapon, MeleeWeapon) and value < weapon._durability:
            self._weapons[weapon] = min(value + number, weapon._durability)
            return True
        elif isinstance(weapon, AmmoWeapon) and value < weapon._capacity:
            self._weapons[weapon] = min(value + number, weapon._capacity)
            return True
        return False

    def remove_weapon(self: Self, weapon: Weapon) -> None:
        self._weapons.pop(weapon)

    def set_weapon_number(self: Self, weapon: Weapon, number: int) -> None:
        self._weapons[weapon] = number

    def change_weapon_number(self: Self, weapon: Weapon, change: int) -> None:
        self._weapons[weapon] += change

    def add_collectible(self: Self, collectible: Collectible) -> bool:
        value = collectible not in self._collectibles
        self._collectibles.add(collectible)
        return value

    def remove_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.remove(collectible)

