#!/usr/bin/env python
# coding: utf-8


class Tile:

    def __init__(self, x, y, z, data, format="jpeg"):
        self.x = x
        self.y = y
        self.z = z
        self.data = data
        self.format = format

    def get_coordinates(self):
        return self.x, self.y, self.z

    def get_TMS_coordinates(self):
        new_y = pow(2, self.z) - 1 - self.y
        return self.x, new_y, self.z

    def get_data(self):
        return self.data


class Tileset:

    def __init__(self, tile_list):
        self._tile_list = tile_list
        for tile in self._tile_list:
            if not isinstance(tile, Tile):
                raise Exception("Tile is not an instance of Tile class")

    def get_tiles_list(self):
        return self._tile_list
