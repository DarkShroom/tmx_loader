Loads TMX files


myTMX = MyTMX('somefile.tmx')

loads all the data in the tmx file, translating the flags to the format of (GID, rotation, flip)... which makes things easier

loads object and tile layers only


capable of linking to the tile data, to look up a gid (to find it's image and details etc):

myTMX.gid_to_tile(gid) #gid does not include rotation


Currently experimental, but reflects all the linked data, just needs refactoring
