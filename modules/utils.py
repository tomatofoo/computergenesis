import math
from numbers import Number
from numbers import Real
from typing import Self

import pygame as pg
from pygame.typing import Point


FALLBACK_SURF = pg.Surface((2, 2))
pg.draw.rect(FALLBACK_SURF, (255, 0, 255), pg.Rect(1, 0, 1, 1))
pg.draw.rect(FALLBACK_SURF, (255, 0, 255), pg.Rect(0, 1, 1, 1))


class Box(object): # 3D Box
    def __init__(self: Self,
                 left: Real,
                 bottom: Real,
                 near: Real,
                 width: Real,
                 height: Real,
                 depth: Real) -> None:
        
        self._left = left
        self._bottom = bottom
        self._near = near
        self._width = width
        self._height = height
        self._depth = depth

    @property
    def left(self: Self) -> Real:
        return self._left

    @left.setter
    def left(self: Self, value: Real) -> None:
        self._left = value

    @property
    def x(self: Self) -> Real:
        return self._left

    @x.setter
    def x(self: Self, value: Real) -> None:
        self._left = value

    @property
    def right(self: Self) -> Real:
        return self._left + self._width

    @right.setter
    def right(self: Self, value: Real) -> None:
        self._left = value - self._width

    @property
    def bottom(self: Self) -> Real:
        return self._bottom

    @bottom.setter
    def bottom(self: Self, value: Real) -> None:
        self._bottom = value

    @property
    def y(self: Self) -> Real:
        return self._bottom

    @y.setter
    def y(self: Self, value: Real) -> None:
        self._bottom = value

    @property
    def top(self: Self) -> Real:
        return self._bottom + self._height

    @top.setter
    def top(self: Self, value: Real) -> None:
        self._bottom = value - self._height

    @property
    def near(self: Self) -> Real:
        return self._near

    @near.setter
    def near(self: Self, value: Real) -> None:
        self._near = value

    @property
    def z(self: Self) -> Real:
        return self._near

    @z.setter
    def z(self: Self, value: Real) -> None:
        self._near = value

    @property
    def far(self: Self) -> Real:
        return self._near + self._depth

    @far.setter
    def far(self: Self, value: Real) -> None:
        self._near = value - self._depth

    @property
    def width(self: Self) -> Real:
        return self._width

    @width.setter
    def width(self: Self, value: Real) -> None:
        self._width = value

    @property
    def w(self: Self) -> Real:
        return self._width
    
    @w.setter
    def w(self: Self, value: Real) -> None:
        self._width = value

    @property
    def height(self: Self) -> Real:
        return self._height

    @height.setter
    def height(self: Self, value: Real) -> None:
        self._height = value

    @property
    def h(self: Self) -> Real:
        return self._height

    @h.setter
    def h(self: Self, value: Real) -> None:
        self._height = value

    @property
    def depth(self: Self) -> Real:
        return self._depth

    @depth.setter
    def depth(self: Self, value: Real) -> None:
        self._depth = value

    @property
    def d(self: Self) -> Real:
        return self._depth

    @d.setter
    def d(self: Self, value: Real) -> None:
        self._depth = value

    @property
    def centerx(self: Self) -> Real:
        return self._left + self._width / 2

    @centerx.setter
    def centerx(self: Self, value: Real) -> None:
        self._left = value - self._width / 2

    @property
    def centery(self: Self) -> Real:
        return self._bottom + self._height / 2

    @centery.setter
    def centery(self: Self, value: Real) -> None:
        self._bottom = value - self._height / 2

    @property
    def centerz(self: Self) -> Real:
        return self._near + self._depth / 2

    @centerz.setter
    def centerz(self: Self, value: Real) -> None:
        self._near = value - self._depth / 2

    def copy(self: Self) -> Self:
        return Box(
            self._left,
            self._bottom,
            self._near,
            self._width,
            self._height,
            self._depth,
        )

    def update(self: Self,
               left: Real,
               bottom: Real,
               near: Real,
               width: Real,
               height: Real,
               depth: Real) -> None:

        self._left = left
        self._bottom = bottom
        self._near = near
        self._width = width
        self._height = height
        self._depth = depth
    
    def collidepoint(self: Self, point: pg.Vector3) -> bool:
        return (
            point[0] > self._left
            and point[0] < self.right
            and point[1] > self._bottom
            and point[1] < self.top
            and point[2] > self._near
            and point[2] < self.far
        )

    def collidebox(self: Self, box: Self) -> bool:
        return not (
            self._left >= box.right
            or self.right <= box._left
            or self._bottom >= box.top
            or self.top <= box._bottom
            or self._near >= box.far
            or self.far <= box._near
        )


