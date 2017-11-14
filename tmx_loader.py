'''

todo:
xml load in object layers (like tile layer)
remove debug prints


Loads a Tiled map file (tmx) and linked tilesets (tsx) into an easy to use Python object

Translates GID to tile information, supports multiple tilesets

Uses XML parser, not a TMX lib


Issues:

-Absolute paths? unsure

-Custom properties cannot be the same as keywords like:
    image_source
    image_width
    image_height
    type
    is
This is by design, it makes it easier to access custom properties and has a simpler object model

-Supports future and unknown tags by setting class objects using setattr, but this means some python functions get overshadowed, like "id" and "type"
    This makes things simpler, and does not affect usage scenarios

- Embedded tilesets unsupported


'''
from __future__ import absolute_import, division, print_function  # , unicode_literals # CAUSES CSV BUG

import os  # TODO
import xml.etree.ElementTree as ET
import json
from pprint import pprint


class GID():
    '''
    My GID translation object
    splits the actual ID from the GID (removes flip flag)
    represents the flags as a rotation (0-3) and flip (0-1) instead of the confusing tiled way (flip hor, flip vert, flip diagonal)
    '''

    # easy translations of flags to 4 rotations (0-3) and 2 flip states (0-1)
    trans_dict = {'010': (2, 1), '011': (3, 0), '001': (3, 1), '000': (0, 0), '111': (1, 1), '110': (2, 0), '100': (0, 1), '101': (1, 0)}

    def __init__(self, gid):
        self.gid = gid
        self.bin_s = format(self.gid, '032b')
        self.id = self.bin_s[3:]
        self.id = int(self.id, 2)
        self.flags = self.bin_s[0:3]
        translation = self.trans_dict[self.flags]  # translation as a tuple of (rotation(0-3),flip(0-1))
        self.rotation = translation[0]
        self.flip = translation[1]

    def get_tuple(self):
        return (self.id, self.rotation, self.flip)

    def __repr__(self):
        return 'GID({},{},{})'.format(self.id, self.rotation, self.flip)


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
    '''
    todo add the init
    '''
    gid = None
    id = None
    x = None
    y = None
    width = None
    height = None
    visible = None

    def __repr__(self):
        s = 'ObjectLayerObject('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s

    def __init__(self, xml_element):

        self.object_type = None  # is used to identify what type of object this is
        # rectangle
        # ellipse
        # polygon
        # polyline
        # tile
        # text

        for child in xml_element:  # custom properties first so they are overridden in conflicts with default ones
            if child.tag == 'properties':
                for child2 in child:
                    name = child2.attrib['name']
                    value = child2.attrib['value']

                    # correct the custom property from string to the actual type
                    type_ = child2.attrib['type']
                    if type_ == 'int':
                        value = int(value)
                    if type_ == 'float':
                        value = float(value)
                    if type_ == 'bool':  # the tmx format has a string here true|false
                        if value == 'true':
                            value = True
                        elif value == 'false':
                            value = False

                    setattr(self, name, value)

            elif child.tag == 'ellipse':
                self.object_type = 'ellipse'

            elif child.tag == 'polyline':
                self.polyline_points = []
                for coor in child.attrib['points'].split(' '):  # turn the points string to arrays of floats
                    coor = coor.split(',')
                    coor = [float(i) for i in coor]
                    self.polyline_points.append(coor)
                self.object_type = 'polyline'

            elif child.tag == 'text':
                self.object_type = 'text'

            elif child.tag == 'polygon':
                self.polygon_points = []
                for coor in child.attrib['points'].split(' '):  # turn the points string to arrays of floats
                    coor = coor.split(',')
                    coor = [float(i) for i in coor]
                    self.polygon_points.append(coor)
                    self.object_type = 'polygon'

        if self.object_type is None:  # if we found no object_type so far, we must be a rectangle or a tile
            if 'gid' in xml_element.attrib:  # a gid means tile
                self.object_type = 'tile'
            else:
                self.object_type = 'rectangle'

        for key in xml_element.attrib:
            setattr(self, key, xml_element.attrib[key])
            if key == 'gid':  # convert the GID
                gid_ob = GID(int(self.gid))
                self.gid_rotation = gid_ob.rotation
                self.gid_flip = gid_ob.flip
                self.gid = gid_ob.id
                self.gid_tuple = gid_ob.get_tuple()

        # attaempt to convert any found values from strings to the actual types
        try:  # x => float
            self.x = float(self.x)
        except Exception as e:
            pass

        try:  # y => float
            self.y = float(self.y)
        except Exception as e:
            pass

        try:  # width => float
            self.width = float(self.width)
        except Exception as e:
            pass

        try:  # height => float
            self.height = float(self.height)
        except Exception as e:
            pass

        try:  # rotation => float
            self.rotation = float(self.rotation)
        except Exception as e:
            pass

        try:  # id => int
            self.id = int(self.id)
        except Exception as e:
            pass

        if self.visible == '0':  # if we have a visible tag as 0 make false
            self.visible = False
        else:
            self.visible = True

        if self.object_type == 'tile':
            # if we have detected a tile, we need this odd hack to ensure it lines up with top-left origins
            # unfortunatly in the tiled format there is this contradiction
            self.y = self.y - self.height


