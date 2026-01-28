from typing import Self
from typing import Optional
from typing import Callable

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
                     func: Callable,
                     antialiasing: bool=False) -> None:

            self._text = text
            self._surfs = [
                font.render(text, antialiasing, unselected),
                font.render(text, antialiasing, selected),
            ]
            self._selected = 0
            self._func = func

        @property
        def surf(self: Self) -> pg.Surface:
            return self._surfs[self._selected]
    
    # Expects there to be at least one button
    def __init__(self: Self,
                 font: pg.Font,
                 y: int=0,
                 gap: int=0,
                 unselected_color: ColorLike=(255, 255, 255),
                 selected_color: ColorLike=(255, 0, 0),
                 background: Optional[pg.Surface]=None) -> None:
        self._widgets = []
        self._selected = 0
        self.selected = 0
        self._selected_dex = 0 # actual index in widgets list
        self._font = font
        self._y = y
        self._gap = gap
        self._colors = {
            'unselected': unselected_color,
            'selected': selected_color,
        }
        self._background = background

    @property
    def gap(self: Self) -> int:
        return self._gap

    @gap.setter
    def gap(self: Self, value: int) -> None:
        self._gap = value

    @property
    def background(self: Self) -> Optional[pg.Surface]:
        return self._background

    @background.setter
    def background(self: Self, value: Optional[pg.Surface]) -> None:
        self._background = value
    
    @property
    def selected(self: Self) -> int:
        return self._selected

    @selected.setter
    def selected(self: Self, value: int) -> None:
        if value < 0:
            return None
        # selects (n + 1)th added selectable
        i = 0
        for dex, widget in enumerate(self._widgets):
            if isinstance(widget, self.Button):
                if i == value:
                    widget._selected = 1
                    selected_dex = dex
                    break
                i += 1
        else:
            return None
        if selected_dex != self._selected_dex:
            self._widgets[self._selected_dex]._selected = 0
        self._selected_dex = selected_dex
        self._selected = value

    def enter(self: Self) -> None:
        self._widgets[self._selected_dex]._func()

    def surf(self: Self, surf: pg.Surface) -> None:
        self._widgets.append(self.Widget(surf))

    def button(self: Self, text: str, func: Callable=lambda: 1) -> None:
        self._widgets.append(
            self.Button(
                text,
                self._font,
                self._colors['unselected'],
                self._colors['selected'],
                func,
            ),
        )

    def render(self: Self, surf: pg.Surface) -> None:
        if self._background is not None:
            surf.blit(self._background, (0, 0))
        y = self._y
        for widget in self._widgets:
            surface = widget.surf
            surf.blit(surface, ((surf.width - surface.width) / 2, y))
            y += surface.height + self._gap

