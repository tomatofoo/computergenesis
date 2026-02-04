cdef class Pathfinder: # A* pathfinder entity (imperfect path)

    _DIAGONAL = {(-1,  1), (1,  1), (-1, -1), (1, -1)}

    def __init__(self: Self,
                 height: Real=1,
                 climb: Real=0.2,
                 straight_weight: Real=1,
                 diagonal_weight: Real=1.414,
                 elevation_weight: Real=1,
                 greediness: Real=1) -> None:

        self._height = height
        self._climb = climb
        self._weights = {
            'straight': straight_weight,
            'diagonal': diagonal_weight,
            'elevation': elevation_weight,
        }
        self._greediness = greediness
        
        self._reset_cache()

    @property
    def straight_weight(self: Self) -> Real:
        return self._weights['straight']

    @straight_weight.setter
    def straight_weight(self: Self, value: Real) -> None:
        self._weights['straight'] = value

    @property
    def diagonal_weight(self: Self) -> Real:
        return self._weights['diagonal']

    @diagonal_weight.setter
    def diagonal_weight(self: Self, value: Real) -> None:
        self._weights['diagonal'] = value

    @property
    def elevation_weight(self: Self) -> Real:
        return self._weights['elevation']

    @elevation_weight.setter
    def elevation_weight(self: Self, value: Real) -> None:
        self._weights['elevation'] = value

    @property
    def greediness(self: Self) -> Real:
        return self._greediness

    @greediness.setter
    def greediness(self: Self, value: Real) -> None:
        self._greediness = value

    def _reset_cache(self: Self) -> None:
        self._gs = {}
        self._elevations = {}

    def _g(self: Self, location: tuple[Point, int]) -> Number:
        g = self._gs.get(location)
        if g is None:
            g = math.inf
            self._gs[location] = g
        return g

    def _h(self: Self,
           location: tuple[Point, int],
           end: tuple[Point, int]) -> Number:
        # Manhattan Distance
        # Won't give perfect path if I use this heuristic
        # But it is fast
        return (
            (abs(location[0][0] - end[0][0])
             + abs(location[0][1] - end[0][1]))
            * self._weights['straight']
            + abs(
                self._get_elevation(location)
                - self._get_elevation(end)
            ) * self._weights['elevation']
        ) * self._greediness

    def _get_elevation(self: Self, location: tuple[Point, int]) -> Real:
        elevation = self._elevations.get(location)
        if elevation is None:
            elevation = 0
            if location[1]: 
                data = self._manager._level._walls._tilemap.get(
                    gen_tile_key(location[0]),
                )
                if data is not None:
                    elevation = data['height'] + data['elevation']
            self._elevations[location] = elevation
        return elevation

    def _cant(self: Self,
              data: Optional[dict],
              elevation: int,
              bottom: Real,
              climb: Real) -> bool:
        if data is None:
            if elevation:
                return True
            return False
        return (
            data['elevation'] < bottom + self._height if not elevation
            else data['elevation'] + data['height'] - bottom > climb
        )

    def _calculate(self: Self,
                   location: tuple[Point, int],
                   offset: tuple[int],
                   elevation: int,
                   neighbor: tuple[Point, int],
                   climb: Real) -> Number:
        tile = location[0]
        # i know neighbor can be calculated here
        # but it is faster if it is calculated in the for loop
        # I'm aware of how weird this looks but it works
        tilemap = self._manager._level._walls._tilemap
        data = tilemap.get(gen_tile_key(neighbor[0]))
        bottom = self._get_elevation(location)
        if self._cant(data, elevation, bottom, climb):
            return math.inf
        elif offset in self._DIAGONAL:
            data = tilemap.get(gen_tile_key((tile[0], tile[1] + offset[1])))
            if self._cant(data, elevation, bottom, climb):
                return math.inf
            data = tilemap.get(gen_tile_key((tile[0] + offset[0], tile[1])))
            if self._cant(data, elevation, bottom, climb):
                return math.inf
            weight = self._weights['diagonal']
        else:
            weight = self._weights['straight']
        difference = self._get_elevation(neighbor) - bottom
        if difference < 0:
            weight -= difference * self._weights['elevation']
        elif difference > self._climb:
            weight += (difference - self._climb) * self._weights['elevation']
        return weight

    def pathfind(self: Self,
                 end: tuple[Point, int],
                 climb: Optional[Real]=None,
                 max_nodes: int=100) -> Optional[list[tuple[Point, int]]]:
        # Start
        elevation = 0
        data = self._manager._level._walls._tilemap.get(self.tile_key)
        if (data is not None
            and data['elevation'] + data['height'] <= self._elevation):
            elevation = 1
        start = (self.tile, elevation)

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
                if offset == (0, 0):
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

