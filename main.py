import time
import math
import random
from typing import Self

import pygame as pg

from modules.level import Level
from modules.level import ColumnTexture
from modules.level import Walls
from modules.level import Floor
from modules.level import Sky 
from modules.level import Entity 
from modules.level import Player
from modules.level import EntityManager 
from modules.renderer import Camera

class Game(object):

    _SCREEN_SIZE = (960, 720)
    _SURF_RATIO = (3, 3)
    _SURF_SIZE = (
        int(_SCREEN_SIZE[0] / _SURF_RATIO[0]),
        int(_SCREEN_SIZE[1] / _SURF_RATIO[1]),
    )
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
        pg.display.set_caption('Pygame Raycaster')
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
            '8;11': {'elevation': -0.75, 'height': 1, 'texture': 0}, 
            '9;11': {'elevation': 0, 'height': 1, 'texture': 0}, 
            '10;11': {'elevation': 0, 'height': 1, 'texture': 0},
        }

        self._wall_textures = (
            ColumnTexture(pg.image.load('data/images/redbrick.png').convert()),
        )

        self._player = Player()
        entities = {
            0: Entity(
                height=0.6,
                texture=pg.image.load('data/images/GrenadeZombie.png')
            ),
        }
        entities[0].pos = (6.5, 3)
        self._entities = EntityManager(self._player, entities)

        self._level = Level(
            floor=Floor(pg.image.load('data/images/wood.png').convert()),
            ceiling=Sky(pg.image.load('data/images/nightsky.png').convert()),
            walls=Walls(walls, self._wall_textures),
            entities=self._entities,
        )
        pg.mouse.set_relative_mode(1)

        self._camera = Camera(
            fov=90,
            tile_size=self._SURF_SIZE[0] / 2,
            wall_render_distance=8,
            player=self._player,
        )
        self._player.pos = (6.5, 6)
        self._camera.horizon = 0.5
        self._level_timer = 0

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        
        gun = pg.image.load('data/images/gun.png')

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            self._level_timer += delta_time

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                # temp
                elif event.type == pg.MOUSEMOTION:
                    rel = pg.mouse.get_rel()
                    self._player.yaw += rel[0] * 0.2

            keys = pg.key.get_pressed()
            movement = (
                (keys[pg.K_w] - keys[pg.K_s]) * 0.05,
                (keys[pg.K_d] - keys[pg.K_a]) * 0.05,
                (keys[pg.K_RIGHT] - keys[pg.K_LEFT]) * 2.5,
                (keys[pg.K_DOWN] - keys[pg.K_UP]),
            )
            
            self._player.update(
                rel_game_speed,
                self._level_timer,
                movement[0],
                movement[1],
                movement[2],
            )
            self._camera.horizon -= movement[3] * 0.025

            # temp super basic nextbot
            rel_vector = (self._player.vector2 - self._entities[0].vector2)
            if rel_vector and self._level_timer > 5:
                self._entities[0].velocity2 = (rel_vector.normalize() * 0.05).rotate(random.randint(-23, 23))
            self._entities.update(rel_game_speed, self._level_timer)
            if self._entities[0].vector2.distance_to(self._player.vector2) < 0.25:
                print('score:', int(self._level_timer) * 100)
                self._running = 0
            self._level._walls._tilemap['8;11']['elevation'] = math.sin(self._level_timer)

            self._camera.render(self._surface)
            # self._surface.blit(gun, (self._SURF_SIZE[0] - gun.width, self._SURF_SIZE[1] - gun.height))
            pg.display.set_caption(str(1 / delta_time) if delta_time else 'inf')

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.flip()

        pg.quit()

if __name__ == '__main__':
    Game().run()

