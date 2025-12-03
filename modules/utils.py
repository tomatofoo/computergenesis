import math
from numbers import Real
from typing import Self

import pygame as pg
from pygame.typing import Point


class Box(object):
    def __init__(self: Self,
                 left: Real,
                 top: Real,
                 far: Real,
                 width: Real,
                 height: Real,
                 depth: Real) -> None:
        pass


def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'


def generate_composite(tilemap: dict[str, int],
                       textures: tuple[pg.Surface],
                       tile_size: Point) -> pg.Surface:
        lowest = (math.inf, math.inf)
        highest = (-math.inf, -math.inf)
        for tile in tilemap:
            coords = (int(item) for item in tile.split(';'))
            if (coords[0] - highest[0] + coords[1] - highest[1]) > 0:
                highest = coords
            # regular if (not elif) in case there is only one tile
            if (lowest[0] - coords[0] + lowest[1] - coords[1]) > 0:
                lowest = coords
        scale = (highest[0] - lowest[0] + 1, highest[1] - lowest[1] + 1)
        surf = pg.Surface((scale[0] * tile_size[0], scale[1] * tile_size[1]))
        for tile, texture in tilemap.items():
            coords = (int(item) for item in tile.split(';'))
            render_coords = (coords[0] % scale[0] * tile_size[0],
                             coords[1] % scale[1] * tile_size[1])
            surf.blit(textures[texture], render_coords)
        return surf, scale

