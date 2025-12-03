import math
import bisect
from numbers import Real
from typing import Self
from typing import Union
from threading import Thread
from collections.abc import Sequence

import numpy as np
import pygame as pg
from pygame.typing import Point

from modules.level import ColumnTexture
from modules.level import Sky
from modules.level import Player


# 1-Dimensional integer
class Limits(object):
    def __init__(self: Self) -> None:
        self._limits = []

    def add(self: Self, start: int, end: int) -> None:
        # https://stackoverflow.com/a/15273749
        bisect.insort(self._limits, [int(start), int(end)])

        output = []
        for limit in self._limits:
            if output and output[-1][1] >= limit[0] - 1:
                output[-1][1] = max(output[-1][1], limit[1])
            else:
                output.append(limit)
        self._limits = output

    def full(self: Self, start: int, end: int) -> bool:
        return (self._limits
                and self._limits[0][0] <= start
                and self._limits[0][1] >= end)

    def get(self: Self) -> set:
        return self._limits.copy()


class Camera(object):

    class _DepthBufferObject(object):
        def __init__(self: Self, depth: Real, args: tuple):
            self._args = args # blit args
            self._depth = depth

        def __lt__(self: Self, obj: Self):
            # so objects are rendered farthest to last
            return self._depth < obj._depth 

    def __init__(self: Self,
                 fov: Real,
                 tile_size: Real,
                 wall_render_distance: Real,
                 player: Player,
                 bob_strength: Real=0.0375,
                 bob_frequency: Real=10,
                 line_addition: int=2,
                 min_entity_dist: Real=0.05) -> None:
        
        try:
            self._yaw_magnitude = float(1 / math.tan(math.radians(fov) / 2))
        except ValueError:
            self._yaw_magnitude = 0
        # already sets yaw V
        self.fov = min(abs(fov), 180) # _fov is in degrees
        self._horizon = 0.5
        self._player = player
        self._tile_size = tile_size
        self._wall_render_distance = wall_render_distance
        self._line_addition = line_addition
        self._min_entity_dist = min_entity_dist

        self.bob_strength = bob_strength
        self.bob_frequency = bob_frequency

    @property
    def bob_strength(self: Self) -> Real:
        return self._bob_stength

    @bob_strength.setter
    def bob_strength(self: Self, value: Real) -> None:
        value = pg.math.clamp(value, -0.5, 0.5)
        self._bob_strength = value
        self._player._settings['bob_strength'] = value

    @property
    def bob_frequency(self: Self) -> Real:
        return self._bob_frequency

    @bob_frequency.setter
    def bob_frequency(self: Self, value: Real) -> None:
        self._bob_frequency = value
        self._player._settings['bob_frequency'] = value

    @property
    def player(self: Self) -> Player:
        return self._player

    @player.setter
    def player(self: Self, value: Player) -> None:
        self._player._settings['bob_frequency'] = 0
        self._player._settings['bob_strength'] = 0
        self._player = value
        value._settings['bob_frequency'] = self._bob_frequency
        value._settings['bob_strength'] = self._bob_strength

    @property
    def fov(self: Self) -> Real:
        return self._fov

    @fov.setter
    def fov(self: Self, value: Real) -> None:
        semiradians = math.radians(value / 2)

        self._fov = value
        self._fov_mult = math.tan(semiradians)
        self._yaw_magnitude = float(1 / self._fov_mult)

    @property
    def horizon(self: Self) -> Real:
        return self._horizon

    @horizon.setter
    def horizon(self: Self, value: Real) -> None:
        self._horizon = pg.math.clamp(value, 0, 1)

    @property
    def tile_size(self: Self) -> Real:
        return self._tile_size

    @tile_size.setter
    def tile_size(self: Self, value: Real) -> None:
        self._tile_size = value

    @property
    def wall_render_distance(self: Self) -> Real:
        return self._wall_render_distance

    @wall_render_distance.setter
    def wall_render_distance(self: Self, value: Real) -> None:
        self._wall_render_distance = value

    @property
    def line_addition(self: Self) -> int:
        return self._line_addition

    @line_addition.setter
    def line_addition(self: Self, value: int) -> None:
        self._line_addition = value

    @property
    def min_entity_dist(self: Self) -> Real:
        return self._min_entity_dist

    @min_entity_dist.setter
    def min_entity_dist(self: Self, value: Real) -> None:
        self._min_entity_dist = value

    def _render_floor_and_ceiling(self: Self,
                                  width: Real,
                                  height: Real,
                                  horizon: Real) -> None:

        def _generate_array(mult, offsets, texture):
            # takes into account elevation
            # basically, some of the vertical camera plane is below the ground
            # intersection between ground and ray is behind the plane
            # (not in front); we use this multiplier
            start_points_x = mult / offsets * rays[0][0]
            start_points_y = mult / offsets * rays[0][1]

            end_points_x = mult / offsets * rays[1][0]
            end_points_y = mult / offsets * rays[1][1]

            step_x = (end_points_x - start_points_x) / width
            step_y = (end_points_y - start_points_y) / width
            
            x_points = self._player._pos.x + start_points_x + step_x * x_pixels
            y_points = self._player._pos.y + start_points_y + step_y * x_pixels
            
            # change the multiplier before the mod to change size of texture
            texture_xs = np.floor(x_points * 1 % 1 * texture.width)
            texture_ys = np.floor(y_points * 1 % 1 * texture.height)
            texture_xs = texture_xs.astype('int')
            texture_ys = texture_ys.astype('int')

            array = texture[texture_xs, texture_ys]

            return array

        # Setup (in both floor & ceiling)
        rays = (self._yaw - self._player._semiplane,
                self._yaw + self._player._semiplane)
        x_pixels = np.linspace(0, width, num=width, endpoint=0) 
        x_pixels = np.vstack(x_pixels) # all x values

        # Sky stuff
        semiheight = height / 2
        sky_speed = width / 100

        # Actual Render
        obj = self._player._manager._level._floor
        if obj and isinstance(obj, Sky):
            rect = pg.Rect(0, horizon, width, height - horizon)
            if rect.top >= 0 and rect.bottom < obj._height:
                self._floor = obj.scroll(
                    -self._player.yaw * sky_speed,
                    width,
                    obj._height,
                ).subsurface(rect)
        else:
            # Floor Casting
            difference = int(height - horizon)
            amount_of_offsets = min(difference, height)

            if difference >= 1:
                offsets = np.linspace(
                    max(-horizon, 1),
                    amount_of_offsets + max(-horizon, 0),
                    num=amount_of_offsets,
                    endpoint=0
                ) # offsets from horizon to render

                mult = self._tile_size * self._player._render_elevation
                texture = obj
                floor = _generate_array(mult, offsets, texture)

                # lighting (maybe temp?)
                offsets = np.vstack(offsets)
                lighting = np.minimum(offsets / semiheight, 1)**0.97
                floor = floor * lighting
                # can't do *= ^
                self._floor = pg.surfarray.make_surface(floor)

        obj = self._player._manager._level._ceiling
        # Ceiling Casting
        if obj and isinstance(obj, Sky):
            rect = pg.Rect(0, obj._height - horizon, width, horizon)
            if rect.top > 0 and rect.bottom <= obj._height:
                self._ceiling = obj.scroll(
                    -self._player.yaw * sky_speed,
                    width,
                    obj._height,
                ).subsurface(rect)
        else:
            amount_of_offsets = int(min(horizon, height))
            if horizon >= 1:
                offsets = np.linspace(
                    amount_of_offsets,
                    0,
                    num=amount_of_offsets,
                    endpoint=0
                ) # offsets from horizon to render

                mult = self._tile_size * (1 - self._player._render_elevation)
                texture = obj
                ceiling = _generate_array(mult, offsets, texture)

                # lighting (maybe temp ?)
                offsets = np.vstack(offsets)
                lighting = np.minimum(offsets / semiheight, 1)**0.97
                ceiling = ceiling * lighting
                # can't do *= ^
                self._ceiling = pg.surfarray.make_surface(ceiling)

    def _render_walls_and_entities(self: Self,
                                   width: Real,
                                   height: Real,
                                   horizon: Real) -> None:

        semiwidth = width / 2

        # the per-pixel alpha with (0, 0, 0, 0) doesn't seem to affect
        # fps at all
        self._walls_and_entities = pg.Surface((width, height), pg.SRCALPHA)
        self._walls_and_entities.fill((0, 0, 0, 0))
        
        manager = self._player._manager
        tilemap = manager._level._walls._tilemap
        textures = manager._level._walls._textures
        
        # stores all walls and all that to be rendered
        # entities will be added after walls are computed
        render_buffer = [] 
        
        # entity stuff
        empty_tiles = set() # tiles checked without tiles

        # Wall Casting
        for x in range(width):
            render_buffer.append([]) # add empty list

            ray = self._yaw + self._player._semiplane * (2 * x / width - 1)
            mag = ray.magnitude()

            has_hit = 0
            end_pos = self._player._pos.copy()
            slope = ray.y / ray.x if ray.x else math.inf
            tile = pg.Vector2(math.floor(end_pos.x), math.floor(end_pos.y))
            dir = (ray.x > 0, ray.y > 0)
            depth = 0
            dist = 0
            
            limits = Limits()

            # keep on changing end_pos until hitting a wall (DDA)
            while dist < self._wall_render_distance:
                # Tile Rendering
                tile_key = f'{int(tile.x)};{int(tile.y)}'
                if tilemap.get(tile_key) != None:
                    if depth and not limits.full(0, height):

                        data = tilemap[tile_key] # tile data

                        # distance already does fisheye correction because it 
                        # divides by the magnitude of ray (when "depth" is 1)
                        line_height = min(
                            self._tile_size / depth * data['height'],
                            height * 10,
                        )
                        render_line_height = line_height + self._line_addition
                        # ^ pixel glitches at bottoms of wall are avoided
                        # elevation offset
                        offset = ((self._player._render_elevation * 2
                                   - data['elevation'] * 2
                                   - data['height'])
                                  * self._tile_size / 2 / depth)
                        # check if line is visible
                        if (-line_height / 2 - offset < horizon 
                            < height + line_height / 2 - offset):
                            
                            # Transformation
                            texture = data['texture']
                            dex = math.floor(end_pos[side] % 1
                                             * textures[texture].width)
                            line = pg.transform.scale(
                                textures[texture][dex],
                                (1, render_line_height)
                            )

                            # temp
                            pg.transform.hsl(line, 0, 0, max(-dist / 6, -1), line)
                            
                            # Reverse Painter's Algorithm
                            y = horizon - line_height / 2 + offset
                            render_end = y + render_line_height
                            segments = limits._limits
                            amount = len(segments)
                            # not enumerated because + 1
                            for i in range(amount + 1):
                                end = segments[i - 1][1] if i else 0
                                start = segments[i][0] if i < amount else height

                                if y < start and render_end > end:
                                    render_y = max(end, y)
                                    rect = pg.Rect(
                                        0, render_y - y, 1, start - render_y + 1,
                                    )
                                    
                                    obj = self._DepthBufferObject(
                                        depth, (line, (x, render_y), rect),
                                    )
                                    render_buffer[x].append(obj)

                                    if rect.bottom >= render_line_height:
                                        break

                            limits.add(y, render_end)
                else:
                    empty_tiles.add(tile_key)

                # displacements until hit tile
                disp_x = tile.x + dir[0] - end_pos.x
                disp_y = tile.y + dir[1] - end_pos.y
                # step for tile (for each displacement)
                step_x = dir[0] * 2 - 1 # 1 if yes, -1 if no
                step_y = dir[1] * 2 - 1 

                len_x = abs(disp_x / ray.x) if ray.x else math.inf
                len_y = abs(disp_y / ray.y) if ray.y else math.inf
                if len_x < len_y:
                    tile.x += step_x
                    end_pos.x += disp_x
                    end_pos.y += disp_x * slope
                    depth += len_x
                    side = 1
                else:
                    tile.y += step_y
                    end_pos.x += disp_y / slope if slope else math.inf
                    end_pos.y += disp_y
                    depth += len_y
                    side = 0
                dist = depth * mag
            # the objects are added in closest-to-farthest
            # reverse so that depth buffer works
        
        # Entity Rendering
        for tile_key in empty_tiles:
            entities = manager._sets.get(tile_key)
            if entities:
                for entity in entities:
                    rel_vector = entity.vector3 - self._player._render_vector3
                    # rotation
                    rel_vector.rotate_y_ip(self._player._yaw_value)
                    depth = rel_vector.z
                    if depth >= self._min_entity_dist:
                        ratios = (
                            rel_vector.x / rel_vector.z,
                            rel_vector.y / rel_vector.z,
                        )
                        # final projection
                        mult = self._fov_mult * semiwidth
                        projection = pg.Vector2(
                            -ratios[0] * mult + semiwidth,
                            -ratios[1] * mult + horizon,
                        )
                        
                        dex = int(projection.x)
                        scale = self._tile_size / depth
                        texture = pg.transform.scale(
                            entity._texture,
                            (entity._width * scale,
                             entity._height * scale),
                        )
                        for i in range(texture.width):
                            pos = (
                                int(dex - texture.width / 2 + i),
                                projection.y - texture.height,
                            )
                            if 0 < pos[0] < width:
                                obj = self._DepthBufferObject(
                                    depth,
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
        width = surf.width
        height = surf.height

        surf.fill((0, 0, 0))
        self._yaw = self._player._yaw * self._yaw_magnitude
        self._ceiling = None
        self._floor = None
 
        horizon = self._horizon * height
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

