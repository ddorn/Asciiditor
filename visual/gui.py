import logging
import multiprocessing
import os
from functools import lru_cache

import pygame
import pygame.gfxdraw

from config import Config
from data_structures.sparsemap import Map
from data_structures.vector import Pos
from helper.timer import repeat_every
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


def run_cmd(cmd: str):
    logging.info("running %s", cmd)
    os.system(cmd)


class Asciiditor:
    FPS = 60

    def __init__(self, file_name, conf):

        self.file_name = file_name
        self.map = self.load(file_name)

        self.config = conf  # type: Config

        self.screen = self.get_screen()  # type: pygame.SurfaceType
        self.clock = pygame.time.Clock()
        self.dirty_rects = []

        self._offset = self.get_default_offset()
        self.start_drag_pos = None  # type: Pos
        self.start_drag_offset = None  # type: Pos
        self.left_bar_pos = 42.1  # placeholder

        self.cursor = Pos(0, 0)
        self.overtype = True

        self.exit = False

        repeat_every(10)(self.save)

        # Log if the FPS drops
        @repeat_every(1, start_offset=1)
        def get_fps():
            fps = self.clock.get_fps()
            if fps < self.FPS / 2:
                logging.warning('Low fps: %s', fps)

        self.reset_screen()

    # Get stuff

    def get_default_offset(self):
        return Pos(250, 15)

    def get_screen(self):
        """Get the main screen."""
        if self.config.retina:
            w, h = pygame.display.list_modes()[0]
            return pygame.display.set_mode((w, h), pygame.RESIZABLE)
        else:
            return pygame.display.set_mode((0, 0), pygame.NOFRAME)

    def get_mouse_pos(self):
        x, y = pygame.mouse.get_pos()
        if self.config.retina:
            x *= 2
            y *= 2
        return Pos(x, y)

    # Core gui functions

    def run(self):
        """Start the debugger. stop it with `self.quit()`"""
        try:
            while not self.exit:
                self.update()
                self.update_left_bar()
                self.render()
                pygame.display.update(self.dirty_rects)
                self.clock.tick(self.FPS)
                self.dirty_rects = []
        except BaseException:
            self.quit()
            raise

    def quit(self):
        self.exit = True
        self.save()

    def update(self):

        mouse = self.get_mouse_pos()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return self.quit()

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return self.quit()
                elif e.key == pygame.K_RIGHT:
                    self.move_cursor(1, 0)
                elif e.key == pygame.K_LEFT:
                    self.move_cursor(-1, 0)
                elif e.key == pygame.K_UP:
                    self.move_cursor(0, -1)
                elif e.key == pygame.K_DOWN:
                    self.move_cursor(0, 1)
                elif e.key == pygame.K_RETURN:
                    self.map.insert(self.map_cursor, '\n')
                    self.set_cursor(self.map.col_min, self.cursor.row + 1)
                    self.reset_screen()
                elif e.key == pygame.K_BACKSPACE:
                    self.move_cursor(-1, 0)
                    self.map.suppr((self.cursor.row, self.cursor.col))
                    self.reset_screen()
                elif e.key == pygame.K_DELETE:
                    self.map.suppr((self.cursor.row, self.cursor.col))
                    self.reset_screen()
                elif e.key == pygame.K_INSERT:
                    self.overtype = not self.overtype
                    self.dirty_rects.append(self.map_to_screen_rect(self.cursor))
                elif e.key == pygame.K_F5:
                    self.launch_debugger()
                elif e.mod & pygame.KMOD_CTRL:
                    if e.key == pygame.K_r:  # reset position and size
                        self.offset = self.get_default_offset()
                        self.start_drag_pos = None
                        self.start_drag_offset = None
                        self.cursor = Pos(0, 0)
                        self.set_font_size(DEFAULT_FONT_SIZE)
                    elif e.key == pygame.K_EQUALS:  # I would like the + but apparently it doesn't work
                        self.change_font_size(1)
                    elif e.key == pygame.K_MINUS:
                        self.change_font_size(-1)
                    elif e.key == pygame.K_s:
                        self.save()
                else:
                    s = e.unicode  # type: str
                    if s and s.isprintable():
                        if self.overtype:
                            self.map[self.cursor.row, self.cursor.col] = s
                            # no need to update more than where the cursor was and it's done by move.cursor
                        else:
                            self.map.insert(self.map_cursor, s)
                            self.reset_screen()

                        self.move_cursor(1, 0)
                        self.update_left_bar()

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.set_cursor(*self.screen_to_map_pos(self.get_mouse_pos()))
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
                rect = self.map_to_screen_rect(pos)

                # if we need to rerender this part of the screen
                if rect.colliderect(dirt_rect):

                    bg = COLORS.BACKGROUND
                    color = COLORS.TEXT
                    if pos == self.cursor and self.overtype:
                        bg, color = color, bg
                        cursor_rendered = True

                    surf = MAINFONT.render_char(char, color, bg)
                    self.screen.blit(surf, rect)

                    # try to minimize the overlappings would be nice
                    if not dirt_rect.contains(rect):
                        self.dirty_rects.append(rect)
                    break

        cursor_rect = self.map_to_screen_rect(self.cursor)
        if not cursor_rendered and self.has_dirt(cursor_rect):
            if self.overtype:
                char = self.map[self.cursor.row, self.cursor.col]

                surf = MAINFONT.render_char(char, COLORS.BACKGROUND, COLORS.TEXT)
                self.screen.blit(surf, cursor_rect)
            else:
                rect = self.map_to_screen_rect(self.cursor)
                rect.width = 2
                self.screen.fill(COLORS.TEXT, rect)

            self.dirty_rects.append(cursor_rect)

        left_bar_rect = self.get_left_bar_rect()
        if self.has_dirt(left_bar_rect):
            self.screen.fill(COLORS.TEXT, left_bar_rect)
            self.dirty_rects.append(left_bar_rect)

    # Change cursor, font, offset or screen

    @property
    def offset(self):
        """Offset of the topright of the code vs the topright of the screen."""
        return self._offset

    @offset.setter
    def offset(self, value):
        self.map_to_screen_pos.cache_clear()
        self._offset = value
        self.reset_screen()
        self.update_left_bar()

    @property
    def map_cursor(self):
        """Get the position of the cursor in the map ((row, col) instead of (x, y))."""
        return Pos(self.cursor.row, self.cursor.col)

    def move_cursor(self, dx, dy):
        self.set_cursor(*(self.cursor + (dx, dy)))

    def set_cursor(self, x, y):
        self.dirty_rects.append(self.map_to_screen_rect(self.cursor))
        self.cursor = Pos(x, y)
        new_rect = pygame.Rect(self.map_to_screen_rect(self.cursor))
        self.dirty_rects.append(new_rect)

        screen_rect = self.screen.get_rect()  # type: pygame.rect.RectType
        if new_rect.x < 0:
            # the modulo part it to keep the grid aligned with what it was before,
            # just changing by a mutliple of charsize
            self.offset -= new_rect.x - new_rect.x % MAINFONT.char_size.x, 0
        elif new_rect.right > screen_rect.right:
            # don't ask why it works
            self.offset += ((screen_rect.right - new_rect.left) // MAINFONT.char_size.x - 1) * MAINFONT.char_size.x, 0

        if new_rect.y < 0:
            self.offset -= 0, new_rect.y - new_rect.y % MAINFONT.char_size.y
        elif new_rect.bottom > screen_rect.bottom:
            self.offset += 0, ((screen_rect.bottom - new_rect.top) // MAINFONT.char_size.y - 1) * MAINFONT.char_size.y

    def change_font_size(self, dsize):
        self.set_font_size(MAINFONT.font_size + dsize)

    def set_font_size(self, size):
        MAINFONT.set_size(size)
        BIGFONT.set_size(size * 2)
        SMALLFONT.set_size(size * 0.75)
        logging.info('Main font size changed to %s', MAINFONT.font_size)
        self.map_to_screen_pos.cache_clear()
        self.reset_screen()

    def reset_screen(self):
        self.dirty_rects = [self.screen.get_rect()]
        self.update_left_bar()

    def update_left_bar(self):
        """Check if the left bar has changed and if so, draw it agin on next render."""
        pos = self.map_to_screen_pos(Pos(self.map.col_min, 0))[0] - 1

        if self.left_bar_pos != pos:
            rect = self.get_left_bar_rect()
            self.dirty_rects.append(rect)
            rect = rect.copy()
            rect.x = pos
            self.dirty_rects.append(rect)
            self.left_bar_pos = rect.x

    def get_left_bar_rect(self):
        return pygame.Rect(self.left_bar_pos, 0, 1, self.screen.get_height())

    def has_dirt(self, rect):
        return rect.collidelist(self.dirty_rects) != -1

    # Convertion between the map (row, col) and screen coords

    @lru_cache(maxsize=None)
    def map_to_screen_pos(self, pos):
        """Convert the position of char/dot in the map to its coordinates in the screen."""
        return self.offset.x + MAINFONT.char_size.x * pos.col, self.offset.y + MAINFONT.char_size.y * pos.row

    def map_to_screen_rect(self, pos):
        return pygame.Rect(self.map_to_screen_pos(pos), MAINFONT.char_size)

    def screen_to_map_pos(self, pos):
        return (pos[0] - self.offset.x) // MAINFONT.char_size.x, (pos[1] - self.offset.y) // MAINFONT.char_size.y

    # File functionnalities

    def save(self, file_name=None):
        """Save the file. file_name defaults to self.file_name"""

        # Allow use an other file for a "Save As"option
        file_name = file_name or self.file_name
        with open(file_name, 'w', encoding='utf-8') as f:
            nb_bytes = f.write(self.map[:, :])

        logging.info('File saved at %s. %s bytes saved', file_name, nb_bytes)

    def load(self, file_name=None):
        """Load or create the file at file_name (defaults to self.file_name."""

        file_name = file_name or self.file_name
        logging.info('start loading %s', file_name)

        # create it if it doesn't exists
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                s = f.read()
                length = len(s)
                map_ = Map(s)

            logging.info('%s load %s char success', file_name, length)
        except FileNotFoundError:
            map_ = Map()
            logging.info("File does not exist, creating empty Map.")
        return map_

    def launch_debugger(self):
        self.save()
        logging.info("Creating debugger procces")
        p = multiprocessing.Process(target=run_cmd, args=(self.config.debugger_command.format(file=self.file_name),))
        logging.info("Starting debugger process")
        p.start()
        logging.info("Debugger started")
