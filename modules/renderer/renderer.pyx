cimport cython
from libc.math cimport M_PI
from libc.math cimport tan
from libc.math cimport floor
from libc.math cimport fabs
from libc.math cimport fmax
from libc.math cimport fmin

import bisect
from threading import Thread
from typing import Self

cimport numpy as cnp
cnp.import_array()
import numpy as np
import pygame as pg

from modules.utils import gen_tile_key
from modules.level import ColumnTexture
from modules.level import Floor
from modules.level import Sky
from modules.level import Player


cdef double radians(double degrees):
    return degrees / 180.0 * M_PI


@cython.boundscheck(False)
@cython.wraparound(False)
# 1-Dimensional integer
cdef class Limits:

    cdef public list _limits

    def __init__(self):
        self._limits = []

    cdef void add(self: Self, int start, int end):
        # https://stackoverflow.com/a/15273749
        bisect.insort(self._limits, [start, end])
        
        cdef size_t cur = 0
        output = [self._limits[0]]
        for limit in self._limits[1:]:
            if output[cur][1] >= limit[0] - 1:
                output[cur][1] = fmax(output[cur][1], limit[1])
            else:
                cur += 1
                output.append(limit)
        self._limits = output

    cdef bool full(self: Self, int start, int end):
        for limit in self._limits:
            if limit[0] <= start and limit[1] >= end:
                return True
        return False


