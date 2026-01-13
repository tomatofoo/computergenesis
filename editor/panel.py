from typing import Self
from typing import Callable

import pygame as pg
from pygame.typing import Point


class _Widget(object):
    def __init__(self: Self, pos: Point, size: Point=(0, 0)) -> None:
        self._surf = pg.Surface(size)
        self._rect = pg.Rect(pos, size)
        self._pos = pos
        self._scroll = 0

    @property
    def surf(self: Self) -> pg.Surface:
        return self._surf

    @property
    def pos(self: Self) -> tuple:
        return (self._pos[0], self._pos[1] + self._scroll)

    @property
    def scroll(self: Self) -> Real:
        return self._scroll

    @scroll.setter
    def scroll(self: Self, value: Real) -> None:
        self._scroll = value
        self._rect.y = self._pos[1] + value

    def handle_event(self: Self, event: pg.Event) -> None:
        pass

    def update(self: Self,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        pass


class Button(_Widget): # Text Button
    # COLORS
    # red default
    # green hover
    # blue click

    def __init__(self: Self,
                 pos: Point,
                 text: str,
                 func: Callable,
                 font_size: int=14) -> None:

        super().__init__(pos)
        self._func = func
        self._font = pg.font.SysFont('Arial', font_size)
        text = self._font.render(text, 1, (255, 255, 255))
        self._rect = pg.Rect(pos, text.size)
        
        # Surfs
        default = pg.Surface(text.size)
        default.fill((255, 0, 0))
        hover = pg.Surface(text.size)
        hover.fill((0, 0, 255))
        click = pg.Surface(text.size)
        pg.draw.rect(
            click,
            (0, 0, 255),
            (0, 0, text.width, text.height),
            width=2,
        )

        self._surfs = [default, hover, click]
        for surf in self._surfs:
            surf.blit(text, (0, 0))
        self._surf = self._surfs[0]

    def handle_event(self: Self, event: pg.Event) -> None:
        if (event.type == pg.MOUSEBUTTONDOWN
            and self._rect.collidepoint(event.pos)):
                self._func()

    def update(self: Self,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        # slick boolean index
        collision = self._rect.collidepoint(mouse_pos)
        self._surf = self._surfs[collision]
        if mouse_pressed[0] and collision:
            self._surf = self._surfs[2]


class Input(_Widget): # Text Input
    def __init__(self: Self, pos: Point, font_size: int=12) -> None:
        pass

    def handle_event(self: Self, event: pg.Event) -> None:
        pass

    def update(self: Self,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        pass


class Panel(object):
    def __init__(self: Self, widgets: set[_Widget], min_scroll: Real) -> None:
        self._widgets = widgets
        self._scroll = 0
        self._min_scroll = min_scroll

    @property
    def widgets(self: Self) -> set[_Widget]:
        return self._widgets

    @widgets.setter
    def widgets(self: Self, value: set[_Widget]) -> None:
        self._widgets = value
    
    @property
    def scroll(self: Self) -> Real:
        return self._scroll

    @scroll.setter
    def scroll(self: Self, value: Real) -> None:
        self._scroll = pg.math.clamp(value, self._min_scroll, 0)
        for widget in self._widgets:
            widget.scroll = self._scroll

    def handle_event(self: Self, event: pg.Event) -> None:
        for widget in self._widgets:
            widget.handle_event(event)
        if event.type == pg.MOUSEWHEEL:
            self.scroll += event.precise_y * 10

    def update(self: Self,
               mouse_pos: Point,
               mouse_pressed: tuple[bool]) -> None:
        for widget in self._widgets:
            widget.update(mouse_pos, mouse_pressed)

    def render(self: Self, surf: pg.Surface) -> None:
        for widget in self._widgets:
            surf.blit(widget.surf, widget.pos)

