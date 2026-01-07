import time
import math
from typing import Self

import pygame as pg

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
        pg.display.set_caption('Computergenesis Level Editor')
        self._running = 0

        # Editor Variables
        pg.key.set_repeat(300, 100)

        self._colors = {
            'fill': (0, 0, 0),
            'grid': (255, 255, 255),
            'top': (0, 0, 0),
            'bottom': (0, 0, 0),
        }
        
        # zoom
        self._zoom_step = 2
        self._min_zoom = 8 # anything below tanks performance
        self._zoom = 16
        
        # Settings for current tile
        self._tile = {
            'texture': 0,
            'elevation': 0,
            'height': 1,
            'top': self._colors['top'],
            'bottom': self._colors['bottom'],
        }

        self._pos = pg.Vector2(0, 0)
        self._tilemap = {}

    def _draw_grid(self: Self) -> None:
        for y in range(self._screen.height // self._zoom):
            for x in range(self._screen.width // self._zoom):
                pos = (
                    self._pos[0] * self._zoom % self._zoom + x * self._zoom,
                    self._pos[1] * self._zoom % self._zoom + y * self._zoom,
                )
                self._screen.set_at(pos, self._colors['grid'])

    def _draw_tiles(self: Self) -> None:
        NotImplemented

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.KEYDOWN:
                    # Zoom
                    if event.key == pg.K_z:
                        self._zoom += self._zoom_step
                    elif event.key == pg.K_x:
                        self._zoom = max(
                            self._zoom - self._zoom_step,
                            self._min_zoom,
                        )
                # Editing
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pass

            mouse = pg.mouse.get_pressed()
            if mouse[1]:
                pos = (
                    self._pos[0] + event.pos[0] / self._zoom,
                    self._pos[1] + event.pos[1] / self._zoom,
                )
                tile_key = gen_tile_key(pos)
                self._tilemap[tile_key] = self._tile.copy()

            keys = pg.key.get_pressed()
            movement = pg.Vector2(
                keys[pg.K_d] - keys[pg.K_a],
                keys[pg.K_s] - keys[pg.K_w],
            )
            self._pos += movement * 0.05
            
            self._screen.fill(self._colors['fill'])
            self._draw_grid()
            pg.display.set_caption(str(1 / delta_time))

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

