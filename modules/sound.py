from typing import Self

import openal as oal
from openal import AL_PLAYING
from openal import oalInit
from openal import oalGetInit
from openal import oalQuit
from openal import oalGetListener
from openal import oalOpen
from openal import oalOpen
from pygame import mixer as mx


# Interface for sounds
class _Sound(object):
    def __init__(self: Self, path: str, volume: Real=1) -> None:
        pass

    @property
    def volume(self: Self) -> Real:
        pass

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        pass

    def play(self: Self) -> None:
        pass

    def stop(self: Self) -> None:
        pass


class Sound2D(_Sound):
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
        self._update()

    def _update(self: Self) -> None:
        self._sound.set_volume(self._manager._volume * self._volume)

    def play(self: Self) -> None:
        self._sound.play()

    def stop(self: Self) -> None:
        self._sound.stop()


class Sound3D(_Sound):
    def __init__(self: Self, path: str) -> None:
        self._sources = [oalOpen(path)]
        self._manager = None

    def play(self: Self, vector: pg.Vector3, direction: pg.Vector3) -> None:
        for source in self._sources:
            if source.get_state() == AL_PLAYING:
                pass

    def stop(self: Self) -> None:
        pass


class SoundManager(object):
    def __init__(self: Self,
                 sounds2d: list[Sound2D]=[],
                 sounds3d: list[Sound3D]=[],
                 volume: Real=1) -> None:

        if not oalGetInit():
            oalInit()
        self._listener = oalGetListener()
        self._listener.set_gain(volume)
        self._volume = volume
        self._level = None

    @property
    def volume(self: Self) -> Real:
        return self._volume

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        self._volume = value
        self._listener.set_gain(value)

    def update(self: Self) -> None:
        player = self._level._entities._player
        self._listener.set_position(player.vector3)
        # might need to normalize player yaw
        self._listener.set_orientation((
            player._yaw[0], 0, player._yaw[1], 0, 1, 0,
        ))

    def quit(self: Self) -> None:
        oalQuit()