class ObjectLayer():

    name = None
    visible = None
    objects = None  # list of ObjectLayerObject()

    def __str__(self):
        s = ''
        s += '\n'.join("%s: %s" % item for item in vars(self).items())
        return s

    def __init__(self, xml_element):
        self.objects = []

        for key in xml_element.attrib:
            setattr(self, key, xml_element.attrib[key])

        for child in xml_element:
            if child.tag == 'object':
                objectLayerObject = ObjectLayerObject(child)
                self.objects.append(objectLayerObject)

        # try:
        if self.visible == '0':
            self.visible = False
        else:
            self.visible = True
        # except Exception as e:
        #     print(type(e), e)


class TileSetTile():
    '''
    represents a tile in a tileset
    '''
    id = None  # ID
    type = None  # Type
    image_source = None  # Image
    image_width = None  # Width
    image_height = None  # Height
    probability = None

    def show_image(self):
        '''
        display image, requires PIL
        '''
        from PIL import Image
        Image.open(self.image_source).show()

    def __str__(self):
        s = 'TileSetTile('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s

    def __init__(self, xml_element):
        '''
        reads pars from the tile
        writes the custom properties directly to this object
        '''
        for child in xml_element:  # custom properties are iterated first, this means conflicts will be overwritten
            if child.tag == 'properties':  # found custom properties tag
                for child2 in child:
                    if child2.tag == 'property':  # found a custom property

                        name = child2.attrib['name']
                        value = child2.attrib['value']

                        try:
                            type_ = child2.attrib['type']  # if we have a type try to convert the varible
                            if type_ == 'int':
                                value = int(value)
                            if type_ == 'float':
                                value = float(value)
                            if type_ == 'bool':
                                value = bool(value)

                        except Exception as e:
                            # print(type(e), e)
                            pass

                        setattr(self, name, value)

        for key in xml_element.attrib:  # set all the normal attribs
            setattr(self, key, xml_element.attrib[key])

        for child in xml_element:
            if child.tag == 'image':  # for image tag, make properties of the attributes of the image tag like source => image_source
                for key in child.attrib:
                    setattr(self, child.tag + '_' + key, child.attrib[key])

        # try to convert values from the strings in the tmx
        try:
            self.id = int(self.id)
        except Exception as e:
            # print(type(e), e)
            pass
        try:
            self.image_width = int(self.image_width)
        except Exception as e:
            # print(type(e), e)
            pass
        try:
            self.image_height = int(self.image_height)
        except Exception as e:
            # print(type(e), e)
            pass


