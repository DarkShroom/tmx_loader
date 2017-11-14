Loads TMX files (yet another tmx loader)... Designed for my personal Love 2D project, to make everything far simpler for easy json conversion.

WARNING, back everything up! The code currently runs a glob on all TMX files, it shouldn't overwrite anything but I don't want to be accused of malware! :)




myTMX = MyTMX('somefile.tmx')

loads object and tile layers only, only for orthogonal (square) maps... the script is designed for my love 2D code


capable of linking to the tile data, to look up a gid (to find it's image and details etc):




So far what's good:

-abstracting the GID, the GID removes the flags, and then you have a GID that links straight to the dictionary that stores ALL the tiles in ALL the tilesets
gid becomes gid_rotation and gid_flip ... this makes it much easier to code in the target enviroment (not having to deal with flags)

-tile objects in the object layer in the TMX format, unfortunatly reference from the bottom left, while the rest of things, like rectangles, polygons etc, reference from the top left.... this is corrected (all things now reference from the top left)

-certain things are just added, like visible = true (even if there was no visible tag, this assists easy interaction in love 2D for example)


Design goals:

-This script is not designed for performance, but for simplicity, it shouldn't be a programmers priority to optimise pointless tasks. The code is for translating TMX to a much easier format to deal with in your target enviroment. Worrying about a couple of extra KB in your output file, in todays modern memory rich enviroment, is in my opinion, not very Python.

Important notes:

-Custom properties, CANNOT be named the same as existing defaults (they will be overwritten)... for example you cannot use a customer property called "height", "width", "type" etc.... This is deliberate, it means the output format is not wholey compatible with TMX, but is simplified for the target enviroment.
