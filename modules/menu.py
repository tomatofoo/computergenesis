from typing import Self
from typing import Optional

import pygame as pg
from pygame.typing import ColorLike


class Menu(object): # centered on x
    class Widget(object):
        def __init__(self: Self, surf: pg.Surface) -> None:
            self._surf = surf

        @property
        def surf(self: Self) -> pg.Surface:
            return self._surf

    class Button(Widget):
        def __init__(self: Self,
                     text: str,
                     font: pg.Font,
                     unselected: ColorLike,
                     selected: ColorLike,
                     antialiasing: bool=False) -> None:

            self._text = text
            self._surfs = {
                'unselected': font.render(text, antialiasing, unselected),
                'selected': font.render(text, antialiasing, selected),
            }
            self._selected = 0

        @property
        def surf(self: Self) -> pg.Surface:
            return self._selected

    def __init__(self: Self,
                 font: pg.Font,
                 y: int=0,
                 unselected_color: ColorLike=(255, 255, 255),
                 selected_color: ColorLike=(255, 0, 0),
                 background: Optional[pg.Surface]=None) -> None:
        self._widgets = []
        self._y = y
        self._gap = 0
        self._colors = {
            'unselected': unselected_color,
            'selected': selected_color,
        }

    @property
    def gap(self: Self) -> int:
        return self._gap

    @gap.setter
    def gap(self: Self, value: int) -> None:
        self._gap = value

    def surf(self: Self, surf: pg.Surface) -> None:
        self._widgets.append(self.Widget(surf))

    def button(self: Self, text: str) -> None:
        self._widgets.append(
            self.Button(
                text,
                self._font,
                self._colors['unselected'],
                self._colors['selected'],
            ),
        )

    def render(self: Self, surf: pg.Surface) -> None:
        y = self._y
        for widget in self._widgets:
            surface = widget.surf
            surf.blit(surface, ((surf.width - surface.width) / 2, y))
            y += surface.height + self._gap