cdef class _DepthBufferObject:
    cdef public float _depth
    cdef public tuple _args

    def __init__(self: Self, float depth, args: tuple):
        self._depth = depth
        self._args = args # blit args

    def __lt__(self: Self, obj: Self) -> bool:
        # so objects are rendered farthest to last
        return self._depth < obj._depth 

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class Camera:

    cdef public float _fov
    cdef public float _yaw_magnitude
    cdef public float _horizon
    cdef public float _tile_size
    cdef public float _wall_render_distance
    cdef public float _bob_strength
    cdef public float _bob_frequency
    cdef public float _darkness
    cdef public float _max_line_height
    cdef public float _min_entity_depth
    cdef public object _yaw
    cdef public object _player
    cdef public object _floor
    cdef public object _ceiling
    cdef public object _walls_and_entities

    def __init__(self: Self,
                 float fov,
                 float tile_size,
                 float wall_render_distance,
                 player: Player,
                 float bob_strength=0.0375,
                 float bob_frequency=10,
                 float darkness=1,
                 float max_line_height=10,
                 float min_entity_depth=0.05) -> None:
        
        try:
            self._yaw_magnitude = float(1 / tan(radians(fov) / 2))
        except ValueError:
            self._yaw_magnitude = 0
        # already sets yaw V
        self.fov = fmin(fabs(fov), 180) # _fov is in degrees
        self._horizon = 0.5
        self._player = player
        self._tile_size = tile_size
        self._wall_render_distance = wall_render_distance
        self._max_line_height = max_line_height
        self._min_entity_depth = min_entity_depth
        self._darkness = darkness

        self.bob_strength = bob_strength
        self.bob_frequency = bob_frequency

    @property
    def bob_strength(self: Self):
        return self._bob_stength

    @bob_strength.setter
    def bob_strength(self: Self, float value):
        value = fmax(fmin(value, 0.5), -0.5)
        self._bob_strength = value
        self._player._settings['bob_strength'] = value

    @property
    def bob_frequency(self: Self):
        return self._bob_frequency

    @bob_frequency.setter
    def bob_frequency(self: Self, float value):
        self._bob_frequency = value
        self._player._settings['bob_frequency'] = value

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player):
        self._player._settings['bob_frequency'] = 0
        self._player._settings['bob_strength'] = 0
        self._player = value
        value._settings['bob_frequency'] = self._bob_frequency
        value._settings['bob_strength'] = self._bob_strength

    @property
    def fov(self: Self):
        return self._fov

    @fov.setter
    def fov(self: Self, float value):
        semiradians = radians(value / 2)

        self._fov = value
        self._yaw_magnitude = 1 / tan(semiradians)

    @property
    def horizon(self: Self):
        return self._horizon

    @horizon.setter
    def horizon(self: Self, float value):
        self._horizon = fmax(fmin(value, 1), 0)

    @property
    def tile_size(self: Self):
        return self._tile_size

    @tile_size.setter
    def tile_size(self: Self, float value):
        self._tile_size = value

    @property
    def wall_render_distance(self: Self):
        return self._wall_render_distance

    @wall_render_distance.setter
    def wall_render_distance(self: Self, float value):
        self._wall_render_distance = value

    @property
    def max_line_height(self: Self):
        return self._max_line_height

    @max_line_height.setter
    def max_line_height(self: Self, float value):
        self._max_line_height = value

    @property
    def min_entity_depth(self: Self):
        return self._min_entity_depth

    @min_entity_depth.setter
    def min_entity_depth(self: Self, float value):
        self._min_entity_depth = value

    cdef cnp.ndarray[char, ndim=3] _generate_array(
        self: Self,
        int width,
        float mult,
        texture: Floor,
        left_ray: pg.Vector2,
        right_ray: pg.Vector2,
        cnp.ndarray[double, ndim=2] x_pixels,
        cnp.ndarray[double, ndim=1] offsets
    ):

        cdef cnp.ndarray[double, ndim=1, mode='c'] start_points_x
        cdef cnp.ndarray[double, ndim=1, mode='c'] start_points_y
        cdef cnp.ndarray[double, ndim=1, mode='c'] end_points_x
        cdef cnp.ndarray[double, ndim=1, mode='c'] end_points_y
        cdef cnp.ndarray[double, ndim=1, mode='c'] step_x
        cdef cnp.ndarray[double, ndim=1, mode='c'] step_y
        cdef cnp.ndarray[double, ndim=2, mode='c'] x_points
        cdef cnp.ndarray[double, ndim=2, mode='c'] y_points
        cdef cnp.ndarray[long, ndim=2, mode='c'] texture_xs
        cdef cnp.ndarray[long, ndim=2, mode='c'] texture_ys
        cdef cnp.ndarray[char, ndim=3, mode='c'] array

        # takes into account elevation
        # basically, some of the vertical camera plane is below the ground
        # intersection between ground and ray is behind the plane
        # (not in front); we use this multiplier
        start_points_x = mult / offsets * left_ray[0]
        start_points_y = mult / offsets * left_ray[1]

        end_points_x = mult / offsets * right_ray[0]
        end_points_y = mult / offsets * right_ray[1]

        step_x = (end_points_x - start_points_x) / width
        step_y = (end_points_y - start_points_y) / width
        
        x_points = self._player._pos.x + start_points_x + step_x * x_pixels
        y_points = self._player._pos.y + start_points_y + step_y * x_pixels
        
        # change the multiplier before the mod to change size of texture
        texture_xs = np.floor(
            x_points * texture._scale[0] % 1 * texture.width,
        ).astype('int')
        texture_ys = np.floor(
            y_points * texture._scale[1] % 1 * texture.height,
        ).astype('int')

        array = texture[texture_xs, texture_ys]

        return array

    cdef void _render_floor_and_ceiling(self: Self,
                                        int width,
                                        int height,
                                        int horizon):

        
        # Setup (in both floor & ceiling)
        cdef object left_ray = self._yaw - self._player._semiplane
        cdef object right_ray = self._yaw + self._player._semiplane
        cdef object obj
        cdef int[4] rect
        cdef int difference
        cdef int amount_of_offsets
        
        # all x values
        cdef cnp.ndarray[double, ndim=2, mode='c'] x_pixels = np.vstack(
            np.linspace(0, width, num=width, endpoint=0),
        )
        cdef cnp.ndarray[double, ndim=1, mode='c'] offsets
        cdef cnp.ndarray[double, ndim=2, mode='c'] lighting
        cdef cnp.ndarray[char, ndim=3, mode='c'] array

        # Sky stuff
        cdef float semiheight = height / 2
        cdef float sky_speed = width / 100
        cdef double mult

        # Actual Render
        obj = self._player._manager._level._floor
        if isinstance(obj, Sky):
            rect = (0, horizon, width, height - horizon)
            if height < obj._height:
                self._floor = obj.scroll(
                    -self._player.yaw * sky_speed,
                    width,
                    obj._height,
                ).subsurface(rect)
        elif obj:
            # Floor Casting
            difference = int(height - horizon)
            amount_of_offsets = min(difference, height)

            if difference >= 1:
                offsets = np.linspace(
                    fmax(-horizon, 1),
                    amount_of_offsets + fmax(-horizon, 0),
                    num=amount_of_offsets,
                    endpoint=0
                ) # offsets from horizon to render

                mult = self._tile_size * self._player._render_elevation
                array = self._generate_array(
                    width=width,
                    mult=mult,
                    texture=obj,
                    left_ray=left_ray,
                    right_ray=right_ray,
                    x_pixels=x_pixels,
                    offsets=offsets,
                )
                
                #lighting
                if self._darkness:
                    lighting = np.minimum(
                        np.vstack(offsets) / semiheight / self._darkness,
                        1,
                    )
                    array = (array * lighting).astype('uint8')
                    # can't do *= ^

                self._floor = pg.surfarray.make_surface(array)

        obj = self._player._manager._level._ceiling
        # Ceiling Casting
        if isinstance(obj, Sky):
            rect = (0, obj._height - horizon, width, horizon)
            if obj._height > horizon:
                self._ceiling = obj.scroll(
                    -self._player.yaw * sky_speed,
                    width,
                    obj._height,
                ).subsurface(rect)
        elif obj:
            amount_of_offsets = int(min(horizon, height))
            if horizon >= 1:
                offsets = np.linspace(
                    amount_of_offsets,
                    0,
                    num=amount_of_offsets,
                    endpoint=0
                ) # offsets from horizon to render

                mult = self._tile_size * (1 - self._player._render_elevation)
                array = self._generate_array(
                    width=width,
                    mult=mult,
                    texture=obj,
                    left_ray=left_ray,
                    right_ray=right_ray,
                    x_pixels=x_pixels,
                    offsets=offsets,
                )
                
                # lighting
                if self._darkness:
                    lighting = np.minimum(
                        np.vstack(offsets) / semiheight / self._darkness,
                        1,
                    )
                    array = (array * lighting).astype('uint8')
                    # can't do *= ^

                self._ceiling = pg.surfarray.make_surface(array)
    
    cdef tuple _calculate_line(self: Self, double depth, data: dict):
        cdef int line_height
        cdef int render_line_height
        cdef float offset

        # distance already does fisheye correction because it 
        # divides by the magnitude of ray (when "depth" is 1)
        line_height = min(
            self._tile_size / depth * data['height'],
            self._tile_size * self._max_line_height,
        )
        # 2 was found through testing
        render_line_height = line_height + 2
        # ^ pixel glitches at bottoms of wall are avoided
        # elevation offset
        offset = (
            (self._player._render_elevation * 2
             - data['elevation'] * 2
             - data['height'])
            * self._tile_size / 2 / depth
        )
        
        # inting accounts for some pixel glitch errors
        # not inting offset because some walls seem to "bounce"
        return (line_height, render_line_height, offset)

    cdef void _darken_line(self: Self, line: pg.Surface, double dist):
        cdef double factor

        if self._darkness:
            # magic numbers found through testing
            factor = -dist**0.9 * self._darkness / 7
            pg.transform.hsl(line, 0, 0, fmax(factor, -1), line)

    cdef void _render_walls_and_entities(self: Self,
                                         int width,
                                         int height,
                                         int horizon):

        cdef int render_back
        cdef int back_edge
        cdef int side
        cdef int y
        cdef int amount
        cdef int render_y
        cdef int dex
        cdef int line_height
        cdef int render_line_height
        cdef int back_line_height
        cdef int render_back_line_height
        cdef int[2] dir
        cdef int[3] calculation
        cdef float dist
        cdef float rel_depth
        cdef float slope
        cdef float disp_x
        cdef float disp_y
        cdef float step_x
        cdef float step_y
        cdef float factor
        cdef float semiwidth = width / 2
        cdef float mag
        cdef float[2] tile
        cdef float[2] center
        cdef str tile_key
        cdef dict data
        cdef object texture

        # entity stuff
        cdef float projection_mult = self._yaw_magnitude * semiwidth
        cdef set empty_tiles = set() # empty tiles that could have entities

        # stores all walls and all that to be rendered
        # entities will be added after walls are computed
        cdef list render_buffer = []
        # distance to center of each tile (top/bottom rendering)
        cdef dict dists = {} 

        # the per-pixel alpha with (0, 0, 0, 0) doesn't seem to affect
        # fps at all
        self._walls_and_entities = pg.Surface((width, height), pg.SRCALPHA)
        self._walls_and_entities.fill((0, 0, 0, 0))
        
        # level manager stuff
        cdef object manager = self._player._manager
        cdef dict tilemap = manager._level._walls._tilemap
        textures = manager._level._walls._textures
        
        # Wall Casting
        for x in range(width):
            render_buffer.append([]) # add empty list

            ray = self._yaw + self._player._semiplane * (2 * x / width - 1)
            mag = ray.magnitude()

            end_pos = self._player._pos.copy()
            slope = ray.y / ray.x if ray.x else 2147483647
            tile = [floor(end_pos.x), floor(end_pos.y)]
            dir = (ray.x > 0, ray.y > 0)
            rel_depth = 0 # relative to yaw magnitude
            dist = 0
            
            limits = Limits()
            
            # 0 to not render back of wall
            # 1 if rendering top of back of wall
            # 2 if rendering bottom of back of wall
            render_back = 0
            back_line_height = 0
            # ^ variable is needed because the back line might not be 
            # the full height
        
            # keep on changing end_pos until hitting a wall (DDA)
            while dist < self._wall_render_distance:
                # Tile Rendering
                if render_back: # back of wall rendering
                    calculation = self._calculate_line(rel_depth, data)
                    line_height, render_line_height, offset = calculation
                    y = horizon - line_height / 2 + offset

                    if render_back == 1: # render back on top
                        render_y = horizon - line_height / 2 + offset
                        back_line_height = back_edge - render_y
                        color = data['top']
                    elif render_back == 2: # render back at bottom
                        render_y = back_edge
                        back_line_height = y + render_line_height - render_y
                        color = data['bottom']

                    render_back_line_height = back_line_height + 1
                    # this + 1 helps with pixel glitches (found by testing)
                    line = pg.Surface((1, fmax(render_back_line_height, 0)))
                    line.fill(color)
                    self._darken_line(line, dists[tup])
                    
                    obj = _DepthBufferObject(
                        rel_depth, (line, (x, render_y), None),
                    )

                    render_buffer[x].append(obj)
                    limits.add( # looks kinda weird when not int
                        render_y,
                        render_y + render_back_line_height,
                    )

                    render_back = 0

                tile_key = gen_tile_key(tile)
                data = tilemap.get(tile_key)
                if data != None: # front of wall rendering
                    if rel_depth and not limits.full(0, height):

                        calculation = self._calculate_line(rel_depth, data)
                        line_height, render_line_height, offset = calculation
                        y = horizon - line_height / 2 + offset
                        render_end = y + render_line_height

                        tup = tuple(tile) # tuple of last tile
                        center = (tile[0] + 0.5, tile[1] + 0.5)
                        # render back of tile on to
                        if horizon < y:
                            render_back = 1
                            back_edge = int(y)
                            if dists.get(tup) == None: # calc dist to center
                                dists[tup] = self._player._pos.distance_to(
                                    center,
                                )

                        # render back of tile on bottom
                        elif horizon > render_end:
                            render_back = 2
                            back_edge = int(render_end)
                            # ^ inting helps with pixel glitch
                            if dists.get(tup) == None: # calc dist to center
                                dists[tup] = self._player._pos.distance_to(
                                    center,
                                )
                            
                        # check if line is visible
                        if (render_end > 0
                            and y < height
                            and not limits.full(y, render_end)):
                            # Transformation
                            texture = data['texture']
                            dex = int(floor(
                                end_pos[side] % 1 * textures[texture].width,
                            ))
                            line = pg.transform.scale(
                                textures[texture][dex],
                                (1, render_line_height)
                            )
                            self._darken_line(line, dist)
 
                            # Reverse Painter's Algorithm
                            amount = len(limits._limits)
                            # not enumerated because + 1
                            for i in range(amount + 1):
                                end = limits._limits[i - 1][1] if i else 0
                                if i < amount:
                                    start = limits._limits[i][0]
                                else:
                                    start = height

                                if y < start and render_end > end:
                                    render_y = max(end, y)
                                    rect = pg.Rect(
                                        0,
                                        render_y - y,
                                        1,
                                        # + 1 was found through testing
                                        # helps w/ pixel glitches
                                        start - render_y + 1,
                                    )
                                    
                                    obj = _DepthBufferObject(
                                        rel_depth, (line, (x, render_y), rect),
                                    )
                                    render_buffer[x].append(obj)

                                    if rect.bottom >= render_line_height:
                                        break
                            # looks kinda weird when not int
                            limits.add(int(y), int(render_end))
                else:
                    empty_tiles.add(tile_key)
                
                # displacements until hit tile
                disp_x = tile[0] + dir[0] - end_pos.x
                disp_y = tile[1] + dir[1] - end_pos.y
                # step for tile (for each displacement)
                step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
                step_y = dir[1] * 2 - 1 

                len_x = fabs(disp_x / ray.x) if ray.x else 2147483647
                len_y = fabs(disp_y / ray.y) if ray.y else 2147483647
                if len_x < len_y:
                    tile[0] += step_x
                    end_pos.x += disp_x
                    end_pos.y += disp_x * slope
                    rel_depth += len_x
                    side = 1
                else:
                    tile[1] += step_y
                    end_pos.x += disp_y / slope if slope else 2147483647
                    end_pos.y += disp_y
                    rel_depth += len_y
                    side = 0
                dist = rel_depth * mag
            # the objects are added in closest-to-farthest
            # reverse so that depth buffer works
        
        cdef int[2] projection
        cdef float scale

        # Entity Rendering
        for tile_key in empty_tiles:
            entities = manager._sets.get(tile_key)
            if entities:
                for entity in entities:
                    rel_vector = entity.vector3 - self._player._render_vector3
                    # rotation
                    rel_vector.rotate_y_ip(self._player._yaw_value)
                    if rel_vector.z >= self._min_entity_depth:
                        ratios = (
                            rel_vector.x / rel_vector.z,
                            rel_vector.y / rel_vector.z,
                        )
                        # final projection
                        projection = (
                            -ratios[0] * projection_mult + semiwidth,
                            -ratios[1] * projection_mult + horizon,
                        )

                        rel_depth = rel_vector.z / self._yaw_magnitude
                        dex = int(projection[0])
                        scale = self._tile_size / rel_depth
                        
                        texture = entity._texture

                        # lighting
                        if not entity._glowing and self._darkness:
                            # mgaic numbers found by testing
                            factor = -rel_vector.z**0.9 * self._darkness / 7
                            texture = pg.transform.hsl(
                                texture,
                                0, 0,
                                max(factor, -1),
                            )

                        texture = pg.transform.scale(
                            texture,
                            (entity._width * scale,
                             entity._height * scale),
                        )

                        for i in range(texture.width):
                            pos = (
                                int(dex - texture.width / 2 + i),
                                projection[1] - texture.height,
                            )
                            if 0 < pos[0] < width:
                                obj = _DepthBufferObject(
                                    rel_depth,
                                    (texture,
                                     pos,
                                     pg.Rect(i, 0, 1, texture.height)),
                                )
                                bisect.insort(render_buffer[pos[0]], obj)

        for blits in render_buffer:
            for i in range(len(blits) - 1, -1, -1):
                args = blits[i]._args
                self._walls_and_entities.blit(*args)

    def render(self: Self, surf: pg.Surface) -> None:
        cdef int width = surf.width
        cdef int height = surf.height

        surf.fill((0, 0, 0))
        self._ceiling = None
        self._floor = None
        self._yaw = self._player._yaw * self._yaw_magnitude
 
        cdef int horizon = int(self._horizon * height)
        if self._horizon == None:
            horizon = int(height / 2)
        
        floor_and_ceiling = Thread(
            target=self._render_floor_and_ceiling,
            args=(width, height, horizon),
        )
        walls_and_entities = Thread(
            target=self._render_walls_and_entities,
            args=(width, height, horizon),
        )

        floor_and_ceiling.start()
        walls_and_entities.start()
        floor_and_ceiling.join()
        walls_and_entities.join()
        
        if self._floor:
            surf.blit(self._floor, (0, horizon))
        if self._ceiling:
            surf.blit(self._ceiling, (0, 0))

        surf.blit(self._walls_and_entities, (0, 0))


