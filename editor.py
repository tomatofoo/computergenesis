import time
import math
from typing import Self

import pygame as pg

from data.levels import LEVELS
from modules.utils import FALLBACK_SURF
from modules.utils import gen_tile_key


class Game(object):

    _SCREEN_SIZE = (960, 720)
    _SCREEN_FLAGS = pg.RESIZABLE | pg.SCALED
    _GAME_SPEED = 60

    def __init__(self: Self) -> None:
        pg.init()

        self._settings = {
            'vsync': 1,
        }
        self._screen = pg.display.set_mode(
            self._SCREEN_SIZE,
            flags=self._SCREEN_FLAGS,
            vsync=self._settings['vsync']
        )
        pg.display.set_caption('Level Editor')
        self._running = 0

        # Editor Variables
        pg.key.set_repeat(300, 100)

        self._colors = {
            'fill': (0, 0, 0),
            'grid': (255, 255, 255),
            'top': (0, 0, 255), # default top
            'bottom': (255, 0, 0), # default bottom
            'remove': (255, 0, 0), # remove tool
            'select': (0, 255, 0), # select tool
        }

        self._keys = {
            'mod': (pg.K_LSHIFT, pg.K_RSHIFT),
            'mod2': (pg.K_LCTRL, pg.K_RCTRL),
            'zoom_in': pg.K_z,
            'zoom_out': pg.K_x,
            'vertical_increase': pg.K_UP,
            'vertical_decrease': pg.K_DOWN,
            'do': pg.K_z, # undo redo
            'place': pg.K_b,
            'remove': pg.K_e,
            'select': pg.K_v,
        }
        
        # tools
        self._tool = 'place' # place, remove, select
        self._place_alpha = 128 # alpha of 'ghost' tile when placing
        self._remove_width = 1
        self._select_pos = (0, 0) # original tile pos for selection

        # Zoom
        self._zoom_step = 2
        self._min_zoom = 8 # anything below tanks performance
        self._zoom = 16 # tile size
       
        # Settings for current tile
        self._data = {
            'texture': 0,
            'elevation': 0,
            'height': 1,
            'top': self._colors['top'],
            'bottom': self._colors['bottom'],
        }

        self._level = None
        self._wall_textures = []
        self._tilemap = {}
        
        # Pos for top left
        self._pos = pg.Vector2(0, 0)

        # History
        self._history = [{}] # pos: (prev, new)
        self._change = 0

    def _get_screen_pos(self: Self, x: int, y: int) -> None:
        return (
            (math.floor(self._pos[0]) + x - self._pos[0]) * self._zoom,
            (math.floor(self._pos[1]) + y - self._pos[1]) * self._zoom,
        )

    def _draw_grid(self: Self) -> None:
        for y in range(math.ceil(self._SCREEN_SIZE[1] / self._zoom) + 1):
            for x in range(math.ceil(self._SCREEN_SIZE[0] / self._zoom) + 1):
                self._screen.set_at(
                    self._get_screen_pos(x, y),
                    self._colors['grid'],
                )

    def _draw_tile(self: Self,
                   alpha: Optional[Real],
                   data: dict,
                   pos: tuple) -> None:

        surf = pg.Surface((self._zoom, self._zoom))
        semizoom = self._zoom / 2
        quarterzoom = self._zoom / 4
        # Texture
        try:
            texture = self._wall_textures[self._data['texture']]._surf
        except:
            texture = FALLBACK_SURF
        surf.blit(
            pg.transform.scale(texture, (semizoom, semizoom)),
            (0, 0),
        )
        # Colors
        rect = (semizoom, 0, semizoom, quarterzoom)
        pg.draw.rect(surf, data['top'], rect)
        rect = (semizoom, quarterzoom, semizoom, quarterzoom)
        pg.draw.rect(surf, data['bottom'], rect)
        # Draw
        surf.set_alpha(alpha)
        self._screen.blit(surf, pos)

    def _draw_tiles(self: Self) -> None:
        for y in range(math.ceil(self._SCREEN_SIZE[1] / self._zoom) + 1):
            for x in range(math.ceil(self._SCREEN_SIZE[0] / self._zoom) + 1):
                tile = (math.floor(self._pos[0]) + x,
                        math.floor(self._pos[1]) + y)
                tile_key = gen_tile_key(tile)
                data = self._tilemap.get(tile_key)
                if data is not None:
                    self._draw_tile(None, data, self._get_screen_pos(x, y)) 

    def _draw_panel(self: Self) -> None:
        pass

    def _draw_tool(self: Self, mouse_pos: tuple) -> None:
        x = self._zoom * (
            math.floor(self._pos[0] + mouse_pos[0] / self._zoom)
            - self._pos[0]
        )
        y = self._zoom * (
            math.floor(self._pos[1] + mouse_pos[1] / self._zoom)
            - self._pos[1]
        )
        if self._tool == 'place':
            self._draw_tile(self._place_alpha, self._data, (x, y))
        elif self._tool == 'remove':
            pg.draw.rect(
                self._screen,
                self._colors['remove'],
                (x, y, self._zoom, self._zoom),
                width=self._remove_width,
            )
        elif self._tool == 'select':
            pass

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            keys = pg.key.get_pressed()
            mod = any(keys[key] for key in self._keys['mod'])
            mod2 = any(keys[key] for key in self._keys['mod2'])
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.KEYDOWN:
                    if not mod2:
                        if not mod:
                            # zoom
                            if event.key == self._keys['zoom_in']:
                                self._zoom += self._zoom_step
                            elif event.key == self._keys['zoom_out']:
                                self._zoom = max(
                                    self._zoom - self._zoom_step,
                                    self._min_zoom,
                                )
                            elif event.key == self._keys['place']:
                                self._tool = 'place'
                            elif event.key == self._keys['remove']:
                                self._tool = 'remove'
                            elif event.key == self._keys['select']:
                                self._tool = 'select'
                        # Height / Elevation
                        if event.key == self._keys['vertical_increase']:
                            if mod:
                                self._data['elevation'] += 0.05
                            else:
                                self._data['height'] += 0.05
                        elif event.key == self._keys['vertical_decrease']:
                            if mod:
                                self._data['elevation'] -= 0.05
                            else:
                                self._data['height'] -= 0.05
                    # History
                    if mod2 and event.key == self._keys['do']:
                        # redo
                        if mod:
                            if self._change < len(self._history) - 1:
                                change = self._history[self._change]
                                for key, value in change.items():
                                    if value[1] is None:
                                        if self._tilemap.get(key) is not None:
                                            self._tilemap.pop(key)
                                    else:
                                        self._tilemap[key] = value[1]
                                self._change += 1
                        # undo
                        elif self._change > 0:
                            self._change -= 1
                            change = self._history[self._change]
                            for key, value in change.items():
                                if value[0] is None:
                                    if self._tilemap.get(key) is not None:
                                        self._tilemap.pop(key)
                                else:
                                    self._tilemap[key] = value[0]

                # Editing
                elif event.type == pg.MOUSEBUTTONUP: # history
                    if self._history[-1]:
                        if self._change < len(self._history) - 1:
                            # cut off tree after user makse a change
                            self._history = [
                                *(self._history[:self._change]),
                                self._history[-1],
                            ]
                        self._change = len(self._history)
                        self._history.append({})
            
            mouse = pg.mouse.get_pressed()
            mouse_pos = pg.mouse.get_pos()
            pos = (
                self._pos[0] + mouse_pos[0] / self._zoom,
                self._pos[1] + mouse_pos[1] / self._zoom,
            )
            tile_key = gen_tile_key(pos)
            # set
            tile_data = self._tilemap.get(tile_key)
            if mouse[0]:
                if self._tool == 'place':
                    if tile_data != self._data:
                        data = self._data.copy()
                        self._history[-1][tile_key] = (tile_data, data)
                        self._tilemap[tile_key] = data
                # remove
                elif self._tool == 'remove' and tile_data is not None:
                    self._history[-1][tile_key] = (
                        self._tilemap.pop(tile_key),
                        None,
                    )
            movement = pg.Vector2(
                keys[pg.K_d] - keys[pg.K_a],
                keys[pg.K_s] - keys[pg.K_w],
            )
            if mod:
                self._pos += movement * 0.125
            else:
                self._pos += movement * 0.05

            
            self._screen.fill(self._colors['fill'])
            self._draw_grid()
            self._draw_tiles()
            self._draw_panel()
            self._draw_tool(mouse_pos)

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

