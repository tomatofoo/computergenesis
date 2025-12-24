#!/usr/bin/env python3

import time
import math
import json
import random
from typing import Self

import pygame as pg
from pygame import mixer as mx

from modules.level import ColumnTexture
from modules.level import Walls
from modules.level import Floor
from modules.level import Sky 
from modules.level import Level
from modules.entities import Entity 
from modules.entities import Player
from modules.entities import EntityManager 
from modules.camera import Camera


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
        
        with open('data/map.json', 'r') as file:
            walls = json.loads(file.read())
            
        walls['10;7'] = {
            'elevation': 0,
            'height': 1,
            'texture': 0,
            'semitile': {'axis': 0, 'pos': (0, 0), 'width': 1},
            'rect': (0, -0.0001, 1, 0.0001),
        }
        
        for i in range(10):
            walls[f'{10 + i};6'] = {
                'elevation': 0,
                'height': 0.19 + 0.19 * i,
                'texture': 0,
                'top': (64, 64, 64),
                'bottom': (64, 64, 64),
            }

        self._wall_textures = (
            ColumnTexture(pg.image.load('data/images/redbrick.png').convert()),
        )

        #temp
        self._player = Player()
        self._player.pos = (6.5, 7)
        self._player.yaw = 180
        self._player.elevation = 1
        self._player.height = 0.6

        entities = {
            0: Entity(
                height=0.6,
                textures=[
                    pg.image.load('data/images/vassago/1.png'),
                    pg.image.load('data/images/vassago/2.png'),
                    pg.image.load('data/images/vassago/3.png'),
                    pg.image.load('data/images/vassago/4.png'),
                    pg.image.load('data/images/vassago/5.png'),
                    pg.image.load('data/images/vassago/6.png'),
                    pg.image.load('data/images/vassago/7.png'),
                    pg.image.load('data/images/vassago/8.png'),
                ]
            ),
            1: Entity(
                height=0.6,
                textures=[pg.image.load('data/images/GrenadeZombie.png')],
            ),
            2: Entity(
                height=0.6,
                textures=[pg.image.load('data/images/GrenadeZombie.png')],
            ),
            3: Entity(
                height=0.6,
                textures=[pg.image.load('data/images/GrenadeZombie.png')],
            ),
            4: Entity(
                height=0.6,
                textures=[pg.image.load('data/images/GrenadeZombie.png')],
            ),
        }
        entities[0].pos = (6.5, 6)
        entities[1].pos = (6.5, 5)
        entities[2].pos = (6.5, 4)
        entities[3].pos = (6.5, 3)
        entities[4].pos = (6.5, 2)
        
        """
        entities[0].glowing = 1
        entities[1].glowing = 1
        entities[2].glowing = 1
        entities[3].glowing = 1
        entities[4].glowing = 1"""

        self._entities = EntityManager(self._player, entities)

        self._level = Level(
            floor=Floor(pg.image.load('data/images/wood.png').convert()),
            ceiling=Sky(pg.image.load('data/images/nightsky.png').convert()),
            walls=Walls(walls, self._wall_textures),
            entities=self._entities,
        )
        
        #temp
        pg.mouse.set_relative_mode(1)

        self._camera = Camera(
            fov=90,
            tile_size=self._SURF_SIZE[0] / 2,
            wall_render_distance=8,
            player=self._player,
        )
        self._camera.horizon = 0.5
        self._level_timer = 0

        self._level.walls.set_tile(
            pos=(6, 5),
            elevation=1,
            height=2,
            top=(64, 64, 64),
            bottom=(64, 64, 64),
        )

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        
        gun = pg.image.load('data/images/gun.png')

        from statistics import mean
        frames = []
        fps = 0
        second = pg.event.custom_type()
        pg.time.set_timer(second, 1000)
        
        shotgun = mx.Sound('data/sounds/shotgun.mp3')

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            self._level_timer += rel_game_speed

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                # temp
                elif event.type == pg.MOUSEMOTION:
                    rel = pg.mouse.get_rel()
                    self._player.yaw += rel[0] * 0.2
                    #self._camera.horizon -= rel[1] * 0.0025

                elif event.type == pg.MOUSEBUTTONDOWN:
                    self._player.hitscan_shoot(100)
                    shotgun.play()

                elif event.type == second:
                    fps = mean(frames)
                    frames = []

            keys = pg.key.get_pressed()
            movement = (
                (keys[pg.K_w] - keys[pg.K_s]) * 0.05,
                (keys[pg.K_d] - keys[pg.K_a]) * 0.05,
                (keys[pg.K_RIGHT] - keys[pg.K_LEFT]) * 2.5,
                (keys[pg.K_DOWN] - keys[pg.K_UP]),
                (keys[pg.K_SPACE] - keys[pg.K_LSHIFT]) * 0.05,
            )

            self._player.update(
                rel_game_speed,
                self._level_timer,
                movement[0],
                movement[1],
                movement[2],
                movement[4] if movement[4] else None,
            )
            self._camera.horizon -= movement[3] * 0.025 * rel_game_speed
            
            self._entities.update(rel_game_speed, self._level_timer)

            # moving walls
            self._level.walls.set_tile(
                pos=(8, 11),
                elevation=math.sin(self._level_timer / 60 + math.pi) + 1,
            )
            self._level.walls.set_tile(
                pos=(9, 11),
                height=math.sin(self._level_timer / 60) + 1,
            )
            self._level.walls.set_tile(
                pos=(10, 8),
                elevation=0,
                height=2,
                texture=0,
                semitile={
                    'axis': 1,
                    'pos': (0.2, self._level_timer / 60 % 2 - 1),
                    'width': 1,
                },
                rect=(0.2, 0, 0.0001, 1),
            )

            self._camera.render(self._surface)
            crosshair = (
                self._surface.width / 2 - 1,
                self._surface.height / 2 - 1,
                2,
                2,
            )
            pg.draw.rect(self._surface, (255, 255, 255), crosshair)


            frames.append(1 / delta_time if delta_time else math.inf)
            pg.display.set_caption(str(int(fps)))

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.flip()

        pg.quit()

if __name__ == '__main__':
    Game().run()

