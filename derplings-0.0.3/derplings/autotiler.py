import os

from . import rules
import pygame
import pyscroll

EMPTY = 1
DIRT = 2

DEBUG_CODES = 0

POWERS9 = [1, 2, 4, 8, 16, 32, 64, 128, 256]
POWERS3 = [64, 128, 256]


class AutoTiler(pyscroll.PyscrollDataAdapter):
    def __init__(self, tilemap, tile_size):
        super(AutoTiler, self).__init__()

        # required for pyscroll
        self._old_view = None
        self.tile_size = tile_size
        self.map_size = 0, 0
        self.visible_tile_layers = [0]

        self.last_value = 0
        self.last_x = None
        self.last_y = None
        self.scan_x = 0
        self.total_checks = 0
        self.cached_checks = 0

        self.tile_class_map = tilemap
        self.tile_map = [list([0] * 1024) for i in range(1024)]
        self.font = None

        self.tilesets = {
            'dirt-empty': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
        }
        self.all_tiles = list()
        self.load_textures()

    def score3(self, x, y, secondary):
        tiles = [self.get_tile_class(x, y) for x, y in ((x, y - 1), (x, y), (x, y + 1))]
        return sum(i for v, i in zip(tiles, POWERS3) if v == secondary)

    def score9(self, x, y, secondary):
        tiles = [self.get_tile_class(x, y) for x, y in ((x - 1, y - 1), (x - 1, y), (x - 1, y + 1), (x, y - 1), (x, y),
                                                        (x, y + 1), (x + 1, y - 1), (x + 1, y), (x + 1, y + 1))]
        return sum(i for v, i in zip(tiles, POWERS9) if v == secondary)

    def load_textures(self):
        self.font = pygame.font.Font(None, 18)

        def load(filename):
            path = os.path.join("assets", "tiles", filename + ".png")
            surface = pygame.image.load(path).convert_alpha()
            surface = pygame.transform.smoothscale(surface, self.tile_size).convert_alpha()
            return surface

        blank = pygame.Surface((32, 32))
        blank.fill((64, 64, 64))
        self.all_tiles = [
            blank,
            load("grassMid"),
            load("grassHalfRight"),
            load("grassHalfLeft"),
            load("grassHalf"),
            load("grassCliffLeft"),
            load("grassCliffRight"),
            load("grassLeft"),
            load("grassRight"),
            load("box"),
            load("hill_bottom"),
            load("hill_face"),
            load("hill_top"),
            load("grassCenter"),
            load("grassCenter"),
            load("grassCenter"),
            load("grassCenter"),
        ]
        for i in range(1000):
            self.all_tiles.append(blank.copy())

    def edge_tile(self, x, y, l, primary, secondary, palette):
        if self.last_y == y:
            if self.last_x + 1 != x:
                self.last_value = 0
                self.scan_x = x
        else:
            self.last_value = 0
            self.last_y = y
            self.scan_x = x

        self.last_x = x
        self.total_checks += 1
        if x - self.scan_x == 0:
            self.last_value = self.score9(x, y, secondary)
        else:
            self.cached_checks += 1
            self.last_value >>= 3
            self.last_value += self.score3(x + 1, y, secondary)

        tile_type = rules.standard8.get(self.last_value, 0)
        tile_id = palette[tile_type]

        # make new image with the score drawn on it
        if DEBUG_CODES:
            try:
                tile = self.all_tiles[tile_id].copy()
                text = self.font.render(str(self.last_value), 0, (0, 0, 0))
                tile.blit(text, (0, 0))
                tile_id = len(self.all_tiles)
                self.all_tiles.append(tile)
            except AttributeError:
                pass

        self.tile_map[y][x] = tile_id

    def get_tile_class(self, x, y):
        try:
            return self.tile_class_map[y][x]
        except IndexError:
            return 0

    def set_tile_class(self, x, y, palette):
        self.edge_tile(x, y, 0, DIRT, EMPTY, palette)

    def get_tile_value(self, x, y, l):
        try:
            return self.tile_map[y][x]
        except IndexError:
            return 0

    def get_tile_image(self, x, y, l):
        palette = self.tilesets['dirt-empty']
        self.set_tile_class(x, y, palette)
        tile_number = self.get_tile_value(x, y, l)
        tile = self.all_tiles[tile_number]
        return tile
