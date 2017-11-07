'''

Loads a TMX file


MyTMX loads a file


currently has a stratagy for loading linked tilesets

needs more XML purity, should accept XML elements into some of the objects, allowing better organisation


can't work out how to support shapes like rect/elipse, they just lack gid??



'''
from __future__ import absolute_import, division, print_function  # , unicode_literals # CAUSES CSV BUG

import pytmx  # pip install pytmx
import sys
import os
import glob
import csv
import json


from ppretty import ppretty

# from pprint import pprint
import xml.etree.ElementTree as ET


# from collections import OrderedDict


class GID():
    '''
    My GID translation object
    splits the actual ID from the GID (removes flip flag)
    represents the flags as a rotation (0-3) and flip (0-1) instead of the confusing tiled way (flip hor, flip vert, flip diagonal)
    '''

    # trans_dict = OrderedDict([('000', (0, 0)), ('101', (1, 0)), ('110', (2, 0)), ('011', (3, 0)), ('100', (0, 1)), ('111', (1, 1)), ('010', (2, 1)), ('001', (3, 1))])
    trans_dict = {'010': (2, 1), '011': (3, 0), '001': (3, 1), '000': (0, 0), '111': (1, 1), '110': (2, 0), '100': (0, 1), '101': (1, 0)}

    def __init__(self, i):
        self.i = i
        self.bin_s = format(self.i, '032b')
        self.id = self.bin_s[3:]
        self.id = int(self.id, 2)
        self.flags = self.bin_s[0:3]
        translation = self.trans_dict[self.flags]  # translation as a tuple of (rotation(0-3),flip(0-1))
        self.rotation = translation[0]
        self.flip = translation[1]

    def get_tuple(self):
        return (self.id, self.rotation, self.flip)


class TileLayer():
    name = None
    width = None
    height = None
    data = None

    def __str__(self):
        s = ''
        s += '\n'.join("%s: %s" % item for item in vars(self).items())
        return s

# object layer


class ObjectLayerObject():
    gid = None
    id = None
    x = None
    y = None
    width = None
    height = None

    def __str__(self):
        s = 'ObjectLayerObject('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s


class ObjectLayer():
    name = None
    objects = []  # list of ObjectLayerObject()

    def __str__(self):
        s = ''
        s += '\n'.join("%s: %s" % item for item in vars(self).items())
        return s


class TileSetTile():
    '''
    represents a tile in a tileset
    '''
    id = None  # warning overrides built in function (but it is easier this way)
    type = None

    # custom_properties = []

    def __str__(self):
        s = 'TileSetTile('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s

    def __init__(self, xml_element):

        for key in xml_element.attrib:
            setattr(self, key, xml_element.attrib[key])

        self.id = int(self.id)  # id must be int

        for child in xml_element:
            if child.tag == 'image':  # for image tag, make properties of the attributes of the image tag like source => image_source
                for key in child.attrib:
                    # print (key)
                    setattr(self, child.tag + '_' + key, child.attrib[key])

        # print(vars(self))

        # print(self)


class TileSet():
    '''
    loads a TSX file
    '''

    firstgid = None
    source = None
    tiles = []  # list of TileSetTile()

    def __str__(self):
        # s = ''
        # s += '\n'.join("%s: %s" % item for item in vars(self).items())
        # return s

        s = 'TileSet('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s

    def load_from_tsx(self, filename):

        with open(filename) as file:
            # print('#tileset#' * 4)
            # print (file)

            s = file.read()
            print(s)
            # print('#tileset#' * 4)

            root = ET.fromstring(s)  # load xml from string

            for child in root:
                # print(child.tag)

                if child.tag == 'grid':
                    # print(child.attrib)
                    pass

                if child.tag == 'tile':
                    tilsettile = TileSetTile(child)  # accepts xml element
                    self.tiles.append(tilsettile)


