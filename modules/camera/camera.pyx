# cython: language_level=3, profile=True, boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True, cpow=True

cimport cython
from cpython.mem cimport PyMem_Calloc
from cpython.mem cimport PyMem_Free

from libc.math cimport M_PI
from libc.math cimport tan
from libc.math cimport floorf
from libc.math cimport ceilf
from libc.math cimport fabs
from libc.math cimport fmax
from libc.math cimport fmin
from libc.math cimport sqrt
from libc.string cimport memset

import bisect
from threading import Thread
from typing import Self

cimport numpy as cnp
cnp.import_array()
import numpy as np
import pygame as pg
from pygame.typing import Point

from modules.level import Floor
from modules.level import Sky
from modules.entities import Player


# is getting called a lot so not using python implementation
cdef str gen_tile_key(obj: Point):
    # <int> faster than int()
    return f'{<int>floorf(obj[0])};{<int>floorf(obj[1])}'


cdef float radians(float degrees):
    return degrees / 180.0 * M_PI


cdef struct _Limit:
    int _start
    int _end

cdef struct _Limits:
    size_t _capacity
    size_t _amount
    _Limit* _arr

cdef int _limit_cmp(_Limit limit1, _Limit limit2):
    if limit1._start == limit2._start:
        if limit1._end < limit2._end:
            return -1
        elif limit1._end == limit2._end:
            return 0
        else:
            return 1
    return -1 if limit1._start < limit2._start else 1

cdef _Limits _limits_new(size_t capacity):
    cdef _Limits limits = _Limits(
        capacity,
        0,
        <_Limit *>PyMem_Calloc(capacity, sizeof(_Limit)),
    )
    if not limits._arr:
        raise MemoryError()

    return limits

cdef void _limits_destroy(_Limits *limits):
    PyMem_Free(limits._arr)

cdef void _limits_reset(_Limits *limits):
    memset(limits._arr, 0, limits._capacity * sizeof(_Limit))
    limits._amount = 0

cdef bool _limits_add(_Limits* limits, int start, int end): # bool
    if limits._amount >= limits._capacity:
        return False

    cdef:
        _Limit limit = _Limit(start, end)
        _Limit item
        size_t dex = 0
        size_t cur = 0
        size_t i
        int cur_end
    
    # three-step insertion
    for i in range(limits._amount + 1): # find dex
        item = limits._arr[i]
        if i >= limits._amount or _limit_cmp(limit, item) < 1:
            dex = i
            break

    if dex < limits._amount: # avoid unnecessary shifting
        for i in range(limits._amount, dex, -1): # shift elements
            limits._arr[i] = limits._arr[i - 1]

    limits._arr[dex] = limit # insert
    limits._amount += 1
    
    # https://stackoverflow.com/a/15273749
    # condense inplace
    # don't need to set value to zero after condensing
    # because we will only iterate until _amount
    for i in range(1, limits._amount):
        item = limits._arr[i]
        cur_end = limits._arr[cur]._end
        if cur_end >= item._start - 1:
            limits._arr[cur]._end = int(fmax(
                cur_end,
                item._end,
            ))
        else:
            cur += 1
            limits._arr[cur] = item

    limits._amount = cur + 1

    return True

cdef bool _limits_full(_Limits *limits, int start, int end): # bool
    cdef:
        _Limit item
        size_t i
    for i in range(limits._amount):
        item = limits._arr[i]
        if item._start <= start and item._end >= end:
            return True
    return False


cdef class _DepthBufferObject:
    cdef public float _depth
    cdef public tuple _args
    cdef public int _is_rect

    def __init__(self: Self,
                 float depth,
                 args: tuple,
                 is_rect: bool=False) -> None:
        self._depth = depth
        self._args = args # blit args
        self._is_rect = is_rect

    def __lt__(self: Self, obj: Self) -> bool:
        # so objects are rendered farthest to last
        return self._depth < obj._depth


