import time
from typing import Self

import pygame as pg

from modules.level import Level
from modules.level import WallTexture
from modules.level import Walls
from modules.level import Floor
from modules.level import _FALLBACK_SURF
from modules.renderer import Camera
from modules.entities import Player
from modules.entities import EntityManager


class Game(object):

    _SCREEN_SIZE = (960, 720)
    _SURF_RATIO = (3, 3)
    _SURF_SIZE = (int(_SCREEN_SIZE[0] / _SURF_RATIO[0]),
                  int(_SCREEN_SIZE[1] / _SURF_RATIO[1]))
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
        pg.display.set_caption('Drought')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        
        walls = {
            '0;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '1;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '2;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '3;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '4;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '5;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '6;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '7;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '8;0': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '9;0': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;0': {'elevation': 0, 'height': 1, 'texture': 0},
            '0;1': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '8;1': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;1': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '3;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '8;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '9;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;2': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;3': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;3': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;3': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;3': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '8;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '9;4': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;4': {'elevation': 0, 'height': 1, 'texture': 0},
            '0;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '3;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '8;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '9;5': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;5': {'elevation': 0, 'height': 1, 'texture': 0},
            '0;6': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;6': {'elevation': 0, 'height': 1, 'texture': 0},
            '0;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '1;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '6;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;7': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;8': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;8': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;8': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;8': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;8': {'elevation': 0, 'height': 1, 'texture': 0},
            '0;9': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;9': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;9': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;9': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;9': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;10': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;10': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;10': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;10': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;10': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '0;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '1;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '2;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '3;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '4;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '5;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '6;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '7;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '8;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '9;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;11': {'elevation': 0, 'height': 1, 'texture': 0},
        }
        
        self._wall_textures = (
            WallTexture(_FALLBACK_SURF),
        )

        self._level = Level(
            Floor('data/images/greystone.png'),
            (Walls(walls, self._wall_textures),),
       )

        self._player = Player(self._level)
        self._camera = Camera(
            90, 
            self._SURF_SIZE[0] / 2,
            6,
            self._player,
        )
        self._player.pos = (6.5, 6)
        self._camera.horizon = self._SURF_SIZE[1] / 2
        self._level_timer = 0
    
    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        second = pg.event.custom_type()
        pg.time.set_timer(second, 1000)
        framerates = []

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            self._level_timer += delta_time

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == second:
                    pg.display.set_caption(str(sum(framerates) / len(framerates)))
                    framerates = []
                self._player.handle_events(event)
            framerates.append(1 / delta_time)

            self._player.update(rel_game_speed, self._level_timer)
            self._camera.render(self._surface)

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.update()

        pg.quit()

if __name__ == '__main__':
    Game().run()