class MyTMX():

    debug = False

    tilesets = []
    layers = []
    objectgroups = []


    

    gid_to_tile_dict = None
    def gid_to_tile(self, gid):
        if self.gid_to_tile_dict is None:
            self.gid_to_tile_dict = {}
            for tileset in self.tilesets:
                for tile in tileset.tiles:
                    actual_gid = tile.id + tileset.firstgid
                    self.gid_to_tile_dict[actual_gid] = tile
        return self.gid_to_tile_dict[gid]



    def __init__(self, filename):
        self.load(filename)

    def load(self, filename):

        self.filename = filename

        dirname = os.path.dirname(filename)

        '''
        iterates through tmx file, finding:
        -tile layers
        -object layers

        currently no
        -image layers
        -group layers
        '''
        self.tilesets = []
        self.layers = []
        self.objectgroups = []

        with open(filename) as file:
            s = file.read()

            # print(s)
            # print('filename:',filename)
            # print ('dirname:',dirname)

            root = ET.fromstring(s)  # load xml from string

            for child in root:

                if child.tag == 'tileset':  # found a tileset
                    # print ('tileset:', child.attrib)
                    tileset = TileSet()  # create a tileset
                    for key in child.attrib:  # add all the keys
                        setattr(tileset, key, child.attrib[key])

                    tileset.firstgid = int(tileset.firstgid)

                    tileset_filename = child.attrib['source']  # TODO: WARNING RELATIVE PATH
                    tileset.load_from_tsx(tileset_filename)

                    self.tilesets.append(tileset)

                if child.tag == 'layer':  # find all layers
                    if self.debug:
                        print ('layer:', child.attrib)

                    layer = TileLayer()  # create new layer
                    for key in child.attrib:
                        setattr(layer, key, child.attrib[key])

                    layer_old = {}
                    layer_old.update(child.attrib)

                    for child2 in child:
                        if child2.tag == 'data':  # the csv is here
                            csv_lines = child2.text.strip().splitlines()  # strip and split into lines

                            map_array = []  # 2D arrays
                            map_array_tuples = []

                            for line in csv_lines:
                                line = line.strip(',').split(',')  # strip ending commas, split into vals
                                map_array_row = []
                                map_array_row_tuples = []
                                for val in line:
                                    val = int(val)  # string to int for gid table

                                    tuple_val = None  # empty tiles will be None
                                    if val != 0:
                                        gid = GID(val)
                                        tuple_val = gid.get_tuple()  # converts the gid to a split tuple (id,rotation,flip)

                                    map_array_row.append(val)
                                    map_array_row_tuples.append(tuple_val)  # save with rotation and flip

                                map_array.append(map_array_row)
                                map_array_tuples.append(map_array_row_tuples)

                            if self.debug:
                                for row in map_array_tuples:
                                    print (row)
                                print('#' * 16)

                            layer_old['data'] = map_array_tuples
                            layer.data = map_array_tuples

                    self.layers.append(layer)

                if child.tag == 'objectgroup':
                    if self.debug:
                        print ('objectgroup:', child.attrib)

                    objectgroup = ObjectLayer()
                    for key in child.attrib:
                        setattr(objectgroup, key, child.attrib[key])

                    objectgroup.objects = []

                    for child2 in child:
                        if child2.tag == 'object':
                            if self.debug:
                                print('object:', child2.attrib)
                            objectLayerObject = ObjectLayerObject()
                            for key in child2.attrib:

                                setattr(objectLayerObject, key, child2.attrib[key])
                                if key == 'gid':
                                    objectLayerObject.gid = GID(int(objectLayerObject.gid)).get_tuple()

                            objectgroup.objects.append(objectLayerObject)

                    if self.debug:
                        print (objectgroup)
                    self.objectgroups.append(objectgroup)

    def get_image_name(self, gid):

        print ('get_image_name', gid)

        for tileset in self.tilesets:
            # print (tileset.source , '::')
            # print ('--' , tileset)

            for tile in tileset.tiles:
                # print(tile)

                pass

        pass

    def __str__(self):
        s = ''
        s += 'tmx file: {}\n'.format(self.filename)
        # s = 'tile layers:\n'
        s += '\n'
        for layer in self.layers:
            s += 'layer: {}\n'.format(layer.name)
            s += str(layer) + '\n'
            s += '#' * 8 + '\n'

        # s += 'object layers:\n'
        for object_layer in self.objectgroups:
            # s += object_layer.name + '\n'
            s += str(object_layer) + '\n'
            s += '#' * 8 + '\n'

        return s


def test1():
    myTMX = MyTMX('map_rotate_test.tmx')
    print('&%^*' * 16)

    print(myTMX)
    # image_name = myTMX.get_image_name(98)


        # print ('SSS', tileset_dict[6])

    print('SSS', myTMX.gid_to_tile(1))
    print('SSS', myTMX.gid_to_tile(162))
    print('SSS', myTMX.gid_to_tile(164))

    


test1()
