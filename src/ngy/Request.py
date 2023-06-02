#!/usr/bin/env python
# coding: utf-8

import ngy.Map_func
import ngy.Magic_Request
import ngy.Tiles
from urllib.parse import urlencode
import sqlite3
import os


class Request:

    def __init__(self, bounds, zoom_list, layer="GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR.CV",
                 style="normal", projection="PM", format="jpeg"):
        self.bounds = (min(bounds[1], bounds[3]),
                       min(bounds[0], bounds[2]),
                       max(bounds[1], bounds[3]),
                       max(bounds[0], bounds[2]))  # WGS 84 Coordinates
        self.zoom_list = zoom_list
        self.layer = layer
        self.style = style
        self.projection = projection
        self.format = format
        self._tile_set = None
        self._request_list = []
        self._base_url = "https://wxs.ign.fr/an7nvfzojv5wa96dsga5nk8w/geoportail/wmts"

        self._headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'wxs.ign.fr',
            'Referer': 'http://www.geoportail.gouv.fr/swf/geoportal-visu-1.3.2.swf',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0',
        }

    def get_number_of_tiles(self):
        self._build_request_list()
        return len(self._request_list)

    def _build_request_list(self):
        self._request_list = []
        _default_value = {
            'layer': self.layer,
            'style': self.style,
            'tilematrixset': self.projection,
            'Service': 'WMTS',
            'Request': 'GetTile',
            'Version': '1.0.0',
            'Format': 'image/' + self.format
        }

        for k in self.zoom_list:
            top_left_corner = ngy.Map_func.Coord._make(
                ngy.Map_func.convert_coord((min(self.bounds[0], self.bounds[2]), max(self.bounds[1], self.bounds[3])),
                                           ngy.Map_func.MATRIX_SET_DATA, k, self.projection))

            bot_right_corner = ngy.Map_func.Coord._make(
                ngy.Map_func.convert_coord((max(self.bounds[0], self.bounds[2]), min(self.bounds[1], self.bounds[3])),
                                           ngy.Map_func.MATRIX_SET_DATA, k, self.projection))

            def url_build(i, j, zoom):
                _values = _default_value
                _values['TileCol'] = i
                _values['TileRow'] = j
                _values['TileMatrix'] = zoom
                return self._base_url + '?' + urlencode(_values)

            for j in range(top_left_corner.lat, bot_right_corner.lat + 1):
                for i in range(top_left_corner.lon, bot_right_corner.lon + 1):
                    self._request_list.append({'x': i, 'y': j, 'z': k, 'url': url_build(i, j, k)})

    def fetch_data(self):
        if not self._request_list:
            self._build_request_list()
        _data = ngy.Magic_Request.async_req([_item['url'] for _item in self._request_list], headers=self._headers)
        # TODO : To optimize
        _temp = list(zip(self._request_list, _data))
        _temp2 = [ngy.Tiles.Tile(_item[0]['x'], _item[0]['y'], _item[0]['z'], _item[1], format=self.format) for _item in _temp]
        self._tile_set = ngy.Tiles.Tileset(_temp2)

    def save(self, file, name, meta=None ):
        # See https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
        _format_trans = dict(jpeg="jpg", png="png", pbf="pbf", webp="webp")
        _meta = dict(name=name,
                     format=_format_trans[self.format],
                     bounds=", ".join(str(v) for v in self.bounds),
                     minzoom=min(self.zoom_list),
                     maxzoom=max(self.zoom_list),
                     center=", ".join(str(v) for v in [round((self.bounds[0] + self.bounds[2])/2, 7),
                             round((self.bounds[1] + self.bounds[3])/2, 7),
                             max(self.zoom_list)])
                     )
        if meta is not None:
            _meta = {**_meta, **meta}

        if os.path.isfile(file):
            os.remove(file)
        conn = sqlite3.connect(file)
        c = conn.cursor()
        # Create db structure
        # Create table metadata (need name, format, bounds)
        c.execute('CREATE TABLE metadata (name text, value text)')
        # Create table tiles
        c.execute('CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob)')
        c.execute('CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row)')
        for key, val in _meta.items():
            c.execute('INSERT INTO metadata (name,value) VALUES (?,?)', (key, val))
        for _tile in self._tile_set.get_tiles_list():
            c.execute('INSERT INTO tiles (tile_column , tile_row , zoom_level , tile_data) VALUES (?,?,?,?)',
                      (*_tile.get_TMS_coordinates(), sqlite3.Binary(_tile.get_data())))

        # Save (commit) the changes
        conn.commit()

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()