#!/usr/bin/env python3

import time
import math
import json
import random
from numbers import Real
from typing import Self

import pygame as pg

from modules.level import ColumnTexture
from modules.level import Walls
from modules.level import Floor
from modules.level import Sky 
from modules.level import Special
from modules.level import SpecialManager
from modules.level import Level
from modules.camera import Camera
from modules.hud import HUDElement
from modules.hud import HUD
from modules.sound import patch_surround
from modules.sound import Sound
from modules.sound import SoundManager
from modules.entities import Entity
from modules.entities import EntityExState
from modules.entities import EntityEx
from modules.entities import Missile
from modules.entities import Player
from modules.entities import EntityManager 
from modules.inventory import Collectible
from modules.inventory import Inventory
from modules.weapons import MeleeWeapon
from modules.weapons import HitscanWeapon
from modules.weapons import MissileWeapon
from modules.utils import gen_img_path
from modules.utils import gen_sfx_path
from modules.utils import gen_mus_path


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
        
        textures = (
            (pg.image.load(gen_img_path('cacodemon/1/1.png')),
             pg.image.load(gen_img_path('cacodemon/1/2.png')),
             pg.image.load(gen_img_path('cacodemon/1/3.png')),
             pg.image.load(gen_img_path('cacodemon/1/4.png')),
             pg.image.load(gen_img_path('cacodemon/1/5.png')),
             pg.image.load(gen_img_path('cacodemon/1/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/2/1.png')),
             pg.image.load(gen_img_path('cacodemon/2/2.png')),
             pg.image.load(gen_img_path('cacodemon/2/3.png')),
             pg.image.load(gen_img_path('cacodemon/2/4.png')),
             pg.image.load(gen_img_path('cacodemon/2/5.png')),
             pg.image.load(gen_img_path('cacodemon/2/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/3/1.png')),
             pg.image.load(gen_img_path('cacodemon/3/2.png')),
             pg.image.load(gen_img_path('cacodemon/3/3.png')),
             pg.image.load(gen_img_path('cacodemon/3/4.png')),
             pg.image.load(gen_img_path('cacodemon/3/5.png')),
             pg.image.load(gen_img_path('cacodemon/3/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/4/1.png')),
             pg.image.load(gen_img_path('cacodemon/4/2.png')),
             pg.image.load(gen_img_path('cacodemon/4/3.png')),
             pg.image.load(gen_img_path('cacodemon/4/4.png')),
             pg.image.load(gen_img_path('cacodemon/4/5.png')),
             pg.image.load(gen_img_path('cacodemon/4/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/5/1.png')),
             pg.image.load(gen_img_path('cacodemon/5/2.png')),
             pg.image.load(gen_img_path('cacodemon/5/3.png')),
             pg.image.load(gen_img_path('cacodemon/5/4.png')),
             pg.image.load(gen_img_path('cacodemon/5/5.png')),
             pg.image.load(gen_img_path('cacodemon/5/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/6/1.png')),
             pg.image.load(gen_img_path('cacodemon/6/2.png')),
             pg.image.load(gen_img_path('cacodemon/6/3.png')),
             pg.image.load(gen_img_path('cacodemon/6/4.png')),
             pg.image.load(gen_img_path('cacodemon/6/5.png')),
             pg.image.load(gen_img_path('cacodemon/6/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/7/1.png')),
             pg.image.load(gen_img_path('cacodemon/7/2.png')),
             pg.image.load(gen_img_path('cacodemon/7/3.png')),
             pg.image.load(gen_img_path('cacodemon/7/4.png')),
             pg.image.load(gen_img_path('cacodemon/7/5.png')),
             pg.image.load(gen_img_path('cacodemon/7/6.png'))),
            (pg.image.load(gen_img_path('cacodemon/8/1.png')),
             pg.image.load(gen_img_path('cacodemon/8/2.png')),
             pg.image.load(gen_img_path('cacodemon/8/3.png')),
             pg.image.load(gen_img_path('cacodemon/8/4.png')),
             pg.image.load(gen_img_path('cacodemon/8/5.png')),
             pg.image.load(gen_img_path('cacodemon/8/6.png'))),
        )
        for animation in textures:
            for surf in animation:
                surf.set_colorkey((255, 0, 255))
        
        d = [[
            pg.image.load(gen_img_path('cacodemon/d/1.png')),
            pg.image.load(gen_img_path('cacodemon/d/2.png')),
            pg.image.load(gen_img_path('cacodemon/d/3.png')),
            pg.image.load(gen_img_path('cacodemon/d/4.png')),
            pg.image.load(gen_img_path('cacodemon/d/5.png')),
            pg.image.load(gen_img_path('cacodemon/d/6.png'))
        ]]
        for animation in d:
            for surf in animation:
                surf.set_colorkey((255, 0, 255))
        missile = Missile(
            damage=100,
            width=0.25,
            height=0.25,
            states={
                'default': EntityExState(textures, 30),
                'attack': EntityExState(d, 30, loop=0, trigger=1),
            }
        )

        entities = {
            EntityEx(
                pos=(9, 9),
                elevation=3,
                width=0.5,
                height=0.75,
                attack_width=0.8,
                attack_height=0.8,
                render_width=1,
                render_height=1,
                states={'default': EntityExState(textures, 60)},
            ),
            Entity(
                pos=(6.5, 6),
                width=0.25,
                height=0.6,
                attack_width=0.4,
                render_width=0.5,
                textures=[
                    pg.image.load(gen_img_path('vassago/1.png')),
                    pg.image.load(gen_img_path('vassago/2.png')),
                    pg.image.load(gen_img_path('vassago/3.png')),
                    pg.image.load(gen_img_path('vassago/4.png')),
                    pg.image.load(gen_img_path('vassago/5.png')),
                    pg.image.load(gen_img_path('vassago/6.png')),
                    pg.image.load(gen_img_path('vassago/7.png')),
                    pg.image.load(gen_img_path('vassago/8.png')),
                ]
            ),
            Entity(
                pos=(6.5, 5),
                width=0.25,
                height=0.6,
                attack_width=0.4,
                render_width=0.5,
                textures=[pg.image.load(gen_img_path('GrenadeZombie.png'))],
            ),
            Entity(
                pos=(6.5, 4),
                width=0.25,
                height=0.6,
                attack_width=0.4,
                render_width=0.5,
                textures=[pg.image.load(gen_img_path('GrenadeZombie.png'))],
            ),
            Entity(
                pos=(6.5, 3),
                width=0.25,
                height=0.6,
                attack_width=0.4,
                render_width=0.5,
                textures=[pg.image.load(gen_img_path('GrenadeZombie.png'))],
            ),
            Entity(
                pos=(6.5, 2),
                width=0.25,
                height=0.6,
                attack_width=0.4,
                render_width=0.5,
                textures=[pg.image.load(gen_img_path('GrenadeZombie.png'))],
            ),
        }
        for dex, entity in enumerate(entities):
            entity.glowing = 1

        self._player = Player((6.5, 7))
        self._player.yaw = 180
        self._player.elevation = 1
        self._camera = Camera(
            fov=90,
            tile_size=self._SURF_SIZE[0] / 2,
            wall_render_distance=8,
            player=self._player,
            multithreaded=True,
        )
        self._camera.horizon = 0.5
        self._camera.weapon_scale = 1
        self._entities = EntityManager(self._player, entities)

        # Sound
        patch_surround()
        self._sounds = SoundManager(
            sounds={
                'shotgun': Sound(gen_sfx_path('shotgun.mp3')),
                'water': Sound(gen_sfx_path('water.wav')),
            },
        )

        with open('data/map.json', 'r') as file:
            walls = json.loads(file.read())
        wall_textures = (
            ColumnTexture(
                pg.image.load(
                    gen_img_path('tilesets/all/redbrick.png'),
                ).convert(),
            ),
        )
        self._specials = SpecialManager()
        self._level = Level(
            floor=Floor(
                pg.image.load(gen_img_path('tilesets/all/wood.png')).convert(),
            ),
            ceiling=Sky(pg.image.load(gen_img_path('nightsky.png')).convert()),
            walls=Walls(walls, wall_textures),
            specials=self._specials,
            entities=self._entities,
            sounds=self._sounds,
        )
        pg.mouse.set_relative_mode(1)

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
            missile=missile,
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

