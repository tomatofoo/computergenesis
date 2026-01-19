from pygame import mixer as mx

from modules.sound import patch_surround
from modules.sound import Sound
from modules.sound import SoundManager
from modules.utils import gen_sfx_path
from modules.utils import gen_mus_path


mx.init()
patch_surround()
SOUNDS = SoundManager(
    sounds={
        'shotgun': Sound(gen_sfx_path('shotgun.mp3')),
        'water': Sound(gen_sfx_path('water.wav')),
    },
)