class TileSet():
    '''
    loads a TSX file
    '''

    firstgid = None
    source = None
    tiles = None  # list of TileSetTile()

    def __str__(self):
        # s = ''
        # s += '\n'.join("%s: %s" % item for item in vars(self).items())
        # return s

        s = 'TileSet('
        s += ', '.join("%s: %s" % item for item in vars(self).items())
        s += ')'
        return s

    # def load_from_tsx(self, filename):
    def __init__(self, filename):

        self.tiles = []

        with open(filename) as file:
            # print('#tileset#' * 4)
            # print (file)

            s = file.read()
            # print(s)
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

    tilesets = None
    tile_layers = None
    object_layers = None

    gid_to_tile_dict = None

    def refresh_gid_to_tile_dict(self):
        '''
        creates a dict of all the keys in the map translated to tile
        '''
        self.gid_to_tile_dict = {}
        for tileset in self.tilesets:
            for tile in tileset.tiles:
                actual_gid = tile.id + tileset.firstgid
                self.gid_to_tile_dict[actual_gid] = tile

        pass

    def gid_to_tile(self, gid):
        '''
        seems to fuck up when the tiles are deleted?
        '''
        if self.gid_to_tile_dict is None:
            self.refresh_gid_to_tile_dict()
            # self.gid_to_tile_dict = {}
            # for tileset in self.tilesets:
            #     for tile in tileset.tiles:
            #         actual_gid = tile.id + tileset.firstgid
            #         self.gid_to_tile_dict[actual_gid] = tile

        return self.gid_to_tile_dict[gid]

    def __init__(self, filename):

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
        self.tile_layers = []
        self.object_layers = []

        with open(filename) as file:
            s = file.read()

            root = ET.fromstring(s)  # load xml from string

            for child in root:

                if child.tag == 'tileset':  # found a tileset
                    # print ('tileset:', child.attrib)

                    tileset_filename = child.attrib['source']  # TODO: WARNING RELATIVE PATH

                    # print('', child.attrib)
                    tileset = TileSet(tileset_filename)  # create a tileset
                    for key in child.attrib:  # add all the keys
                        setattr(tileset, key, child.attrib[key])

                    tileset.firstgid = int(tileset.firstgid)

                    self.tilesets.append(tileset)

                if child.tag == 'layer':  # find all layers TODO: translate to thing

                    layer = TileLayer()  # create new layer
                    for key in child.attrib:
                        setattr(layer, key, child.attrib[key])

                    layer.width = int(layer.width)
                    layer.height = int(layer.height)
                    try:
                        layer.visible = bool(layer.visible)
                    except Exception as e:
                        print(type(e), e)

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
                                map_array_row_tuples = []  # no longer tuples
                                for val in line:
                                    val = int(val)  # string to int for gid table

                                    gid = 0  # empty tiles will be None
                                    if val != 0:
                                        gid = GID(val).get_tuple()
                                        # tuple_val = gid  # converts the gid to a split tuple (id,rotation,flip)

                                    map_array_row.append(val)
                                    map_array_row_tuples.append(gid)  # save with rotation and flip

                                map_array.append(map_array_row)
                                map_array_tuples.append(map_array_row_tuples)

                            layer_old['data'] = map_array_tuples
                            layer.data = map_array_tuples

                    self.tile_layers.append(layer)

                if child.tag == 'objectgroup':

                    objectgroup = ObjectLayer(child)

                    ''' OLD
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

                    '''
                    self.object_layers.append(objectgroup)

        self.refresh_gid_to_tile_dict()

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

    def json_file_format1(self):
        '''
        just the first layers

        dict with keys as:
        map (2D array of (key, rotation, flip))
        tiles (dict of dicts with tile info)
        objects (list of objects as dicts)
        '''

        d = {}

        tile_layer = self.tile_layers[0]

        gidmap = tile_layer.data

        keymap = []
        for y in gidmap:
            row = []
            for x in y:
                # tile = None
                tile = {}
                if x is not 0 or None:
                    # tile = x.get_tuple()
                    tile = {}
                    tile['id'] = x[0]
                    tile['rotation'] = x[1]
                    tile['flip'] = x[2]
                if tile is None:
                    tile = 0
                row.append(tile)
            keymap.append(row)
        d['map'] = keymap

        tiledict = {}
        for key in self.gid_to_tile_dict:
            tiledict[key] = vars(self.gid_to_tile_dict[key])
        d['tiles'] = tiledict

        objects = self.object_layers[0].objects
        oblist = []
        for ob in objects:
            oblist.append(vars(ob))
        d['objects'] = oblist

        # print(vars(tile_layer))

        return d

    def json_file_format2(self):

        print(vars(self))

        d = {}

        tile_layers = []
        for layer in self.tile_layers:
            # # method one, manual
            # tile_layer = {}
            # tile_layer['name'] = layer.name
            # tile_layer['width'] = layer.width
            # tile_layer['height'] = layer.height
            # tile_layer['visible'] = layer.visible
            # # tile_layer['data'] = layer.data
            # tile_layers.append(tile_layer)

            # method two, just add the vars dict, as our map is just tuples now
            vars_dict = vars(layer)
            print(vars_dict)
            tile_layers.append(vars_dict)

        d['tile_layers'] = tile_layers

        object_layers = []
        for object_layer in self.object_layers:
            print('json_file_format2', object_layer.name)
            object_layer_vars = vars(object_layer)

            object_dicts = []  # the object list would not be json compatible due to "ObjectLayerObject"
            for ob in object_layer.objects:
                object_dicts.append(vars(ob))
            object_layer_vars['objects'] = object_dicts

            object_layers.append(object_layer_vars)
        d['object_layers'] = object_layers

        tiledict = {}
        for key in self.gid_to_tile_dict:
            tiledict[key] = vars(self.gid_to_tile_dict[key])
        d['tiles'] = tiledict

        # print (d)
        # return(vars(self))

        return d