# A shit ton of changes might need to be made for multi tilemap support
cdef class Camera:
    
    cdef:
        float _fov
        float _yaw_magnitude
        float _horizon
        float _tile_size
        float _wall_render_distance
        float _headbob_strength
        float _headbob_frequency
        float _weaponbob_strength
        float _weaponbob_frequency
        float _weapon_scale
        float _climb_speed
        float _darkness
        float _max_line_height
        float _min_entity_depth
        object _yaw
        object _player
        object _floor
        object _ceiling
        object _walls_and_entities
        object _weapon
        object _weapon_pos # uv coords, python obj on purpose

    def __init__(self: Self,
                 float fov,
                 float tile_size,
                 float wall_render_distance,
                 player: Player,
                 float headbob_strength=0.0375,
                 float headbob_frequency=0.1667,
                 float weaponbob_strength=0.05,
                 float weaponbob_frequency=0.08335,
                 weapon_pos: Point=(0.5, 0.35),
                 float climb_speed=0.15,
                 float darkness=1,
                 float max_line_height=50,
                 float min_entity_depth=0.05) -> None:
        
        self._yaw_magnitude = 1 / tan(radians(fov) / 2)
        # already sets yaw V
        self.fov = fmin(fabs(fov), 180) # _fov is in degrees
        self._horizon = 0.5
        self._player = player
        self._tile_size = tile_size
        self._wall_render_distance = wall_render_distance
        self._weapon_scale = 1
        self._max_line_height = max_line_height
        self._min_entity_depth = min_entity_depth
        self._darkness = darkness

        self.headbob_strength = headbob_strength
        self.headbob_frequency = headbob_frequency
        self.weaponbob_strength = weaponbob_strength
        self.weaponbob_frequency = weaponbob_frequency
        self.weapon_pos = weapon_pos
        self.climb_speed = climb_speed

    @property
    def headbob_strength(self: Self):
        return self._headbob_stength

    @headbob_strength.setter
    def headbob_strength(self: Self, float value):
        value = fmax(fmin(value, 0.5), -0.5)
        self._headbob_strength = value
        self._player._settings['headbob_strength'] = value

    @property
    def headbob_frequency(self: Self):
        return self._headbob_frequency

    @headbob_frequency.setter
    def headbob_frequency(self: Self, float value):
        self._headbob_frequency = value
        self._player._settings['headbob_frequency'] = value

    @property
    def weaponbob_strength(self: Self):
        return self._weaponbob_stength

    @weaponbob_strength.setter
    def weaponbob_strength(self: Self, float value):
        value = fmax(fmin(value, 0.5), -0.5)
        self._weaponbob_strength = value
        self._player._settings['weaponbob_strength'] = value

    @property
    def weaponbob_frequency(self: Self):
        return self._weaponbob_frequency

    @weaponbob_frequency.setter
    def weaponbob_frequency(self: Self, float value):
        self._weaponbob_frequency = value
        self._player._settings['weaponbob_frequency'] = value

    @property
    def weapon_pos(self: Self) -> Point:
        return self._weapon_pos

    @weapon_pos.setter
    def weapon_pos(self: Self, value: Point) -> None:
        self._weapon_pos = value
        cdef float[2] old = self._player._settings['weapon_pos']
        self._player._render_weapon_pos = (
            <float>value[0]
            + <float>self._player._render_weapon_pos[0]
            - old[0],
            <float>value[1]
            + <float>self._player._render_weapon_pos[1]
            - old[1],
        )
        self._player._settings['weapon_pos'] = value

    @property
    def weapon_scale(self: Self):
        return self._weapon_scale

    @weapon_scale.setter
    def weapon_scale(self: Self, value: float):
        self._weapon_scale = value

    @property
    def climb_speed(self: Self) -> Real:
        return self._climb_speed

    @climb_speed.setter
    def climb_speed(self: Self, float value):
        self._climb_speed = value
        self._player._settings['climb_speed'] = value

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player) -> None:
        self._player._settings['headbob_frequency'] = 0
        self._player._settings['headbob_strength'] = 0
        self._player._settings['weaponbob_frequency'] = 0
        self._player._settings['weaponbob_strength'] = 0
        self._player._settings['climb_speed'] = 0
        self._player = value
        value._settings['headbob_frequency'] = self._headbob_frequency
        value._settings['headbob_strength'] = self._headbob_strength
        value._settings['weaponbob_frequency'] = self._weaponbob_frequency
        value._settings['weaponbob_strength'] = self._weaponbob_stength
        value._settings['climb_speed'] = self._climb_speed

    @property
    def fov(self: Self):
        return self._fov

    @fov.setter
    def fov(self: Self, float value):
        cdef float semiradians = radians(value / 2)

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
    
    # array multiplication to render floor
    cdef cnp.ndarray[char, ndim=3] _generate_array(
        self: Self,
        int width,
        float mult,
        left_ray: pg.Vector2,
        right_ray: pg.Vector2,
        scale: tuple,
        cnp.ndarray[char, ndim=3] texture,
        x_pixels: np.ndarray,
        offsets: np.ndarray,
    ):
        
        cdef: 
            cnp.ndarray[long, ndim=2, mode='c'] texture_xs
            cnp.ndarray[long, ndim=2, mode='c'] texture_ys

        # takes into account elevation
        # basically, some of the vertical camera plane is below the ground
        # intersection between ground and ray is behind the plane
        # (not in front); we use this multiplier
        ray_mult = mult / offsets

        start_points_x = ray_mult * left_ray[0]
        start_points_y = ray_mult * left_ray[1]

        end_points_x = ray_mult * right_ray[0]
        end_points_y = ray_mult * right_ray[1]

        step_x = (end_points_x - start_points_x) / width
        step_y = (end_points_y - start_points_y) / width
        
        x_points = self._player._pos.x + start_points_x + step_x * x_pixels
        y_points = self._player._pos.y + start_points_y + step_y * x_pixels
        
        # change the multiplier before the mod to change size of texture
        texture_xs = np.floor(
            x_points * scale[0] % 1 * texture.shape[0],
        ).astype('int')
        texture_ys = np.floor(
            y_points * scale[1] % 1 * texture.shape[1],
        ).astype('int')

        return texture[texture_xs, texture_ys]


    cdef void _render_floor_and_ceiling(self: Self,
                                        int width,
                                        int height,
                                        int horizon):

        cdef: 
            # Setup (in both floor & ceiling)
            object left_ray = self._yaw - self._player._semiplane
            object right_ray = self._yaw + self._player._semiplane
            object obj
            object level = self._player._manager._level
            int difference
            int amount_of_offsets
        
            # all x values
            cnp.ndarray[char, ndim=3] array

            # Sky stuff
            int sky_height
            float semiheight = height / 2
            float mult
            float scroll = -<float>self._player._yaw_value * width / 100

        x_pixels = np.vstack(np.linspace(0, width, num=width, endpoint=0))

        # Actual Render
        obj = level._floor
        if isinstance(obj, Sky):
            # scale the same factor as width
            sky_height = obj._height * width / obj._width
            rect = (0, horizon, width, height - horizon)
            if height < sky_height:
                self._floor = obj.scroll(
                    scroll,
                    width,
                    sky_height,
                ).subsurface(rect)
        elif obj:
            # Floor Casting
            difference = height - horizon

            if difference > 0:
                offsets = np.linspace(
                    1,
                    difference,
                    num=difference,
                    endpoint=0,
                ) # offsets from horizon to render

                mult = self._tile_size * <float>self._player._render_elevation
                array = self._generate_array(
                    width=width,
                    mult=mult,
                    left_ray=left_ray,
                    right_ray=right_ray,
                    scale=obj._scale,
                    texture=obj._array,
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

        obj = level._ceiling
        # Ceiling Casting
        if isinstance(obj, Sky):
            # scale the same factor as width
            sky_height = obj._height * width / obj._width
            rect = (0, sky_height - horizon, width, horizon)
            if sky_height > horizon:
                self._ceiling = obj.scroll(
                    scroll,
                    width,
                    sky_height,
                ).subsurface(rect)
        elif obj:
            if horizon > 0:
                offsets = np.linspace(
                    horizon,
                    0,
                    num=horizon,
                    endpoint=0,
                ) # offsets from horizon to render

                mult = (
                    self._tile_size
                    * (<float>level._ceiling_elevation
                       - <float>self._player._render_elevation)
                )
                array = self._generate_array(
                    width=width,
                    mult=mult,
                    left_ray=left_ray,
                    right_ray=right_ray,
                    scale=obj._scale,
                    texture=obj._array,
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
    
    cdef void _calculate_line(self: Self,
                              float rel_depth,
                              float height,
                              float elevation,
                              int[3] calculation):
        
        # distance already does fisheye correction because it 
        # divides by the magnitude of ray (when "depth" is 1)
        calculation[0] = int(fmin( # line height
            self._tile_size / rel_depth * height,
            self._tile_size * self._max_line_height,
        ))
        # 2 was found through testing
        calculation[1] = calculation[0] + 2 # render_line_height
        # ^ pixel glitches at bottoms of wall are avoided

        # elevation offset
        calculation[2] = int( # offset
            (<float>self._player._render_elevation * 2
             - elevation * 2
             - height)
            * self._tile_size / 2 / rel_depth
        )
        
    cdef void _darken_line(self: Self, line: pg.Surface, float dist):
        cdef float factor

        if self._darkness:
            # magic numbers found through testing
            factor = -dist**0.9 * self._darkness / 7
            pg.transform.hsl(line, 0, 0, fmax(factor, -1), line)

    cdef void _render_walls_and_entities(self: Self,
                                         int width,
                                         int height,
                                         int horizon):
        cdef:
            object texture
            object manager = self._player._manager
            int i
            int x
            int render_back = 0
            int back_edge
            int dex # errors arise when is size_t
            int amount
            int render_y
            int y
            int line_height
            int render_line_height
            int old_y
            int old_render_end
            int back_line_height
            int render_back_line_height
            int render_end
            int start
            int end
            int axis
            int[2] dir
            int[3] calculation
            int offset
            int top
            int bottom
            int rect_height
            int texture_height
            int side
            float scale
            float dist
            float rel_depth
            float slope
            float disp_x
            float disp_y
            float step_x
            float step_y
            float factor
            float semiwidth = width / 2
            float mag
            float semitile_offset
            float semitile_width
            float final_rel_depth
            float part
            float[2] semitile_pos
            float[2] ray
            float[2] tile
            float[2] end_pos
            str tile_key
            str side_key
            dict data
            dict tilemap = manager._level._walls._tilemap
            tuple center
            _Limits limits = _limits_new(height / 2)
            # len_x and len_y are not one here because they do python interaction

            # entity stuff
            set searched_tiles = set() # empty tiles that could have entities
            # stores all walls and all that to be rendered
            # entities will be added after walls are computed
            list[width] render_buffer = []
            # colors of each tile (top/bottom rendering)
            dict colors = {} 
        
        
        # level manager stuff
        textures = manager._level._walls._textures
        
        # Wall Casting
        for x in range(width):
            render_buffer.append([])
            
            # float() will use double while <float> is float
            factor = 2 * x / <float>width - 1
            obj = self._yaw + self._player._semiplane * factor
            ray = (obj[0], obj[1])
            mag = sqrt(ray[0] * ray[0] + ray[1] * ray[1])

            end_pos = [self._player._pos[0], self._player._pos[1]]
            slope = ray[1] / ray[0] if ray[0] else 2147483647
            tile = [floorf(end_pos[0]), floorf(end_pos[1])]
            center = (tile[0] + 0.5, tile[1] + 0.5)
            tile_key = gen_tile_key(tile)
            data = tilemap.get(tile_key)
            dir = (ray[0] > 0, ray[1] > 0)
            # step for tile (for each displacement)
            step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
            step_y = dir[1] * 2 - 1 
            rel_depth = 0 # relative to yaw magnitude
            dist = 0
            
            _limits_reset(&limits)
            
            # render_back:
            # 0 to not render back of wall
            # 1 if rendering top of back of wall
            # 2 if rendering bottom of back of wall
            # I know it's funky but it works
            if data is not None:
                obj = data.get('semitile')
                if obj is None:
                    if self._player._render_elevation < data['elevation']:
                        render_back = 2
                        back_edge = 0
                    elif (self._player._render_elevation
                          > data['elevation'] + data['height']):
                        render_back = 1
                        back_edge = height
                else:
                    side = not obj['axis']
                    # ^ needed when is directly underneath player

            # keep on changing end_pos until hitting a wall (DDA)
            while dist < self._wall_render_distance:
                # Tile Rendering
                searched_tiles.add(tile_key)

                # no nested if statement on purpose
                if render_back and rel_depth: # top/bottom of wall rendering
                    self._calculate_line(
                        rel_depth,
                        data['height'],
                        data['elevation'],
                        calculation,
                    )
                    line_height, render_line_height, offset = calculation
                    y = horizon - line_height / 2 + offset
                    
                    if render_back == 1: # render back on top
                        render_y = horizon - line_height / 2 + offset
                        back_line_height = back_edge - render_y
                        side_key = 'top'
                    elif render_back == 2: # render back at bottom
                        render_y = back_edge
                        back_line_height = y + render_line_height - render_y
                        side_key = 'bottom'

                    render_back_line_height = back_line_height + 1
                    # this + 1 helps with pixel glitches (found by testing)
                    render_end = render_y + render_back_line_height
                    if (render_end > 0
                        and y < height
                        and not _limits_full(&limits, y, render_end)):
                        
                        color = colors.get(tile_key)
                        if not color:
                            line = pg.Surface((1, 1))
                            line.set_at((0, 0), data[side_key])
                            self._darken_line(
                                line, self._player._pos.distance_to(center),
                            )
                            color = line.get_at((0, 0))
                            colors[tile_key] = color
                        
                        # not sure if making the rect only the part onscreen 
                        # will improve performance that much
                        obj = _DepthBufferObject(
                            rel_depth,
                            (color, (x, render_y, 1, render_back_line_height)),
                            is_rect=1,
                        )
                        render_buffer[x].append(obj)

                        _limits_add(&limits, render_y, render_end)
                    render_back = 0

                tile_key = gen_tile_key(tile)
                data = tilemap.get(tile_key)
                if data is not None:
                    obj = data.get('semitile')
                    # this weird if statement structure is so that rendering
                    # semitiles works; if a semitile is directly underneath 
                    # the player, the old if statement structure wouldn't've 
                    # worked because rel_depth is 0
                    if obj is None:
                        if rel_depth:
                            self._calculate_line(
                                rel_depth,
                                data['height'],
                                data['elevation'],
                                calculation,
                            )
                            line_height = calculation[0]
                            render_line_height = calculation[1]
                            offset = calculation[2]
                            y = horizon - line_height / 2 + offset
                            render_end = y + render_line_height

                            center = (tile[0] + 0.5, tile[1] + 0.5)
                            # render back of tile on to
                            if horizon < y:
                                render_back = 1
                                back_edge = y
                            # render back of tile on bottom
                            elif horizon > render_end:
                                render_back = 2
                                back_edge = render_end
                            final_rel_depth = rel_depth
                            part = end_pos[side] % 1
                        else:
                            render_end = -1 # so it doesn't get rendered

                    else: # semitiles
                        # slow when directly next to wall because 
                        # these don't use rpa
                        render_back = 0
                        final_rel_depth = rel_depth
                        
                        # data about semitile
                        axis = obj['axis']
                        semitile_width = obj['width']
                        semitile_pos = obj['pos']
                        part = semitile_pos[not axis]
                        semitile_offset = semitile_pos[axis]
                        
                        # semitile pos gets repurposed as the final end pos
                        # I know this is weird but i really really really 
                        # really really don't want to have too much cdefs
                        semitile_pos = [end_pos[0], end_pos[1]]
                        # part also gets repurposed btw
                        # calculating displacement
                        if axis: # y-axis
                            if side:
                                disp_x = part - (not dir[0])
                            else:
                                disp_x = tile[0] + part - end_pos[0]
                            disp_y = disp_x * slope
                            if ray[0]:
                                final_rel_depth += disp_x / ray[0]
                            else:
                                final_rel_depth = 2147483647
                        else: # x-axis
                            if side:
                                disp_y = tile[1] + part - end_pos[1]
                            else:
                                disp_y = part - (not dir[1])
                            disp_x = disp_y / slope if slope else 2147483647
                            if ray[1]:
                                final_rel_depth += disp_y / ray[1]
                            else:
                                final_rel_depth = 2147483647
                        
                        semitile_pos[0] += disp_x
                        semitile_pos[1] += disp_y
                        part = semitile_pos[axis] - tile[axis]

                        # filter out lines that are erroneous
                        if (final_rel_depth > 0
                            # ^ have to use > 0 because could be negative
                            # ^ might need semitile_rel_depth and 
                            # semitile_rel_depth >= rel_depth but in my testing 
                            # nothing has gone wrong with > 0
                            and floorf(semitile_pos[0]) == tile[0]
                            and floorf(semitile_pos[1]) == tile[1]
                            and part >= semitile_offset
                            and part < semitile_offset + semitile_width):
                            
                            # final part
                            part = (part - semitile_offset) / semitile_width
                            dist = final_rel_depth * mag
                            self._calculate_line(
                                final_rel_depth,
                                data['height'],
                                data['elevation'],
                                calculation,
                            )
                            line_height = calculation[0]
                            render_line_height = calculation[1]
                            offset = calculation[2]
                            y = horizon - line_height / 2 + offset
                            render_end = y + render_line_height
                        else:
                            render_end = -1 # so it won't get rendered

                    # check if line is visible
                    if (render_end > 0
                        and y < height
                        and not _limits_full(&limits, y, render_end)):
                        # Transformation
                        texture = textures[data['texture']]
                        texture_height = texture.height
                        dex = int(floorf(part * <int>texture.width))
                        
                        # only resize the part that is visible (optimization)
                        scale = render_line_height / <float>texture_height
                        top = int(floorf(fmax(-y / scale, 0)))
                        bottom = int(ceilf(fmin(
                            (height - y) / scale, texture_height,
                        )))
                        rect_height = bottom - top
                        
                        old_y = y
                        old_render_end = render_end
                        # adjust variables accordingly
                        # for some reason needs angle brackets to use C
                        y += <int>ceilf(top * scale)
                        render_line_height = int(rect_height * scale)
                        render_end = y + render_line_height
                        
                        line = texture[dex]
                        line = pg.transform.scale(
                            line.subsurface(0, top, 1, rect_height),
                            (1, render_line_height)
                        )
                        self._darken_line(line, dist)

                        # if not semitile or if semitile and no alpha
                        # walls expected to have no transparency
                        if obj is None or not texture._transparency:
                            # Reverse Painter's Algorithm
                            amount = limits._amount
                            # not enumerated because + 1
                            for i in range(amount + 1):
                                end = limits._arr[i - 1]._end if i else 0
                                if i < amount:
                                    start = limits._arr[i]._start
                                else:
                                    start = height

                                if y < start and render_end > end:
                                    render_y = max(end, y)
                                    rect = (
                                        0,
                                        render_y - y,
                                        1,
                                        # + 1 was found through testing
                                        # helps w/ pixel glitches
                                        start - render_y + 1,
                                    )
                                    
                                    obj = _DepthBufferObject(
                                        final_rel_depth, (line, (x, render_y), rect),
                                    )
                                    render_buffer[x].append(obj)
                                    # rect bottom
                                    if start - y + 1 >= render_line_height:
                                        break
                            # old variables because of the full check
                            _limits_add(&limits, old_y, old_render_end)

                        else: # transparent semitiles
                            obj = _DepthBufferObject(
                                final_rel_depth,
                                (line, (x, y)),
                            )
                            render_buffer[x].append(obj)
                else:
                    # needed because render_back might stay as 1 or 2 when the 
                    # player is on the exact edge and there is no tile in the 
                    # next cast; will error when trying to render top/bottom of
                    # tile
                    render_back = 0

                # displacements until hit tile
                disp_x = tile[0] + dir[0] - end_pos[0]
                disp_y = tile[1] + dir[1] - end_pos[1]

                len_x = fabs(disp_x / ray[0]) if ray[0] else 2147483647
                len_y = fabs(disp_y / ray[1]) if ray[1] else 2147483647
                if len_x < len_y:
                    tile[0] += step_x
                    end_pos[0] += disp_x
                    end_pos[1] += disp_x * slope
                    rel_depth += len_x
                    side = 1
                else:
                    tile[1] += step_y
                    end_pos[0] += disp_y / slope if slope else 2147483647
                    end_pos[1] += disp_y
                    rel_depth += len_y
                    side = 0
                dist = rel_depth * mag

        _limits_destroy(&limits)
        
        cdef:
            float[2] projection
            float[2] ratios
            float[3] rel_vector
            int[2] pos
            float scale_x
            float scale_y
            int left
            int right
            int rect_width
            int render_x
            int render_width
            int render_height
            int texture_width
            # top, bottom, rect_height, and texture_height were already
            # declared above
            set entities
        # Entity Rendering
        for tile_key in searched_tiles:
            entities = manager._sets.get(tile_key)
            if entities:
                for entity in entities:
                    obj = entity.vector3 - self._player._render_vector3
                    # rotation
                    obj.rotate_y_ip(self._player._yaw_value)
                    rel_vector = [obj[0], obj[1], obj[2]]

                    if rel_vector[2] >= self._min_entity_depth:
                        # taking ratio of x:z and y:z
                        ratios = (
                            rel_vector[0] / rel_vector[2],
                            rel_vector[1] / rel_vector[2],
                        )

                        # final projection
                        projection = (
                            -ratios[0]
                            * self._yaw_magnitude
                            * semiwidth
                            + semiwidth,
                            -ratios[1]
                            * self._yaw_magnitude
                            * self._tile_size
                            + horizon,
                        )

                        rel_depth = rel_vector[2] / self._yaw_magnitude

                        texture = entity.texture
                        texture_width = texture.width
                        texture_height = texture.height

                        # only resize the part that is visible (optimization)
                        # this optimization is a little slower if entity is 
                        # fully in frame but i think it is worth it
                        render_width = int(
                            <float>entity._render_width
                            * semiwidth
                            / rel_depth
                        )
                        render_height = int(
                            <float>entity._render_height
                            * self._tile_size
                            / rel_depth
                        )
                        render_x = int(projection[0] - render_width / 2)
                        y = int(projection[1] - render_height)
                        
                        if (y < height
                            and y + render_height > 0
                            and render_x < width
                            and render_x + render_width > 0):
                            
                            # y-axis calculations
                            scale_y = render_height / <float>texture_height
                            top = int(floorf(fmax(-y / scale_y, 0)))
                            bottom = int(ceilf(
                                fmin((height - y) / scale_y, texture_height),
                            ))
                            rect_height = bottom - top
                            # adjust variables accordingly
                            # for some reason needs angle brackets to use C
                            y += <int>ceilf(top * scale_y)
                            render_height = int(rect_height * scale_y)
                            
                            # x-axis calculations
                            scale_x = render_width / <float>texture_width
                            left = int(floorf(fmax(-render_x / scale_x, 0)))
                            right = int(ceilf(fmin(
                                (width - render_x) / scale_x, texture_width
                            )))
                            rect_width = right - left
                            # adjust variables accordingly
                            # for some reason needs angle brackets to use C
                            render_x += <int>ceilf(left * scale_x)
                            render_width = int(rect_width * scale_x)

                            # getting subsurface
                            texture = texture.subsurface(
                                left, top, rect_width, rect_height,
                            )
                            
                            # scaling and lighting
                            # order depends on if scale is greater or less
                            # (optimization)
                            # I know this might be long but it works so yes
                            # lighting
                            if not entity._glowing and self._darkness:
                                factor = (
                                    -rel_vector[2]**0.9 * self._darkness / 7
                                )
                                if (render_width * render_height
                                    <= rect_width * rect_height):

                                    texture = pg.transform.scale(
                                        texture,
                                        (render_width, render_height),
                                    )
                                    pg.transform.hsl(
                                        texture,
                                        0, 0, fmax(factor, -1),
                                        texture,
                                    )
                                else:
                                    texture = pg.transform.scale(
                                        pg.transform.hsl(
                                            texture, 0, 0, fmax(factor, -1),
                                        ),
                                        (render_width, render_height),
                                    )
                            else: # no lighting
                                texture = pg.transform.scale(
                                    texture,
                                    (render_width, render_height),
                                )

                            # add to depth buffer
                            for i in range(render_width):
                                pos = (render_x + i, y)
                                if 0 <= pos[0] < width:
                                    obj = _DepthBufferObject(
                                        rel_depth,
                                        (texture,
                                         pos,
                                         (i, 0, 1, render_height)),
                                    )
                                    bisect.insort_left(
                                        render_buffer[pos[0]], obj,
                                    )

        for x in range(width):
            blits = render_buffer[x]
            # the objects are added in closest-to-farthest
            # reverse so that depth buffer works
            for i in range(len(blits) - 1, -1, -1):
                obj = blits[i]
                if obj._is_rect:
                    pg.draw.rect(self._walls_and_entities, *obj._args)
                else:
                    self._walls_and_entities.blit(*obj._args)

    def _render_weapon(self: Self, int width, int height, surf: pg.Surface):
        cdef:
            object weapon_surf = self._player._weapon_surf
            float[2] pos = (
                <float>self._player._render_weapon_pos[0] * width
                - <int>weapon_surf.width / 2,
                <float>self._player._render_weapon_pos[1] * height,
            )
        surf.blit(weapon_surf, pos)

    def render(self: Self, surf: pg.Surface) -> None:
        cdef:
            int width = surf.width
            int height = surf.height
            int horizon = int(self._horizon * height)

        self._yaw = self._player._yaw * self._yaw_magnitude
        surf.fill((0, 0, 0))
        self._ceiling = None
        self._floor = None
        # the per-pixel alpha with (0, 0, 0, 0) doesn't seem to affect
        # fps at all
        self._walls_and_entities = pg.Surface((width, height), pg.SRCALPHA)
        self._walls_and_entities.fill((0, 0, 0, 0))
        self._weapon = None
        
        # Threads
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
        
        # Blits
        if self._floor is not None:
            surf.blit(self._floor, (0, horizon))
        if self._ceiling is not None:
            surf.blit(self._ceiling, (0, 0))
        surf.blit(self._walls_and_entities, (0, 0))
        self._render_weapon(width, height, surf)

