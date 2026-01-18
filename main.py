#!/usr/bin/env python3

import time
import math
import json
import random
from numbers import Real
from typing import Self

import pygame as pg

from data.weapons import WEAPONS
from data.levels import LEVELS
from modules.camera import Camera
from modules.hud import HUDElement
from modules.hud import HUD
from modules.entities import Missile
from modules.entities import Player
from modules.inventory import Collectible
from modules.inventory import Inventory
from modules.weapons import MeleeWeapon
from modules.weapons import HitscanWeapon
from modules.weapons import MissileWeapon
from modules.utils import gen_img_path


# TODO: INVENTORY, *SPECIAL TILES, HUD, MENUS, LEVEL EDITOR, data/level.py, GAMEPLAY / LEVELS
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
        self._player = self._level.entities.player
        self._sounds = self._level.sounds

        self._camera = Camera(
            fov=90,
            tile_size=self._SURF_SIZE[0] / 2,
            wall_render_distance=24,
            player=self._player,
            darkness=1,
            multithreaded=True,
        )
        self._camera.horizon = 0.5
        self._camera.weapon_scale = 3 / self._SURF_RATIO[0]

        textures = [
            pg.image.load(gen_img_path('shotgun/1.png')),
            pg.image.load(gen_img_path('shotgun/2.png')),
            pg.image.load(gen_img_path('shotgun/3.png')),
            pg.image.load(gen_img_path('shotgun/4.png')),
        ]
        for surf in textures:
            surf.set_colorkey((255, 0, 255))
        self._shotgun = HitscanWeapon(
            damage=100,
            attack_range=20,
            cooldown=60,
            capacity=25,
            ground_textures=None,
            hold_textures=[textures[0]],
            attack_textures=[
                textures[1],
                textures[2],
                textures[3],
                textures[2],
                textures[1],
            ],
            ground_animation_time=1,
            hold_animation_time=30,
            attack_animation_time=50,
            attack_sound=self._sounds['shotgun'],
        )
        self._shotgun.ammo = math.inf
        textures = [
            pg.image.load(gen_img_path('fist/1.png')),
            pg.image.load(gen_img_path('fist/2.png')),
            pg.image.load(gen_img_path('fist/3.png')),
            pg.image.load(gen_img_path('fist/4.png')),
        ]
        for surf in textures:
            surf.set_colorkey((255, 0, 255))
        self._fist = MeleeWeapon(
            damage=100,
            attack_range=0.25,
            cooldown=35,
            durability=math.inf,
            ground_textures=None,
            hold_textures=[textures[0]],
            attack_textures=[
                textures[1],
                textures[2],
                textures[3],
                textures[2],
                textures[1],
            ],
            ground_animation_time=1,
            hold_animation_time=30,
            attack_animation_time=30,
        )
        textures = [
            pg.image.load(gen_img_path('missile_launcher/1.png')),
            pg.image.load(gen_img_path('missile_launcher/2.png')),
        ]
        for surf in textures:
            surf.set_colorkey((255, 0, 255))
        self._missile_launcher = MissileWeapon(
            attack_range=10,
            cooldown=25,
            capacity=25,
            speed=0.075,
            missile=Missile(
                damage=100,
                width=0.25,
                height=0.25,
            ),
            ground_textures=None,
            hold_textures=[textures[0]],
            attack_textures=[
                textures[1],
            ],
            ground_animation_time=1,
            hold_animation_time=30,
            attack_animation_time=10,
        )
        self._missile_launcher.ammo = math.inf
        self._player.weapon = self._missile_launcher

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
                        self._player.weapon = self._fist
                    elif event.key == pg.K_2:
                        self._player.weapon = self._shotgun
                    elif event.key == pg.K_3:
                        self._player.weapon = self._missile_launcher
                    elif event.key == pg.K_0:
                        self._sounds['water'].play(pos=(9, 0.25, 9)) 
                    elif event.key == pg.K_e:
                        self._player.interact()

            # Update
            self.move_tiles(level_timer)
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
                level_timer,
                movement[0],
                movement[1],
                movement[2],
                movement[4] if movement[4] else None,
            )
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

