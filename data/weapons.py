import math

import pygame as pg

from data.sounds import SOUNDS
from modules.utils import gen_img_path
from modules.entities import Missile
from modules.weapons import MeleeWeapon
from modules.weapons import HitscanWeapon
from modules.weapons import MissileWeapon

textures = {
    'fist': [
        pg.image.load(gen_img_path('fist/1.png')),
        pg.image.load(gen_img_path('fist/2.png')),
        pg.image.load(gen_img_path('fist/3.png')),
        pg.image.load(gen_img_path('fist/4.png')),
    ],
    'shotgun': [
        pg.image.load(gen_img_path('shotgun/1.png')),
        pg.image.load(gen_img_path('shotgun/2.png')),
        pg.image.load(gen_img_path('shotgun/3.png')),
        pg.image.load(gen_img_path('shotgun/4.png')),
    ],
    'launcher': [
        pg.image.load(gen_img_path('missile_launcher/1.png')),
        pg.image.load(gen_img_path('missile_launcher/2.png')),
    ],
}

for surfs in textures.values():
    for surf in surfs:
        surf.set_colorkey((255, 0, 255))


WEAPONS = {
    'fist': MeleeWeapon(
        damage=100,
        attack_range=0.25,
        cooldown=35,
        durability=math.inf,
        ground_textures=None,
        hold_textures=[textures['fist'][0]],
        attack_textures=[
            textures['fist'][1],
            textures['fist'][2],
            textures['fist'][3],
            textures['fist'][2],
            textures['fist'][1],
        ],
        ground_animation_time=1,
        hold_animation_time=30,
        attack_animation_time=30,
    ),
    'shotgun': HitscanWeapon(
        damage=100,
        attack_range=20,
        cooldown=60,
        capacity=25,
        ground_textures=None,
        hold_textures=[textures['shotgun'][0]],
        attack_textures=[
            textures['shotgun'][1],
            textures['shotgun'][2],
            textures['shotgun'][3],
            textures['shotgun'][2],
            textures['shotgun'][1],
        ],
        ground_animation_time=1,
        hold_animation_time=30,
        attack_animation_time=50,
        attack_sound=SOUNDS['shotgun'],
    ),
    'launcher': MissileWeapon(
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
        hold_textures=[textures['launcher'][0]],
        attack_textures=[
            textures['launcher'][1],
        ],
        ground_animation_time=1,
        hold_animation_time=30,
        attack_animation_time=10,
    ),
}

