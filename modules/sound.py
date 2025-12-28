from typing import Self
from typing import Optional

import openal as oal
from openal import AL_PLAYING
from openal import oalInit
from openal import oalGetInit
from openal import oalQuit
from openal import oalGetListener
from openal import oalOpen
from openal import oalOpen
from pygame import mixer as mx


class Sound2D(object):
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


class Sound3D(object):
    def __init__(self: Self, path: str, volume: Real=1) -> None:
        self._path = path
        self._volume = volume
        self._looping = False
        self._sources = []
        self._manager = None

    @property
    def volume(self: Self) -> Real:
        return self._volume

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        self._volume = value

    @property
    def looping(self: Self) -> bool:
        return self._looping

    @looping.setter
    def looping(self: Self, value: bool) -> None:
        self._looping = value

    def _play(self: Self,
              source: oal.Source,
              pos: pg.Vector3,
              direction: pg.Vector3) -> None:
        source.set_position(pos)
        source.set_direction(direction)
        source.set_gain(self._volume)
        source.set_looping(self._looping)
        source.play()

    def play(self: Self, pos: pg.Vector3, direction: pg.Vector3) -> None:
        for source in self._sources:
            if source.get_state() != AL_PLAYING:
                self._play(source, pos, direction)
                break
        else:
            source = oalOpen(self._path)
            self._sources._append(source)
            self._play(source, pos, direction)

    def stop(self: Self) -> None:
        for source in self._sources:
            source.stop()

    def reset(self: Self) -> None:
        for source in self._sources:
            source.destroy()
        self._sources = []


class SoundManager(object):
    def __init__(self: Self,
                 sounds2d: dict[object, Sound2D]={},
                 sounds3d: dict[object, Sound3D]={},
                 volume: Real=1) -> None:

        if not oalGetInit():
            oalInit()
        self._listener = oalGetListener()
        self._listener.set_gain(volume)
        self._volume = volume
        self._sounds2d = {}
        self._sounds3d = {}
        self.sounds2d = sounds2d
        self.sounds3d = sounds3d
        self._level = None

    @property
    def sounds2d(self: Self) -> list[Sound2D]:
        return self._sounds2d

    @sounds2d.setter
    def sounds2d(self: Self, value: Sound2D) -> None:
        for sound in self._sounds2d.values():
            sound._manager = None
        self._sounds2d = value
        for sound in value.values():
            sound._manager = self
            sound._update()

    @property
    def sounds3d(self: Self) -> list[Sound3D]:
        return self._sounds3d

    @sounds3d.setter
    def sounds3d(self: Self, value: Sound3D) -> None:
        for sound in self._sounds3d.values():
            sound._manager = None
        self._sounds3d = value
        for sound in value.values():
            sound._manager = self

    @property
    def volume(self: Self) -> Real:
        return self._volume

    @volume.setter
    def volume(self: Self, value: Real) -> None:
        self._volume = value
        self._listener.set_gain(value)
        for sound in self._sounds2d.values():
            sound._update()

    def sound2d(self: Self, id: object) -> Optional[Sound2D]:
        return self._sounds2d.get(id)

    def sound3d(self: Self, id: object) -> Optional[Sound3D]:
        return self._sounds3d.get(id)

    def set_sound2d(self: Self, id: object, sound: Sound2D) -> None:
        old = self._sounds2d.get(id)
        if old is not None:
            old._manager = None
        self._sounds2d[id] = sound
        sound._manaager = self

    def pop_sound2d(self: Self, id: object) -> Sound2D:
        self._sounds2d[id]._manager = None
        return self._sounds2d.pop(id)

    def set_sound3d(self: Self, id: object, sound: Sound3D) -> None:
        old = self._sounds3d.get(id)
        if old is not None:
            old._manager = None
        self._sounds3d[id] = sound
        sound._manager = self

    def pop_sound3d(self: Self, id: object) -> Sound3D:
        self._sounds3d[id]._manager = None
        return self._sounds3d.pop(id)

    def update(self: Self) -> None:
        player = self._level._entities._player
        self._listener.set_position(player.vector3)
        # might need to normalize player yaw
        self._listener.set_orientation((
            player._yaw[0], 0, player._yaw[1], 0, 1, 0,
        ))

    def quit(self: Self) -> None:
        oalQuit()

    def reset(self: Self) -> None:
        for sound in self._sounds3d:
            sound.reset()
        self.quit()
        if not oalGetInit():
            oalInit()

