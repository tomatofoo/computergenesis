#!/usr/bin/env python3

import time
import math
import json
import random
from numbers import Real
from typing import Self

import pygame as pg

from data.weapons import SOUNDS
from data.weapons import WEAPONS
from data.levels import LEVELS
from modules.camera import Camera
from modules.hud import HUDElement
from modules.hud import HUD
from modules.entities import Player
from modules.utils import gen_img_path


# TODO: *INVENTORY, *SPECIAL TILES, HUD, MENUS, *LEVEL EDITOR, *data/level.py, GAMEPLAY / LEVELS
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
        pg.display.set_caption('Computergenesis')
        self._surface = pg.Surface(self._SURF_SIZE)
        self._running = 0
        
        pg.mouse.set_relative_mode(1)

        self._level = LEVELS[0]
        self._level.sounds = SOUNDS
        self._player = self._level.entities.player

        self._camera = Camera(
            fov=90,
            tile_size=self._SURF_SIZE[0] / 2,
            wall_render_distance=8,
            player=self._player,
            darkness=1,
            multithreaded=True,
        )
        self._camera.horizon = 0.5
        self._camera.weapon_scale = 3 / self._SURF_RATIO[0]

        self._player.weapon = WEAPONS['launcher']

    def move_tiles(self: Self, level_timer: Real) -> None:
        self._level.walls.set_tile(
            pos=(8, 11),
            elevation=math.sin(level_timer / 60 + math.pi) + 1,
        )
        self._level.walls.set_tile(
            pos=(9, 11),
            height=math.sin(level_timer / 60) + 1,
        )
        self._level.walls.set_tile(
            pos=(10, 8),
            elevation=0,
            height=2,
            texture=0,
            semitile={
                'axis': 1,
                'pos': (0.2, level_timer / 60 % 2 - 1),
                'width': 1,
            },
            rect=(0.2, 0, 0.0001, 1),
        )

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()
        level_timer = 0
        
        from statistics import mean
        frames = []
        fps = 0
        second = pg.event.custom_type()
        pg.time.set_timer(second, 1000)

        jumping = 0
        dashing = 0
        crouching = 0

        while self._running:
            # Time
            delta_time = time.time() - start_time
            start_time = time.time()
            rel_game_speed = delta_time * self._GAME_SPEED
            level_timer += rel_game_speed
            
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self._running = 0
                elif event.type == pg.MOUSEMOTION:
                    rel = pg.mouse.get_rel()
                    self._player.yaw += rel[0] * 0.2
                    #self._camera.horizon -= rel[1] * 0.0025
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self._player.attack()
                elif event.type == second:
                    fps = mean(frames)
                    pg.display.set_caption(str(int(fps)))
                    frames = []
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_1:
                        self._player.weapon = WEAPONS['fist']
                    elif event.key == pg.K_2:
                        self._player.weapon = WEAPONS['shotgun']
                    elif event.key == pg.K_3:
                        self._player.weapon = WEAPONS['launcher']
                    elif event.key == pg.K_0:
                        SOUNDS['water'].play(pos=(9, 0.25, 9)) 
                    elif event.key == pg.K_e:
                        self._player.interact()
                    elif event.key == pg.K_LSHIFT:
                        if not dashing:
                            if jumping:
                                dashing = 1
                                mult = 1
                                if keys[pg.K_s] and not keys[pg.K_w]:
                                    mult = -1
                                self._player.boost = (
                                    self._player.forward * 0.15 * mult
                                )
                                self._player.height = 0.35
                                self._camera.camera_offset = 0.3
                                self._player.elevation_velocity = -0.075
                            else:
                                crouching = 1
            # Update
            if self._level is LEVELS[0]:
                self.move_tiles(level_timer)
            keys = pg.key.get_pressed()

            speed = 1.5
            if dashing:
                dashing += rel_game_speed
                self._camera.camera_offset = dashing / 30 * 0.3 + 0.2
                if dashing > 30:
                    dashing = 0
                    crouching = 1
                    # self._player.height = 0.6
                    # self._camera.camera_offset = 0.5
            if crouching: 
                if keys[pg.K_LSHIFT]:
                    self._player.height = 0.35
                    crouching = min(crouching + rel_game_speed, 10)
                    speed = 0.65
                else:
                    crouching = max(crouching - rel_game_speed, 0)
                    if not crouching:
                        self._player.height = 0.6
                self._camera.camera_offset = 0.5 - crouching / 10 * 0.2

            movement = (
                (keys[pg.K_w] - keys[pg.K_s]) * 0.05 * speed,
                (keys[pg.K_d] - keys[pg.K_a]) * 0.05 * speed,
                (keys[pg.K_RIGHT] - keys[pg.K_LEFT]) * 2.5,
                (keys[pg.K_DOWN] - keys[pg.K_UP]),
                (keys[pg.K_SPACE] and not jumping) * 0.05 * 1.5,
            )
            self._player.update(
                rel_game_speed,
                level_timer,
                movement[0],
                movement[1],
                movement[2],
                movement[4] if movement[4] else None,
            )

            if keys[pg.K_SPACE]:
                jumping = 1
            if self._player.collisions['e'][0]:
                jumping = 0

            self._camera.horizon -= movement[3] * 0.025 * rel_game_speed
            self._level.update(rel_game_speed, level_timer)
            frames.append(1 / delta_time if delta_time else math.inf)

            # Render
            self._camera.render(self._surface)
            # self._hud.render(self._surface)
            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))
            pg.display.flip()
        
        pg.quit()

if __name__ == '__main__':
    Game().run()

