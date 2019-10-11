from enum import Enum
from dataclasses import dataclass
from planar import Point
from pygame import Rect


class Facing(Enum):
    LEFT = 180
    RIGHT = 0


class GameObject:
    _pos: Point
    _w: float
    _h: float
    facing: Facing = Facing.RIGHT
    _rect: Rect

    def __init__(self, pos: Point, w: float, h: float, facing: Facing = Facing.RIGHT):
        self._pos = pos
        self._w = w
        self._h = h
        self.facing = facing
        self._rect = Rect(pos.x, pos.y, w, h)

    @property
    def rect(self):
        return self._rect

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self._rect.topleft = self._pos

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, value):
        self._w = float(value)
        self._rect.width = int(self._w)

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, value):
        self._h = float(value)
        self._rect.hidth = int(self._h)

    @property
    def size(self):
        return (self._rect.width, self._rect.height)


@dataclass
class PlatformComponent:
    pass

class WeakPlatformMarker:
    pass

@dataclass
class WallComponent:
    is_destructible: bool = False