def gen_tile_key(obj: Point):
    return f'{int(math.floor(obj[0]))};{int(math.floor(obj[1]))}'


class Pathfinder(object): # 4-path pathfinder using A*

    _TILE_OFFSETS = (
        (0, 1), (-1, 0), (1, 0), (0, -1),
    )

    def __init__(self: Self, start: Point, end: Point, tilemap: dict) -> None:
        self.start = start
        self.end = end
        self.tilemap = tilemap

        self._path = []
        self._g = {}
        self._h = {}
        self._parent = {}

    @property
    def start(self: Self) -> tuple:
        return self._start

    @start.setter
    def start(self: Self, value: Point) -> None:
        self._start = tuple(value)

    @property
    def end(self: Self) -> tuple:
        return self._end

    @end.setter
    def end(self: Self, value: Point) -> None:
        self._end = tuple(value)
    
    @property
    def tilemap(self: Self) -> dict:
        return self._tilemap

    @tilemap.setter
    def tilemap(self: Self, value: dict) -> None:
        self._tilemap = value

    @property
    def path(self: Self) -> list:
        path = list(self._path)
        path.reverse()
        return path

    def _manhattan(self: Self, start: Point, end: Point) -> int:
        return abs(end[0] - start[0]) + abs(end[1] - start[1])

    def _get_g(self: Self, location: Point) -> Number:
        g = self._g.get(location)
        if g == None:
            g = math.inf
            self._g[location] = g
        return g

    def _get_h(self: Self, location: Point) -> Number:
        h = self._h.get(location)
        if h == None:
            h = self._manhattan(location, self._end)
            self._h[location] = h
        return h

    def _get_parent(self: Self, location: Point) -> Point:
        parent = self._parent.get(location)
        if parent == None:
            parent = self._start
            self._parent[location] = parent
        return parent

    def pathfind(self: Self) -> None:
        if (self._tilemap.get(self._start) != None
            or self._tilemap.get(self._end) != None):

            return None

        # Setup
        self._g = {}
        self._h = {}
        self._parent = {}
        visited = set()
         
        will = {self._start}
        self._g[self._start] = 0

        # Algorithm
        while will:
            # Find the node
            least = math.inf
            for tentative in will:
                f = self._get_g(tentative) + self._get_h(tentative)
                if f < least:
                    node = tentative
                    least = f
            will.remove(node)
            visited.add(node)

            if node == self._end:
                break
            
            # Check Neighbor
            for offset in self._TILE_OFFSETS:
                neighbor = (node[0] + offset[0], node[1] + offset[1])

                weight = 1
                tentative = self._get_g(node) + weight

                invalid = (
                    neighbor in visited
                    or self._tilemap.get(gen_tile_key(neighbor))
                    or tentative >= self._get_g(neighbor)
                )
                if invalid:
                    continue

                self._g[neighbor] = tentative
                self._parent[neighbor] = node
                will.add(neighbor)
        
        # Trace path back
        self._path = []
        node = self._get_parent(self._end)
        while node != self._start:
            node = self._get_parent(node)
            self._path.append(node)


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

