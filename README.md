## HiRISE

Convert HiRISE Digital Terrain Models (DTM) to 3D meshes (.stl) and normal maps for display in OpenGL.

http://www.uahirise.org/dtm/

### Dependencies

    brew install gdal
    pip install Pillow numpy

### Usage

    python main.py INPUT.IMG

Outputs a .stl mesh and a normal map .png.