def write_json_file(filename, data):
    with open(filename, 'w') as json_file:
        json_file.write(json.dumps(data, indent=4))
        # json_file.write(json.dumps(data))


def test1():

    filename = 'TestGID.tmx'
    myTMX = MyTMX(filename)

    # print(myTMX)
    # # image_name = myTMX.get_image_name(98)

    #     # print ('SSS', tileset_dict[6])

    # print('SSS', myTMX.gid_to_tile(1))
    # print('SSS', myTMX.gid_to_tile(162))
    # print('gid_to_tile', myTMX.gid_to_tile(163))
    # myTMX.gid_to_tile(162).show_image()

    gidMap = myTMX.layers[0].data
    # print(gidMap)

    image_list = []

    for y in gidMap:
        row = ''
        for x in y:
            # row += str(x) + ', '

            if x is not None:
                row += '{}'.format(str(x.id))

                gid_to_tile = myTMX.gid_to_tile(x.id)

                print (gid_to_tile)
            row += ','
        print (row)
    print('%' * 8)
    print()

    print ('compmap:')
    compmap = []
    for y in gidMap:
        row = []
        for x in y:
            # row.append(x)
            tile = None
            if x is not None:
                tile = myTMX.gid_to_tile(x.id)
                tile = vars(tile)
            row.append(tile)
        compmap.append(row)
    for y in compmap:
        print (y)
    write_json_file(filename + '.compmap.json', compmap)
    print()

    print ('keymap:')
    keymap = []
    for y in gidMap:
        row = []
        for x in y:
            tile = None
            if x is not None:
                tile = x.get_tuple()
            row.append(tile)
        keymap.append(row)
    for y in keymap:
        print (y)
    print()

    for key in myTMX.gid_to_tile_dict:
        print (key, myTMX.gid_to_tile_dict[key])

    print()

    print('object layer:')
    objectlayer = myTMX.objectgroups[0]
    print(vars(objectlayer))
    for ob in objectlayer.objects:
        print (ob)

    # for tileset in myTMX.tilesets:
    #     print (tileset)
    #     for tile in tileset.tiles:
    #         print (tile)

        # print (row)
# test1()


def batchProcessAllTMX():

    # filename = 'ObjectMap1.tmx'
    # myTMX = MyTMX(filename)
    # write_json_file(filename + '.format1.json', myTMX.json_file_format1())
    # write_json_file(filename + '.format2.json', myTMX.json_file_format2())

    from glob import glob

    for filename in glob('*.tmx'):
        print('found file {}'.format(filename))
        myTMX = MyTMX(filename)
        write_json_file(filename + '.format2.json', myTMX.json_file_format2())


batchProcessAllTMX()

'''
old_print = print
def print(*args, **kwargs):
    old_print('overshadowed print:',*args, **kwargs)
print('sss', 'gsgsgs')
'''


'''
print (json.dumps({'hello': 'balls', 11 : 'some num'}))

class JSONCompatClass:


    def __init__(self):
        self.x = 44
        self.s = 'sshshs'

    def __repr__(self):
        return str(vars(self))

    pass

jsonCompatClass = JSONCompatClass()

print (json.dumps(jsonCompatClass)) #does not work

'''

print(bool('false'))
