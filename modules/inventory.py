from typing import Self

import pygame as pg

from modules.weapons import Weapon


class Collectible(object):
    def __init__(self: Self,
                 textures: list[pg.Surface],
                 animation_time: Real) -> None:
        self._textures = textures
        self._animation_time = animation_time


class Inventory(object):
    def __init__(self: Self,
                 weapons: set[Weapon]=set(),
                 collectibles: set[Collectible]=set()) -> None:
        self._weapons = weapons
        self._collectibles = collectibles

    def add_weapon(self: Self, weapon: Weapon) -> None:
        self._weapons.add(weapon)

    def remove_weapon(self: Self, weapon: Weapon) -> None:
        self._weapons.remove(weapon)

    def add_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.add(collectible)

    def remove_collectible(self: Self, collectible: Collectible) -> None:
        self._collectibles.remove(collectible)

