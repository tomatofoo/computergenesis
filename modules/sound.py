from typing import Self
from typing import Optional

import pygame as pg
from pygame import mixer as mx


# Switch to forced stereo if using 7.1 surround
# Should be called before initializing Sound objects
def patch_surround():
    assert mx.get_init() is not None, 'init mixer before calling'
    try: # Test to make sure that setting location works
        mx.Channel(0).set_source_location(0, 0)
    except pg.error: # Re-init with forced stereo
        mx.quit()
        mx.init(channels=2)


class Sound(object):
    def __init__(self: Self, path: str, volume: Real=1) -> None:
        self._sound = mx.Sound(path)
        self._sound.set_volume(volume)
        self._volume = volume
        self._manager = None

    @property
    def volume(self: Self) -> Real:
        return self._volume

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        self._volume = value

    def play(self: Self,
             loops=0,
             maxtime=0,
             fade_ms=0,
             pos: Optional[pg.Vector3]=None) -> None:

        channel = mx.find_channel(force=1)
        channel.set_volume(self._manager._volume)
        if pos is not None:
            player = self._manager._level._entities._player
            rel_vector = (pos[0], pos[2]) - player._pos
            if rel_vector:
                angle = player._yaw_value - rel_vector.angle - 90
            else:
                angle = 0
            dist = player.vector3.distance_to(pos) * self._manager._dist_factor
            channel.set_source_location(angle, min(dist, 255))
            self._manager._channels.append((pos, channel))
        channel.play(self._sound, loops, maxtime, fade_ms)

    def stop(self: Self) -> None:
        self._sound.stop()


class SoundManager(object):
    def __init__(self: Self,
                 sounds: dict[object, Sound3D]={},
                 volume: Real=1,
                 channels: int=64,
                 dist_factor: Real=15) -> None:
        
        # Attributes
        self._sounds = sounds
        for sound in sounds.values():
            sound._manager = self
        self._level = None
        self._channels = [] # (vec3, channel)
        self._dist_factor = dist_factor
        self.volume = volume
        mx.set_num_channels(channels)

    def __getitem__(self: Self, id: object) -> Sound:
        return self._sounds[id]

    @property
    def sounds(self: Self) -> dict[object, Sound]:
        return self._sounds

    @sounds.setter
    def sounds(self: Self, value: Sound) -> None:
        for sound in self._sounds.values():
            sound._manager = None
        self._sounds = value
        for sound in value.values():
            sound._manager = self

    @property
    def volume(self: Self) -> Real:
        return self._volume

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        self._volume = value
        for _, channel in self._channels:
            channel.set_volume(value)

    @property
    def dist_factor(self: Self) -> Real:
        return self._dist_factor

    @dist_factor.setter
    def dist_factor(self: Self, value: Real) -> None:
        self._dist_factor = value

    def set_sound(self: Self, id: object, sound: Sound) -> None:
        old = self._sounds.get(id)
        if old is not None:
            old._manager = None
        self._sounds[id] = sound
        sound._manaager = self

    def pop_sound(self: Self, id: object) -> Sound:
        self._sounds[id]._manager = None
        return self._sounds.pop(id)

    def update(self: Self) -> None: # Update directional sounds
        player = self._level._entities._player
        channels = []
        for pos, channel in self._channels:
            rel_vector = (pos[0], pos[2]) - player._pos
            if rel_vector:
                angle = player._yaw_value - rel_vector.angle - 90
            else:
                angle = 0
            dist = player.vector3.distance_to(pos) * self._dist_factor
            channel.set_source_location(angle, min(dist, 255))
            if channel.get_busy(): # filter inactive channels
                channels.append((pos, channel))
        self._channels = channels

