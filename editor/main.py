import os
import sys
import time
import math
import json
from typing import Self

import pygame as pg

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from data.levels import LEVELS
from modules.utils import FALLBACK_SURF
from modules.utils import gen_tile_key

from panel import Surface
from panel import Label
from panel import Button
from panel import Input
from panel import Panel


# The code is a bit sloppy but it works
class Game(object):

    _SCREEN_SIZE = (960, 720)
    _EDITOR_WIDTH = 720
    _SCREEN_FLAGS = pg.RESIZABLE | pg.SCALED
    _GAME_SPEED = 60

    def __init__(self: Self) -> None:
        pg.init()

        self._settings = {
            'vsync': 1,
        }
        self._screen = pg.display.set_mode(
            self._SCREEN_SIZE,
            flags=self._SCREEN_FLAGS,
            vsync=self._settings['vsync']
        )
        pg.display.set_caption('Level Editor')
        self._running = 0

        # Editor Variables
        pg.key.set_repeat(300, 75)

        self._colors = {
            'fill': (0, 0, 0),
            'grid': (255, 255, 255),
            'top': (0, 0, 0), # default top
            'bottom': (0, 0, 0), # default bottom
            'remove': (255, 0, 0), # remove tool
            'eyedropper': (0, 255, 0), # eyedropper
            'rect': (255, 255, 0),
            'semitile': (0, 255, 0),
       }

        self._keys = {
            'mod': (pg.K_LSHIFT, pg.K_RSHIFT),
            'mod2': (pg.K_LCTRL, pg.K_RCTRL),
            'zoom_in': (pg.K_z, ),
            'zoom_out': (pg.K_x, ),
            'vertical_increase': (pg.K_UP, pg.K_k),
            'vertical_decrease': (pg.K_DOWN, pg.K_j),
            'do': (pg.K_z, ), # undo redo
            'place': (pg.K_b, ),
            'remove': (pg.K_e, ),
            'eyedropper': (pg.K_i, ),
        }
        
        # Data
        self._default_data = {
            'texture': 0,
            'elevation': 0,
            'height': 1,
            'top': self._colors['top'],
            'bottom': self._colors['bottom'],
            'rect': None,
        }
        self._data = self._default_data.copy()
        self._hover_key = 'N/A'
        self._hover_data = None
        
        # Level Stuff
        self._level = None
        self._wall_textures = []
        self._tilemap = {}
        # self._dict = {}
        # TODO: MOVE TILEMAP TO DICT
        # TODO: ADD MARKERS
        # TODO: ADD THAT TO HISTORY
        
        # tools
        self._tool = 'place' # place, remove, eyedropper
        self._place_alpha = 128 # alpha of 'ghost' tile when placing
        
        # Panel
        self._initialize_panel()

        # Zoom
        self._zoom_step = 2
        self._min_zoom = 8 # anything below tanks performance
        self._zoom = 32 # tile size
       
        # Pos for top left
        self._pos = pg.Vector2(0, 0)

        # History
        self._history = [{}] # pos: (prev, new)
        self._change = 0

    def _initialize_panel(self: Self) -> None:
        # difference in y between widgets is 20

        self._fonts = {
            'title': pg.font.SysFont('Andale Mono', 16),
            'main': pg.font.SysFont('Andale Mono', 16),
        }
        self._fonts['title'].underline = 1

        self._widgets = {
            'path': Input(
                (self._EDITOR_WIDTH + 10, 30),
                width=220,
                max_chars=25,
                font=self._fonts['main'],
            ),
            'level': Input(
                (self._EDITOR_WIDTH + 10, 110),
                width=220,
                max_chars=25,
                font=self._fonts['main'],
            ),
            'tool': Label(
                (self._EDITOR_WIDTH + 10, 190),
                text=self._tool,
                font=self._fonts['main'],
            ),
            'current': {
                'surface': Surface(
                    (self._EDITOR_WIDTH + 10, 250),
                    surf=pg.Surface((0, 0)),
                ),
                'texture': Input(
                    (self._EDITOR_WIDTH + 60, 290),
                    width=170,
                    max_chars=25,
                    font=self._fonts['main'],
                ),
                'elevation': Input(
                    (self._EDITOR_WIDTH + 60, 310),
                    width=170,
                    max_chars=25,
                    font=self._fonts['main'],
                ),
                'height': Input(
                    (self._EDITOR_WIDTH + 60, 330),
                    width=170,
                    max_chars=25,
                    font=self._fonts['main'],
                ),
                'top': {
                    'r': Input(
                        (self._EDITOR_WIDTH + 60, 350),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'g': Input(
                        (self._EDITOR_WIDTH + 110, 350),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'b': Input(
                        (self._EDITOR_WIDTH + 160, 350),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                },
                'bottom': {
                    'r': Input(
                        (self._EDITOR_WIDTH + 60, 370),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'g': Input(
                        (self._EDITOR_WIDTH + 110, 370),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'b': Input(
                        (self._EDITOR_WIDTH + 160, 370),
                        width=40,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                },
                'rect': {
                    'left': Input(
                        (self._EDITOR_WIDTH + 60, 390),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'top': Input(
                        (self._EDITOR_WIDTH + 60, 410),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'width': Input(
                        (self._EDITOR_WIDTH + 60, 430),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'height': Input(
                        (self._EDITOR_WIDTH + 60, 450),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                },
                'semitile': {
                    'axis': Input(
                        (self._EDITOR_WIDTH + 60, 470),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'x': Input(
                        (self._EDITOR_WIDTH + 60, 490),
                        width=75,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'y': Input(
                        (self._EDITOR_WIDTH + 145, 490),
                        width=75,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                    'width': Input(
                        (self._EDITOR_WIDTH + 60, 510),
                        width=170,
                        max_chars=25,
                        font=self._fonts['main'],
                    ),
                },
            },
            'hover': {
                'surface': Surface(
                    (self._EDITOR_WIDTH + 10, 570),
                    surf=pg.Surface((0, 0)),
                ),
                'key': Label(
                    (self._EDITOR_WIDTH + 60, 610),
                    text='N/A',
                    font=self._fonts['main'],
                ),
                'texture': Label(
                    (self._EDITOR_WIDTH + 60, 630),
                    text='N/A',
                    font=self._fonts['main'],
                ),
                'elevation': Label(
                    (self._EDITOR_WIDTH + 60, 650),
                    text='N/A',
                    font=self._fonts['main'],
                ),
                'height': Label(
                    (self._EDITOR_WIDTH + 60, 670),
                    text='N/A',
                    font=self._fonts['main'],
                ),
                'top': {
                    'r': Label(
                        (self._EDITOR_WIDTH + 60, 690),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'g': Label(
                        (self._EDITOR_WIDTH + 110, 690),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'b': Label(
                        (self._EDITOR_WIDTH + 160, 690),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                },
                'bottom': {
                    'r': Label(
                        (self._EDITOR_WIDTH + 60, 710),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'g': Label(
                        (self._EDITOR_WIDTH + 110, 710),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'b': Label(
                        (self._EDITOR_WIDTH + 160, 710),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                },
                'rect': {
                    'left': Label(
                        (self._EDITOR_WIDTH + 60, 730),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'top': Label(
                        (self._EDITOR_WIDTH + 60, 750),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'width': Label(
                        (self._EDITOR_WIDTH + 60, 770),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'height': Label(
                        (self._EDITOR_WIDTH + 60, 790),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                },
                'semitile': {
                    'axis': Label(
                        (self._EDITOR_WIDTH + 60, 810),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'x': Label(
                        (self._EDITOR_WIDTH + 60, 830),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'y': Label(
                        (self._EDITOR_WIDTH + 145, 830),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                    'width': Label(
                        (self._EDITOR_WIDTH + 60, 850),
                        text='N/A',
                        font=self._fonts['main'],
                    ),
                }
            },
        }
        self._widgets['path'].text = 'data/maps/0.json'
        self._widgets['level'].text = '0'
        current = self._widgets['current'] 
        self._current_from_data(self._data)
        hover = self._widgets['hover']
        self._update_widgets()

        self._panel = Panel(
            widgets={
                Label(
                    (self._EDITOR_WIDTH + 10, 10),
                    text='File Path',
                    font=self._fonts['title'],
                ),
                self._widgets['path'],
                Button(
                    (self._EDITOR_WIDTH + 10, 50),
                    text='Save',
                    func=self._save,
                    font=self._fonts['main'],
                ),
                Button(
                    (self._EDITOR_WIDTH + 60, 50),
                    text='Load',
                    func=self._load,
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 90),
                    text='Level Index',
                    font=self._fonts['title'],
                ),
                self._widgets['level'],
                Button(
                    (self._EDITOR_WIDTH + 10, 130),
                    text='Load',
                    func=self._load_level,
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 170),
                    text='Tool',
                    font=self._fonts['title'],
                ),
                self._widgets['tool'],
                Label(
                    (self._EDITOR_WIDTH + 10, 230),
                    text='Tile',
                    font=self._fonts['title'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 290),
                    text='Text',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 310),
                    text='Elev',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 330),
                    text='Hieg',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 350),
                    text='Top',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 370),
                    text='Bott',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 390),
                    text='Rect',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 470),
                    text='Semi',
                    font=self._fonts['main'],
                ),
                current['surface'],
                current['texture'],
                current['elevation'],
                current['height'],
                *current['top'].values(),
                *current['bottom'].values(),
                *current['rect'].values(),
                *current['semitile'].values(),
                Label(
                    (self._EDITOR_WIDTH + 10, 550),
                    'Hover',
                    self._fonts['title'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 610),
                    text='Key',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 630),
                    text='Text',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 650),
                    text='Elev',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 670),
                    text='Hieg',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 690),
                    text='Top',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 710),
                    text='Bott',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 730),
                    text='Rect',
                    font=self._fonts['main'],
                ),
                Label(
                    (self._EDITOR_WIDTH + 10, 810),
                    text='Semi',
                    font=self._fonts['main'],
                ),
                hover['key'],
                hover['surface'],
                hover['texture'],
                hover['elevation'],
                hover['height'],
                *hover['top'].values(),
                *hover['bottom'].values(),
                *hover['rect'].values(),
                *hover['semitile'].values(),
            },
            min_scroll=-self._SCREEN_SIZE[1],
        ) 

    def _save(self: Self) -> None:
        with open(self._widgets['path'].text, 'w') as file:
            json.dump({'tilemap': self._tilemap}, file)

    def _load(self: Self) -> None:
        try:
            with open(self._widgets['path'].text, 'r') as file:
                data = json.loads(file.read())
                self._tilemap = data['tilemap']
        except:
            pass

    def _load_level(self: Self) -> None:
        try:
            self._level = LEVELS[int(self._widgets['level'].text)]
            self._tilemap = self._level._walls._tilemap
            self._wall_textures = self._level._walls._textures
        except:
            self._level = None

    def _update_surfaces(self: Self) -> None: # current and hovers
        size = self._fonts['main'].get_height() + 20

        surf = pg.Surface((size * 2, size))
        self._draw_tile(None, self._data, (0, 0), size=size, surf=surf)
        rect = (size, 0, size, size / 2)
        pg.draw.rect(surf, self._data['top'], rect)
        pg.draw.rect(surf, (255, 255, 255), rect, width=1)
        rect = (size, size / 2, size, size / 2)
        pg.draw.rect(surf, self._data['bottom'], rect)
        pg.draw.rect(surf, (255, 255, 255), rect, width=1)
        self._widgets['current']['surface'].surf = surf

        surf = pg.Surface((size * 2, size))
        if self._hover_data is not None:
            self._draw_tile(
                None,
                self._hover_data,
                (0, 0),
                size=size,
                surf=surf,
            )
            rect = (size, 0, size, size / 2)
            pg.draw.rect(surf, self._hover_data['top'], rect)
            pg.draw.rect(surf, (255, 255, 255), rect, width=1)
            rect = (size, size / 2, size, size / 2)
            pg.draw.rect(surf, self._hover_data['bottom'], rect)
            pg.draw.rect(surf, (255, 255, 255), rect, width=1)
        self._widgets['hover']['surface'].surf = surf

    def _update_current(self: Self) -> None:
        current = self._widgets['current']
        # I'm not sure if there's a better way
        try:
            texture = int(current['texture'].text)
        except ValueError:
            texture = 0
        self._data['texture'] = texture
        try:
            elevation = float(current['elevation'].text)
        except ValueError:
            elevation = 0
        self._data['elevation'] = elevation
        try:
            height = float(current['height'].text)
        except ValueError:
            height = 1
        self._data['height'] = height
        try:
            top = current['top']
            top = (
                int(top['r'].text),
                int(top['g'].text),
                int(top['b'].text),
            )
        except ValueError:
            top = (0, 0, 0)
        self._data['top'] = top
        try:
            bottom = current['bottom']
            bottom = (
                int(bottom['r'].text),
                int(bottom['g'].text),
                int(bottom['b'].text),
            )
        except ValueError:
            bottom = (0, 0, 0)
        self._data['bottom'] = bottom
        try:
            rect = current['rect']
            rect = (
                float(rect['left'].text),
                float(rect['top'].text),
                float(rect['width'].text),
                float(rect['height'].text),
            )
            if rect == (0, 0, 1, 1):
                rect = None
        except ValueError:
            rect = None
        self._data['rect'] = rect
        try:
            semitile = current['semitile']
            semitile = {
                'axis': int(semitile['axis'].text),
                'pos': (float(semitile['x'].text),
                        float(semitile['y'].text)),
                'width': float(semitile['width'].text),
            }
        except ValueError:
            semitile = None
        self._data['semitile'] = semitile

    def _current_from_data(self: Self, data: dict) -> None:
        current = self._widgets['current']
        current['texture'].text = str(data['texture'])
        current['elevation'].text = str(data['elevation'])
        current['height'].text = str(data['height'])
        top = current['top']
        top['r'].text = str(data['top'][0])
        top['g'].text = str(data['top'][1])
        top['b'].text = str(data['top'][2])
        bottom = current['bottom']
        bottom['r'].text = str(data['bottom'][0])
        bottom['g'].text = str(data['bottom'][1])
        bottom['b'].text = str(data['bottom'][2])
        rect = current['rect']
        data_rect = data.get('rect')
        if data_rect is not None:
            rect['left'].text = str(data_rect[0])
            rect['top'].text = str(data_rect[1])
            rect['width'].text = str(data_rect[2])
            rect['height'].text = str(data_rect[3])
        else:
            rect['left'].text = '0'
            rect['top'].text = '0'
            rect['width'].text = '1'
            rect['height'].text = '1'
        semitile = current['semitile']
        data_semitile = data.get('semitile')
        if data_semitile is not None:
            semitile['axis'].text = str(data_semitile['axis'])
            semitile['x'].text = str(data_semitile['pos'][0])
            semitile['y'].text = str(data_semitile['pos'][1])
            semitile['width'].text = str(data_semitile['width'])
        else:
            semitile['axis'].text = '0'
            semitile['x'].text = ''
            semitile['y'].text = ''
            semitile['width'].text = ''

    def _update_hover(self: Self) -> None:
        data = self._hover_data
        if data is None:
            data = {
                'texture': 'N/A',
                'elevation': 'N/A',
                'height': 'N/A',
                'top': 'N/A',
                'bottom': 'N/A',
                'rect': ('N/A', 'N/A', 'N/A', 'N/A'),
                'semitile': {
                    'axis': 'N/A',
                    'pos': ('N/A', 'N/A'),
                    'width': 'N/A',
                }
            }
        hover = self._widgets['hover']
        hover['key'].text = self._hover_key
        hover['texture'].text = str(data['texture'])
        hover['elevation'].text = str(data['elevation'])
        hover['height'].text = str(data['height'])
        top = hover['top']
        top['r'].text = str(data['top'][0])
        top['g'].text = str(data['top'][1])
        top['b'].text = str(data['top'][2])
        bottom = hover['bottom']
        bottom['r'].text = str(data['bottom'][0])
        bottom['g'].text = str(data['bottom'][1])
        bottom['b'].text = str(data['bottom'][2])
        rect = hover['rect']
        data_rect = data.get('rect')
        if data_rect is not None:
            rect['left'].text = str(data_rect[0])
            rect['top'].text = str(data_rect[1])
            rect['width'].text = str(data_rect[2])
            rect['height'].text = str(data_rect[3])
        else:
            rect['left'].text = '0'
            rect['top'].text = '0'
            rect['width'].text = '1'
            rect['height'].text = '1'
        semitile = hover['semitile']
        data_semitile = data.get('semitile')
        if data_semitile is not None:
            semitile['axis'].text = str(data_semitile['axis'])
            semitile['x'].text = str(data_semitile['pos'][0])
            semitile['y'].text = str(data_semitile['pos'][1])
            semitile['width'].text = str(data_semitile['width'])

    def _update_widgets(self: Self) -> None:
        self._widgets['tool'].text = self._tool
        self._update_current()
        self._update_hover()
        self._update_surfaces()
        
    def _get_screen_pos(self: Self, x: int, y: int) -> None:
        return (
            (math.floor(self._pos[0]) + x - self._pos[0]) * self._zoom,
            (math.floor(self._pos[1]) + y - self._pos[1]) * self._zoom,
        )

    def _draw_grid(self: Self) -> None:
        for y in range(math.ceil(self._SCREEN_SIZE[1] / self._zoom) + 1):
            for x in range(math.ceil(self._SCREEN_SIZE[0] / self._zoom) + 1):
                self._screen.set_at(
                    self._get_screen_pos(x, y),
                    self._colors['grid'],
                )

    def _draw_tile(self: Self,
                   alpha: Optional[Real],
                   data: dict,
                   pos: tuple,
                   size: Optional[int]=None,
                   surf: Optional[pg.Surface]=None) -> None:

        if size is None:
            size = self._zoom
        if surf is None:
            surf = self._screen

        # surface is what's rendered
        # surf is where surface is rendered

        surface = pg.Surface((size, size))
        semizoom = size / 2
        quarterzoom = size / 4
        # Texture
        try:
            texture = self._wall_textures[data['texture']]._surf
        except:
            texture = FALLBACK_SURF
        surface.blit(
            pg.transform.scale(texture, (size, size)), (0, 0),
        )
        # Rect
        rect = data.get('rect')
        if rect is None:
            rect = (0, 0, size, size)
        else:
            rect = (
                rect[0] * size,
                rect[1] * size,
                rect[2] * size,
                rect[3] * size,
            )
        pg.draw.rect(surface, self._colors['rect'], rect, width=1)
        # Semitile
        semitile = data.get('semitile')
        if semitile is not None:
            rect = (
                (semitile['pos'][0] * size,
                 semitile['pos'][1] * size),
                (1, semitile['width'] * size)
                if semitile['axis']
                else (semitile['width'] * size, 1)
            )
            pg.draw.rect(surface, self._colors['semitile'], rect)
        # Draw
        surface.set_alpha(alpha)
        surf.blit(surface, pos)

    def _draw_tiles(self: Self) -> None:
        for y in range(math.ceil(self._SCREEN_SIZE[1] / self._zoom) + 1):
            for x in range(math.ceil(self._SCREEN_SIZE[0] / self._zoom) + 1):
                tile = (math.floor(self._pos[0]) + x,
                        math.floor(self._pos[1]) + y)
                tile_key = gen_tile_key(tile)
                data = self._tilemap.get(tile_key)
                if data is not None:
                    self._draw_tile(None, data, self._get_screen_pos(x, y)) 

    def _draw_panel(self: Self) -> None:
        rect = (
            self._EDITOR_WIDTH,
            0,
            self._SCREEN_SIZE[0] - self._EDITOR_WIDTH,
            self._SCREEN_SIZE[1],
        )
        pg.draw.rect(self._screen, (0, 0, 0), rect)
        self._panel.render(self._screen)
        pg.draw.rect(self._screen, (255, 255, 255), rect, width=1)

    def _draw_tool(self: Self, mouse_pos: tuple) -> None:
        x = self._zoom * (
            math.floor(self._pos[0] + mouse_pos[0] / self._zoom)
            - self._pos[0]
        )
        y = self._zoom * (
            math.floor(self._pos[1] + mouse_pos[1] / self._zoom)
            - self._pos[1]
        )
        if self._tool == 'place':
            self._draw_tile(self._place_alpha, self._data, (x, y))
        else:
            pg.draw.rect(
                self._screen,
                self._colors[self._tool],
                (x, y, self._zoom, self._zoom),
                width=1,
            )

    def run(self: Self) -> None:
        self._running = 1
        start_time = time.time()

        while self._running:
            delta_time = time.time() - start_time
            start_time = time.time()

            rel_game_speed = delta_time * self._GAME_SPEED

            keys = pg.key.get_pressed()
            mod = any(keys[key] for key in self._keys['mod'])
            mod2 = any(keys[key] for key in self._keys['mod2'])
            current = self._widgets['current']
            for event in pg.event.get():
                self._panel.handle_event(event)
                if event.type == pg.QUIT:
                    self._running = 0
                if not self._panel.focused:
                    if event.type == pg.KEYDOWN:
                        if not mod and not mod2:
                            # zoom
                            if event.key in self._keys['zoom_in']:
                                self._zoom += self._zoom_step
                            elif event.key in self._keys['zoom_out']:
                                self._zoom = max(
                                    self._zoom - self._zoom_step,
                                    self._min_zoom,
                                )
                            elif event.key in self._keys['place']:
                                self._tool = 'place'
                            elif event.key in self._keys['remove']:
                                self._tool = 'remove'
                            elif event.key in self._keys['eyedropper']:
                                self._tool = 'eyedropper'

                        # Height / Elevation
                        if event.key in self._keys['vertical_increase']:
                            if mod:
                                current['elevation'].text = str(
                                    round(self._data['elevation'] + 0.05, 3),
                                )
                            else:
                                current['height'].text = str(
                                    round(self._data['height'] + 0.05, 3),
                                )
                        elif event.key in self._keys['vertical_decrease']:
                            if mod:
                                current['elevation'].text = str(
                                    round(self._data['elevation'] - 0.05, 3),
                                )
                            else:
                                current['height'].text = str(
                                    round(self._data['height'] - 0.05, 3),
                                )
                        # History
                        if mod2 and event.key in self._keys['do']:
                            # redo
                            if mod:
                                if self._change < len(self._history) - 1:
                                    change = self._history[self._change]
                                    for key, value in change.items():
                                        if value[1] is None:
                                            data = self._tilemap.get(key)
                                            if data is not None:
                                                self._tilemap.pop(key)
                                        else:
                                            self._tilemap[key] = value[1]
                                    self._change += 1
                            # undo
                            elif self._change > 0:
                                self._change -= 1
                                change = self._history[self._change]
                                for key, value in change.items():
                                    if value[0] is None:
                                        if self._tilemap.get(key) is not None:
                                            self._tilemap.pop(key)
                                    else:
                                        self._tilemap[key] = value[0]

                    # Editing
                    elif event.type == pg.MOUSEBUTTONUP: # history
                        if self._history[-1]:
                            if self._change < len(self._history) - 1:
                                # cut off tree after user makse a change
                                self._history = [
                                    *(self._history[:self._change]),
                                    self._history[-1],
                                ]
                            self._change = len(self._history)
                            self._history.append({})
                self._update_widgets()
            
            if not self._panel.focused:
                mouse_pos = pg.mouse.get_pos()
                mouse = pg.mouse.get_pressed()
                if mouse_pos[0] < self._EDITOR_WIDTH:
                    pos = (
                        self._pos[0] + mouse_pos[0] / self._zoom,
                        self._pos[1] + mouse_pos[1] / self._zoom,
                    )
                    tile_key = gen_tile_key(pos)
                    # set
                    tile_data = self._tilemap.get(tile_key)
                    self._hover_key = tile_key
                    self._hover_data = tile_data
                    if mouse[0]:
                        if self._tool == 'place':
                            if tile_data != self._data:
                                data = self._data.copy()
                                self._history[-1][tile_key] = (tile_data, data)
                                self._tilemap[tile_key] = data
                        # remove
                        elif self._tool == 'remove' and tile_data is not None:
                            self._history[-1][tile_key] = (
                                self._tilemap.pop(tile_key),
                                None,
                            )
                        elif self._tool == 'eyedropper':
                            if tile_data is None:
                                self._data = self._default_data.copy()
                            else:
                                self._data = tile_data.copy()
                            self._current_from_data(self._data)
                            self._update_surfaces()

                movement = pg.Vector2(
                    keys[pg.K_d] - keys[pg.K_a],
                    keys[pg.K_s] - keys[pg.K_w],
                )
                if mod:
                    self._pos += movement * 5 / self._zoom * rel_game_speed
                else:
                    self._pos += movement * 2 / self._zoom * rel_game_speed

            self._panel.update(mouse_pos, mouse)
            
            self._screen.fill(self._colors['fill'])
            self._draw_grid()
            self._draw_tiles()
            self._draw_tool(mouse_pos)
            self._draw_panel()

            pg.display.update()

        pg.quit()


if __name__ == '__main__':
    Game().run()

