import time
import math
import json
import random
from typing import Self

import pygame as pg

from modules.utils import Pathfinder
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
        
        with open('data/map.json', 'r') as file:
            data = file.read()
            walls = json.loads(data)

        self._wall_textures = (
            ColumnTexture(pg.image.load('data/images/redbrick.png').convert()),
        )

        #temp
        self._player = Player()
        self._player.pos = (1.5, 1.5)
        self._player_tile = self._player.tile
        self._dead = 0
        self._minimap_size = 2
        self._minimap = 0
        self._tilemap_size = (41, 41)
        #n
        entities = {
            0: Entity(
                height=0.6,
                texture=pg.image.load('data/images/GrenadeZombie.png')
            ),
        }
        entities[0].pos = (33.5, 33.5)
        self._entities = EntityManager(self._player, entities)
        self._pathfinder = Pathfinder(entities[0].tile, self._player.tile, walls)
        self._pathfinder.pathfind()
        self._next_path_dex = 1

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

        self._font = pg.font.SysFont('Arial', 30)
        self._small_font = pg.font.SysFont('Arial', 12)

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

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_r and self._dead:
                        self._dead = 0
                        self._level_timer = 0
                        self._player.pos = (1.5, 1.5)
                        self._player.velocity2 = (0, 0)
                        self._player.yaw = 0
                        self._entities[0].pos = (33.5, 33.5)
                        self._entities[0].velocity2 = (0, 0)
                        
                        player_tile = self._player.tile
                        self._player_tile = player_tile
                        self._pathfinder.start = self._entities[0].tile
                        self._pathfinder.end = player_tile
                        self._pathfinder.pathfind()
                        self._next_path_dex = 1
                    elif event.key == pg.K_m:
                        self._minimap = not self._minimap

            if self._dead:
                text1 = self._font.render('YOU DIED!', 1, (255, 255, 255))
                text2 = self._small_font.render('PRESS R TO RESTART', 1, (255, 255, 255))
                text3 = self._small_font.render(f'score: {int(score * 100)}', 1, (255, 255, 255))
                self._surface.fill((0, 0, 0))
                self._surface.blit(text1, (10, 10))
                self._surface.blit(text2, (10, 60))
                self._surface.blit(text3, (10, 110))

            else:
                keys = pg.key.get_pressed()
                movement = (
                    (keys[pg.K_w] - keys[pg.K_s]) * 0.1,
                    (keys[pg.K_d] - keys[pg.K_a]) * 0.1,
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
                # A* pathfinding
                player_tile = self._player.tile
                player_vector = self._player.vector2
                entity_vector = self._entities[0].vector2
                if player_tile != self._player_tile:
                    self._player_tile = player_tile
                    self._pathfinder.start = self._entities[0].tile
                    self._pathfinder.end = player_tile
                    self._pathfinder.pathfind()
                    self._next_path_dex = 1
                path = self._pathfinder.path
                try:
                    wanted_tile = path[self._next_path_dex]
                    wanted_pos = pg.Vector2(wanted_tile) + (0.5, 0.5)
                    pos = self._entities[0].pos
                    if pos.distance_to(wanted_pos) < 0.4:
                        self._next_path_dex += 1
                except IndexError:
                    wanted_pos = player_vector

                pathfind_vector = wanted_pos - entity_vector               
                rel_vector = player_vector - entity_vector
                if pathfind_vector and rel_vector:
                    pathfind_vector = pathfind_vector.normalize()
                    rel_vector = rel_vector.normalize()
                
                    vector = pathfind_vector * 0.9 + rel_vector * 0.1
                
                    if self._level_timer > 5 and vector:
                        self._entities[0].velocity2 = (vector.normalize() * 0.09)

                self._entities.update(rel_game_speed, self._level_timer)

                if self._entities[0].vector2.distance_to(player_vector) < 0.25:
                    self._dead = 1
                    score = self._level_timer

                # moving wall

                # self._level.walls.set_tile(
                #     pos=(8, 11),
                #     elevation=math.sin(self._level_timer),
                #     height=1,
                #     texture=0,
                # )

                self._camera.render(self._surface)
                # self._surface.blit(
                #     gun,
                #     (self._SURF_SIZE[0] - gun.width,
                #      self._SURF_SIZE[1] - gun.height),
                # )
                if self._level_timer <= 5:
                    text = self._font.render(
                        str(int(math.ceil(5 - self._level_timer))),
                        1,
                        (255, 255, 255),
                    )
                    self._surface.blit(text, (280, 10))

                # draw minimap
                if self._minimap:
                    rect = pg.Rect(
                        0, 0,
                        self._minimap_size * self._tilemap_size[0],
                        self._minimap_size * self._tilemap_size[1],
                    )
                    pg.draw.rect(self._surface, (0, 0, 0), rect)
                    for tile in self._level.walls._tilemap:
                        split = tile.split(';')
                        rect = pg.Rect(
                            int(split[0]) * self._minimap_size,
                            int(split[1]) * self._minimap_size,
                            self._minimap_size,
                            self._minimap_size,
                        )
                        pg.draw.rect(self._surface, (255, 255, 255), rect)

                    player_rect = self._player.rect()
                    player_rect.update(
                        player_rect.left * self._minimap_size,
                        player_rect.top * self._minimap_size,
                        player_rect.width * self._minimap_size,
                        player_rect.height * self._minimap_size, 
                    )

                    entity_rect = self._entities[0].rect()
                    entity_rect.update(
                        entity_rect.x * self._minimap_size,
                        entity_rect.y * self._minimap_size,
                        entity_rect.width * self._minimap_size,
                        entity_rect.height * self._minimap_size,
                    )

                    pg.draw.rect(self._surface, (0, 255, 0), player_rect)
                    pg.draw.rect(self._surface, (255, 0, 0), entity_rect)

            pg.display.set_caption(str(1 / delta_time) if delta_time else 'inf')

            resized_surf = pg.transform.scale(self._surface, self._SCREEN_SIZE)
            self._screen.blit(resized_surf, (0, 0))

            pg.display.flip()

        pg.quit()

if __name__ == '__main__':
    Game().run()

