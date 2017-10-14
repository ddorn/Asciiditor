import os
from functools import lru_cache

import pygame
import pygame.gfxdraw

from data_structures.sparsemap import Map
from data_structures.vector import Pos
from visual.colors import COLORS
from visual.font import Font

try:
    # fixing f****** dpi awareness of my computer
    import ctypes

    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except AttributeError:  # not windows
    pass

pygame.init()
pygame.key.set_repeat(200, 10)
os.environ['SDL_VIDEO_CENTERED'] = '1'

FONTNAME = 'assets/monaco.ttf'
DEFAULT_FONT_SIZE = 24
MAINFONT = Font(FONTNAME, DEFAULT_FONT_SIZE)
SMALLFONT = Font(FONTNAME, DEFAULT_FONT_SIZE * 0.75)
BIGFONT = Font(FONTNAME, DEFAULT_FONT_SIZE * 2)


class Asciiditor:
    FPS = 60

    def __init__(self, map_):

        self.map = map_  # type: Map

        self.screen = self.get_screen()  # type: pygame.SurfaceType
        self.clock = pygame.time.Clock()
        self.dirty_rects = [self.screen.get_rect()]

        self.offset = self.get_default_offset()
        self.start_drag_pos = None  # type: Pos
        self.start_drag_offset = None  # type: Pos

        self.cursor = Pos(0, 0)

        self.exit = False

    # Get stuff

    def get_default_offset(self):
        return Pos(250, 15)

    def get_screen(self):
        """Get the main screen."""
        return pygame.display.set_mode((0, 0), pygame.NOFRAME)

    def get_mouse_pos(self):
        x, y = pygame.mouse.get_pos()
        return Pos(x, y)

    # Core functions

    def run(self):
        """Start the debugger. stop it with `self.exit = True`"""
        while not self.exit:
            self.update()
            self.render()
            pygame.display.update(self.dirty_rects)
            self.clock.tick(self.FPS)
            self.dirty_rects = []

    def update(self):

        mouse = Pos(self.get_mouse_pos())

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.exit = 1
                return
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.exit = 1
                    return
                elif e.key == pygame.K_RIGHT:
                    self.move_cursor(1, 0)
                elif e.key == pygame.K_LEFT:
                    self.move_cursor(-1, 0)
                elif e.key == pygame.K_UP:
                    self.move_cursor(0, -1)
                elif e.key == pygame.K_DOWN:
                    self.move_cursor(0, 1)
                elif e.mod & pygame.KMOD_CTRL:
                    if e.key == pygame.K_r:  # reset position and size
                        self.offset = self.get_default_offset()
                        self.start_drag_pos = None
                        self.start_drag_offset = None

                        self.change_font_size(DEFAULT_FONT_SIZE)
                    elif e.key == pygame.K_EQUALS:  # I would like the + but apparently it doesn't work
                        self.change_font_size(1)
                    elif e.key == pygame.K_MINUS:
                        self.change_font_size(-1)
                else:
                    s = e.unicode  # type: str
                    if s and s.isprintable():
                        print('-', e.unicode, '-', ord(e.unicode), sep='')
                        self.map[self.cursor.row, self.cursor.col] = s
                        self.move_cursor(1, 0)
                        self.reset_screen()

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.set_cursor(*self.screen_to_map_pos(pygame.mouse.get_pos()))
                elif e.button == 3:
                    self.start_drag_pos = mouse
                    self.start_drag_offset = self.offset
                    self.reset_screen()
            elif e.type == pygame.MOUSEBUTTONUP:
                if e.button == 3:
                    self.start_drag_pos = None
                    self.start_drag_offset = None
                    self.reset_screen()

        # drag the code if needed
        if self.start_drag_pos is not None:
            actual_pos = mouse
            dx, dy = actual_pos - self.start_drag_pos

            if abs(dx) < 20:
                dx = 0
            if abs(dy) < 20:
                dy = 0

            self.offset = self.start_drag_offset + (dx, dy)
            self.map_to_screen_pos.cache_clear()

    def render(self):

        # clear the dirt
        for rect in self.dirty_rects:
            self.screen.fill(COLORS.BACKGROUND, rect)

        # render what we need

        cursor_rendered = False
        # use a copy because the list can grow and we don't care about the new rects
        dirty_rects = self.dirty_rects[:]
        for pos, char in self.map:
            for dirt_rect in dirty_rects:

                pos = Pos(pos)
                rect = pygame.Rect(self.map_to_screen_rect(pos))

                # if we need to rerender this part of the screen
                if rect.colliderect(dirt_rect):

                    bg = COLORS.BACKGROUND
                    color = COLORS.TEXT
                    if pos == self.cursor:
                        bg, color = color, bg
                        cursor_rendered = True

                    surf = MAINFONT.render_char(char, color, bg)
                    self.screen.blit(surf, rect)

                    # try to minimize the overlappings would be nice
                    self.dirty_rects.append(rect)
                    break

        if not cursor_rendered:
            char = self.map[self.cursor.row, self.cursor.col]
            rect = self.map_to_screen_rect(self.cursor)

            surf = MAINFONT.render_char(char, COLORS.BACKGROUND, COLORS.TEXT)
            self.screen.blit(surf, rect)

            self.dirty_rects.append(rect)

    # Change cursor, font or screen

    def move_cursor(self, dx, dy):
        self.set_cursor(*(self.cursor + (dx, dy)))

    def set_cursor(self, x, y):
        self.dirty_rects.append(self.map_to_screen_rect(self.cursor))
        self.cursor = Pos(x, y)
        self.dirty_rects.append(self.map_to_screen_rect(self.cursor))

    def change_font_size(self, dsize):
        self.set_font_size(MAINFONT.font_size + dsize)

    def set_font_size(self, size):
        MAINFONT.change_size(size)
        BIGFONT.set_size(size * 2)
        SMALLFONT.set_size(size * 0.75)
        self.map_to_screen_pos.cache_clear()
        self.reset_screen()

    def reset_screen(self):
        self.dirty_rects = [self.screen.get_rect()]

    # Convertion between the map (row, col) and screen coords

    @lru_cache(maxsize=None)
    def map_to_screen_pos(self, pos):
        """Convert the position of char/dot in the map to its coordinates in the screen."""
        return self.offset.x + MAINFONT.char_size.x * pos.col, self.offset.y + MAINFONT.char_size.y * pos.row

    def map_to_screen_rect(self, pos):
        return self.map_to_screen_pos(pos), MAINFONT.char_size

    def screen_to_map_pos(self, pos):
        return (pos[0] - self.offset.x) // MAINFONT.char_size.x, (pos[1] - self.offset.y) // MAINFONT.char_size.y