# cython: language_level=3, profile=True, boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True, cpow=True

cimport cython

from libc.math cimport fabs
from libc.math cimport floorf

from typing import Self

from pygame.typing import Point


# is getting called a lot so not using python implementation
cdef str gen_tile_key(obj: Point):
    # <int> faster than int()
    return f'{<int>floorf(obj[0])};{<int>floorf(obj[1])}'


cdef float normalize_degrees(float angle):
    # + 180, then + 360
    return (angle + 540) % 360 - 180


# A* pathfinder; points are in the format tuple[Point, int]
cdef class Pathfinder:
    cdef: 
        int[8][2] _TILE_OFFSETS
        float[8] _ANGLES
        dict _tilemap
        dict _gs
        dict _elevations
        float _height
        float _climb
        float _fall
        float _straight_weight
        float _diagonal_weight
        float _elevation_weight
        float _greediness
        float _max_turn

    def __init__(self: Self,
                 dict tilemap,
                 float height=1,
                 float climb=0.2,
                 float fall=-1,
                 float straight_weight=1,
                 float diagonal_weight=1.414,
                 float elevation_weight=1,
                 float greediness=1,
                 float max_turn=90) -> None:
        
        self._TILE_OFFSETS = [
            [-1,  1], [0,  1], [1,  1],
            [-1,  0],          [1,  0],
            [-1, -1], [0, -1], [1, -1],
        ]

        self._ANGLES = [
            -45,   0,   45,
            -90,        90,
            -135, -180, 135,
        ]
        
        self._tilemap = tilemap
        self._height = height
        self._climb = climb
        self._fall = fall
        self._straight_weight = straight_weight
        self._diagonal_weight = diagonal_weight
        self._elevation_weight = elevation_weight
        self._greediness = greediness
        self._max_turn = max_turn

    @property
    def tilemap(self: Self):
        return self._tilemap

    @tilemap.setter
    def tilemap(self: Self, dict value):
        self._tilemap = value

    @property
    def height(self: Self):
        return self._height

    @height.setter
    def height(self: Self, float value):
        self._height = value

    @property
    def climb(self: Self):
        return self._climb

    @climb.setter
    def climb(self: Self, float value):
        self._climb = value

    @property
    def fall(self: Self):
        return self._fall

    @fall.setter
    def fall(self: Self, float value):
        self._fall = value

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

    @property
    def max_turn(self: Self):
        return self._max_turn

    @max_turn.setter
    def max_turn(self: Self, float value):
        self._max_turn = value

    cdef void _reset_cache(self: Self):
        self._gs = {}
        self._elevations = {}

    cdef float _g(self: Self, tuple node):
        cdef object g = self._gs.get(node)
        if g is None:
            g = 2147483647
            self._gs[node] = g
        return g

    cdef float _h(self: Self, tuple node, tuple end):
        # Manhattan Distance
        # Won't give perfect path if I use this heuristic
        # But it is fast
        return (
            (fabs(<float>node[0][0] - <float>end[0][0])
             + fabs(<float>node[0][1] - <float>end[0][1]))
            * self._straight_weight
            + fabs(
                self._get_elevation(node)
                - self._get_elevation(end)
            ) * self._elevation_weight
        ) * self._greediness

    cdef float _get_elevation(self: Self, tuple node):
        cdef object elevation = self._elevations.get(node)
        if elevation is None:
            elevation = 0
            if node[1]: 
                data = self._tilemap.get(gen_tile_key(node[0]))
                if data is not None:
                    elevation = data['height'] + data['elevation']
            self._elevations[node] = elevation
        return elevation

    cdef bint _cant(self: Self,
                    object data,
                    int elevation,
                    float bottom,
                    float climb):
        if data is None:
            if elevation:
                return True
            return self._fall != -1 and bottom > self._fall
        cdef float tile_elevation = data['elevation']
        cdef float tile_height = data['height']
        if elevation:
            return (
                tile_elevation + tile_height - bottom > climb
                or (self._fall != -1
                    and bottom - tile_elevation - tile_height > self._fall)
            )
        else:
            return (
                tile_elevation < bottom + self._height
                or (self._fall != -1 and bottom > self._fall)
            )

    cdef float _calculate(self: Self,
                          tuple node,
                          int[2] offset,
                          int elevation,
                          tuple neighbor,
                          float climb):
        cdef:
            object data
            float bottom = self._get_elevation(node)
            int[2] tile = node[0]
        # i know neighbor can be calculated here
        # but it is faster if it is calculated in the for loop
        # I'm aware of how weird this looks but it works
        data = self._tilemap.get(gen_tile_key(neighbor[0]))
        if self._cant(data, elevation, bottom, climb):
            return 2147483647
        elif offset[0] and offset[1]:
            data = self._tilemap.get(
                gen_tile_key((tile[0], tile[1] + offset[1])),
            )
            if self._cant(data, elevation, bottom, climb):
                return 2147483647
            data = self._tilemap.get(
                gen_tile_key((tile[0] + offset[0], tile[1])),
            )
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

    cdef list _pathfind(self: Self,
                        float yaw,
                        tuple start,
                        tuple end,
                        float climb=-1,
                        int max_nodes=100,
                        bint force=0):
        # Setup
        self._reset_cache()
        cdef:
            list path # final path
            dict yaws = {start: yaw}
            dict parent = {start: start}
            dict will = {start: self._h(start, end)} # open
            set visited = set() # closed
            int elevation
            int[2] offset
            float turn
            float f
            float h
            float least
            float least_h = 2147483647
            float tentative_g
            tuple closest_node
            tuple tentative
            tuple node
            tuple neighbor

        if climb == -1:
            climb = self._climb 
        self._gs[start] = 0

        # Algorithm
        while will and len(visited) <= max_nodes:
            # Find the node
            least = 2147483647
            for tentative in will:
                f = will[tentative]
                if f < least:
                    least = f
                    node = tentative
            if node == end:
                # Trace path back
                node = parent.get(end)
                if node is None:
                    return []
                path = [node]
                while node != start:
                    node = parent[node]
                    path.append(node)
                return path
            f = will.pop(node)
            if force:
                h = f - self._gs[node]
                if h < least_h:
                    least_h = h
                    closest_node = node
            visited.add(node)

            # Check Neighbor
            for i in range(8):
                offset = self._TILE_OFFSETS[i]
                turn = fabs(
                    normalize_degrees(self._ANGLES[i] - <float>yaws[node[0]])
                )
                if turn > self._max_turn:
                    continue 
                for elevation in range(2): # 0 is ground; 1 is atop tile
                    neighbor = (
                        (<int>node[0][0] + offset[0],
                         <int>node[0][1] + offset[1]),
                        elevation,
                    )
                    if neighbor in visited:
                        continue
                    tentative_g = (
                        self._g(node)
                        + self._calculate(
                            node, offset, elevation, neighbor, climb,
                        )
                    )
                    if tentative_g >= self._g(neighbor):
                        continue
                    self._gs[neighbor] = tentative_g
                    parent[neighbor] = node
                    yaws[neighbor[0]] = self._ANGLES[i]
                    will[neighbor] = tentative_g + self._h(neighbor, end)
        if force:
            node = parent[closest_node]
            path = [node]
            while node != start:
                node = parent[node]
                path.append(node)
            return path
        return []

    def pathfind(self: Self,
                 float yaw,
                 tuple start,
                 tuple end,
                 float climb=-1,
                 int max_nodes=100,
                 bint force=0) -> list:
        return self._pathfind(yaw, start, end, climb, max_nodes, force)

