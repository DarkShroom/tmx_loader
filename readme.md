TMX Loading Object



Loads TMX in a simple object format, a much simpler format than other TMX loaders.

Design Goals are simplicity and usability over performance. It's still a fraction of a second it seems to take to process my whole forlder of maps.



-Simplifys certain aspects of the format, for example, custom properties are alongside default ones.
-GIDs have their flags removed to get easy access to Rotation and Flip
-Coordinate contradictions are dealt with, like objects/rectangles (rotations can still be wrong here)
-Tilesets are mereged to a lookup dictionary
-Many properties are converted to correct types, like int, float, bool etc


Currently one big file, set up to glob the whole folder and turn all
filename.tmx => filename.tmx.json