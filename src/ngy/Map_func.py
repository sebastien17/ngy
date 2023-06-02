#!/usr/bin/env python
# coding: utf-8

import os
from collections import namedtuple
from lxml import etree
import pyproj

# XML DATA
WMTS_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),"data", "wmts.xml")
_DEF_NS = {"foo": "http://www.opengis.net/wmts/1.0", "ows": "http://www.opengis.net/ows/1.1"}

# Type def
Coord = namedtuple('Coord', ['lon', 'lat'])

# to get more info : https://wxs.ign.fr/an7nvfzojv5wa96dsga5nk8w/geoportail/wmts?Service=WMTS&Request=GetCapabilities
# &Version=1.0.0&Layer=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR.CV


def get_scale_denom_info(file):
    """Return dict with tile matrix set identifier, zoom(scale), scale denom(meters/pixel)"""
    data = {}
    tree = etree.parse(file)

    tile_matrix_sets = tree.xpath('/foo:Capabilities/foo:Contents/foo:TileMatrixSet', namespaces=_DEF_NS)
    for tilematrixset in tile_matrix_sets:
        identifier = tilematrixset.find('ows:Identifier', namespaces=_DEF_NS).text
        supportedcrs = tilematrixset.find('ows:SupportedCRS', namespaces=_DEF_NS).text
        data[identifier] = {}
        data[identifier]['supportedcrs'] = supportedcrs
        TileMatrixes = tilematrixset.findall('foo:TileMatrix', namespaces=_DEF_NS)
        for tilematrix in TileMatrixes:
            scale = tilematrix.find('ows:Identifier', namespaces=_DEF_NS).text
            # Dénominateur d'échelle = résolution / taille pixel ; taille de pixel arbitraire = 0.00028 m
            scale_denom = float(tilematrix.find('foo:ScaleDenominator', namespaces=_DEF_NS).text) * 0.00028
            data[identifier][scale] = scale_denom
            str_ref = tilematrix.find('foo:TopLeftCorner', namespaces=_DEF_NS).text
            (data[identifier]['X_ref'], data[identifier]['Y_ref']) = map(float, str_ref.split(" "))
    return data

# Get all information about tile sets
MATRIX_SET_DATA = get_scale_denom_info(WMTS_FILE_PATH)

def convert_coord(long_lat, matrix_data, zoom, projection):
    """convert decimals coords into Web Mercator coords into tile coords"""
    # See https://geoservices.ign.fr/documentation/geoservices/wmts.html

    #proj_4326 = pyproj.Proj(init='epsg:4326')

    #final_proj = pyproj.Proj(init=matrix_data[projection]['supportedcrs'])

    transformer = pyproj.Transformer.from_crs('EPSG:4326', matrix_data[projection]['supportedcrs'])
    tile_res = matrix_data[projection][str(zoom)] * 256  # 256 pixel per tile

    # Web Mercator
    #(x, y) = pyproj.transform(proj_4326, final_proj, long_lat[0], long_lat[1])
    (x, y) = transformer.transform( long_lat[1], long_lat[0])


    # Get the top left corner
    (x0, y0) = (matrix_data[projection]['X_ref'], matrix_data[projection]['Y_ref'])

    # Tile coords depending on matrix_data (see get_scale_denom_info function)
    (xf, yf) = (int((x - x0) / tile_res), int((y0 - y) / tile_res))
    # ("Zoom: " + str(zoom) + " Tile Rez: " + str(tile_res) + " X,Y: " + str(xf) + "," + str(yf))

    return (xf, yf)