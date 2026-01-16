import pygame as pg
from pygame import mixer as mx

from modules.level import ColumnTexture
from modules.level import Walls
from modules.level import Floor
from modules.level import Sky 
from modules.level import Special
from modules.level import SpecialManager
from modules.level import Level
from modules.sound import patch_surround
from modules.sound import Sound
from modules.sound import SoundManager
from modules.entities import Entity
from modules.entities import EntityExState
from modules.entities import EntityEx
from modules.entities import Missile
from modules.entities import Player
from modules.entities import EntityManager
from modules.utils import gen_img_path
from modules.utils import gen_sfx_path
from modules.utils import gen_mus_path


# Sound
# All levels share the same sounds
mx.init()
patch_surround()
SOUNDS = SoundManager(
    sounds={
        'shotgun': Sound(gen_sfx_path('shotgun.mp3')),
        'water': Sound(gen_sfx_path('water.wav')),
    },
)

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

player = Player((6.5, 7))
player.yaw = 180
player.elevation = 1
entities = EntityManager(player, entities)

wall_textures = (
    ColumnTexture(pg.image.load(gen_img_path('tilesets/all/redbrick.png'))),
)
specials = SpecialManager()
level0 = Level(
    floor=Floor(pg.image.load(gen_img_path('tilesets/all/wood.png'))),
    ceiling=Sky(pg.image.load(gen_img_path('nightsky.png'))),
    walls=Walls.load('data/maps/1.json', wall_textures),
    specials=specials,
    entities=entities,
    sounds=SOUNDS,
)

LEVELS = (
    level0,
)

