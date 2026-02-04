cimport cython

from libc.math cimport floorf
from libc.math cimport fabs

import math
from typing import Self

from pygame.typing import Point


# is getting called a lot so not using python implementation
cdef str gen_tile_key(obj: Point):
    # <int> faster than int()
    return f'{<int>floorf(obj[0])};{<int>floorf(obj[1])}'


# A* pathfinder; points are in the format tuple[Point, int]
cdef class Pathfinder:
    cdef: 
        int[8][2] _TILE_OFFSETS
        dict tilemap
        dict _gs
        dict _elevations
        float _height
        float _climb
        float _straight_weight
        float _diagonal_weight
        float _elevation_weight
        float _greediness

    def __init__(self: Self,
                 dict tilemap,
                 float height=1,
                 float climb=0.2,
                 float straight_weight=1,
                 float diagonal_weight=1.414,
                 float elevation_weight=1,
                 float greediness=1) -> None:
        
        self._TILE_OFFSETS = [
            (-1,  1), (0,  1), (1,  1),
            (-1,  0), (1,  0),
            (-1, -1), (0, -1), (1, -1),
        ]
        
        self._tilemap = tilemap
        self._height = height
        self._climb = climb
        self._straight_weight = straight_weight
        self._diagonal_weight = diagonal_weight
        self._elevation_weight = elevation_weight
        self._greediness = greediness
        
        self._reset_cache()

    @property
    def straight_weight(self: Self):
        return self._straight_weight

    @straight_weight.setter
    def straight_weight(self: Self, float value):
        self._straight_weight = value

    @property
    def diagonal_weight(self: Self) -> Real:
        return self._diagonal_weight

    @diagonal_weight.setter
    def diagonal_weight(self: Self, float value):
        self._diagonal_weight = value

    @property
    def elevation_weight(self: Self):
        return self._elevation_weight

    @elevation_weight.setter
    def elevation_weight(self: Self, float value):
        self._elevation_weight = value

    @property
    def greediness(self: Self):
        return self._greediness

    @greediness.setter
    def greediness(self: Self, float value):
        self._greediness = value

    cdef void _reset_cache(self: Self):
        self._gs = {}
        self._elevations = {}

    cdef float _g(self: Self, tuple location):
        cdef float g = self._gs.get(location)
        if g is None:
            g = 2147483647
            self._gs[location] = g
        return g

    cdef float _h(self: Self,
                  tuple location,
                  tuple end):
        # Manhattan Distance
        # Won't give perfect path if I use this heuristic
        # But it is fast
        return (
            (abs(location[0][0] - end[0][0])
             + abs(location[0][1] - end[0][1]))
            * self._straight_weight
            + abs(
                self._get_elevation(location)
                - self._get_elevation(end)
            ) * self._elevation_weight
        ) * self._greediness

    cdef float _get_elevation(self: Self, tuple location):
        cdef float elevation = self._elevations.get(location)
        if elevation is None:
            elevation = 0
            if location[1]: 
                data = self._tilemap.get(gen_tile_key(location[0]))
                if data is not None:
                    elevation = data['height'] + data['elevation']
            self._elevations[location] = elevation
        return elevation

    cdef bint _cant(self: Self,
                    object data,
                    int elevation,
                    float bottom,
                    float climb):
        if data is None:
            if elevation:
                return True
            return False
        return (
            data['elevation'] < bottom + self._height if not elevation
            else data['elevation'] + data['height'] - bottom > climb
        )

    cdef float _calculate(self: Self,
                          tuple location,
                          int[2] offset,
                          int elevation,
                          tuple neighbor,
                          float climb):
        tile = location[0]
        # i know neighbor can be calculated here
        # but it is faster if it is calculated in the for loop
        # I'm aware of how weird this looks but it works
        data = self._tilemap.get(gen_tile_key(neighbor[0]))
        bottom = self._get_elevation(location)
        if self._cant(data, elevation, bottom, climb):
            return 2147483647
        elif offset[0] and offset[1]:
            data = self._tilemap.get(gen_tile_key((tile[0], tile[1] + offset[1])))
            if self._cant(data, elevation, bottom, climb):
                return 2147483647
            data = self._tilemap.get(gen_tile_key((tile[0] + offset[0], tile[1])))
            if self._cant(data, elevation, bottom, climb):
                return 2147483647
            weight = self._diagonal_weight
        else:
            weight = self._straight_weight
        cdef float difference = self._get_elevation(neighbor) - bottom
        if difference < 0:
            weight -= difference * self._elevation_weight
        elif difference > self._climb:
            weight += (difference - self._climb) * self._elevation_weight
        return weight

    def pathfind(self: Self,
                 start: tuple[Point, int],
                 end: tuple[Point, int],
                 climb: Optional[Real]=None,
                 max_nodes: int=100) -> Optional[list[tuple[Point, int]]]:
        # Setup
        self._reset_cache()
        if climb is None:
            climb = self._climb 
        parent = {}
        visited = set() # closed
        will = {start: self._h(start, end)} # open
        self._gs[start] = 0

        # Algorithm
        while will and len(visited) <= max_nodes:
            # Find the node
            node = min(will, key=lambda x: will[x])
            if node == end:
                # Trace path back
                path = []
                node = parent.get(end)
                if node is not None:
                    path.append(node)
                    while node != start:
                        node = parent[node]
                        path.append(node)
                print(len(visited), len(path))
                return path
            will.pop(node)
            visited.add(node)

            # Check Neighbor
            for offset in self._TILE_OFFSETS:
                if not (offset[0] or offset[1]):
                    continue
                for elevation in range(2): # 0 is ground; 1 is atop tile
                    neighbor = (
                        (node[0][0] + offset[0],
                         node[0][1] + offset[1]),
                        elevation,
                    )
                    if neighbor in visited:
                        continue
                    tentative = (
                        self._g(node)
                        + self._calculate(
                            node, offset, elevation, neighbor, climb,
                        )
                    )
                    if tentative >= self._g(neighbor):
                        continue
                    self._gs[neighbor] = tentative
                    parent[neighbor] = node
                    will[neighbor] = tentative + self._h(neighbor, end)

