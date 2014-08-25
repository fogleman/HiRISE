from PIL import Image
import numpy as np
import gdal
import gdalconst
import struct
import sys

ALTITUDE_MULTIPLIER = 1
MESH_STEP = 8
NORMAL_STEP = 2

def compute_mesh(data, step):
    print 'compute_mesh'
    h = ALTITUDE_MULTIPLIER
    positions = []
    data = data[::step, ::step]
    rows, cols = data.shape
    for i0 in xrange(rows - 1):
        for j0 in xrange(cols - 1):
            i1 = i0 + 1
            j1 = j0 + 1
            y00 = data[i0][j0]
            y01 = data[i0][j1]
            y10 = data[i1][j0]
            y11 = data[i1][j1]
            x0, x1 = i0 * step, i1 * step
            z0, z1 = j0 * step, j1 * step
            if not any(np.isnan(y) for y in [y01, y10, y00]):
                positions.append((x0, y01 * h, z1))
                positions.append((x1, y10 * h, z0))
                positions.append((x0, y00 * h, z0))
            if not any(np.isnan(y) for y in [y11, y10, y01]):
                positions.append((x1, y11 * h, z1))
                positions.append((x1, y10 * h, z0))
                positions.append((x0, y01 * h, z1))
    print len(positions) / 3
    return positions

def compute_normals(data, step):
    print 'compute_normals'
    deltas = []
    data = data[::step, ::step]
    for dz in xrange(-1, 2):
        for dx in xrange(-1, 2):
            print dz, dx
            d = data
            d = np.roll(d, -dz, axis=0)
            d = np.roll(d, -dx, axis=1)
            d = d - data
            d = np.expand_dims(d, 2)
            d = np.insert(d, 0, -dz * step, axis=2)
            d = np.insert(d, 0, -dx * step, axis=2)
            deltas.append(d)
    edges = [0, 1, 2, 5, 8, 7, 6, 3, 0]
    normals = []
    for a, b in zip(edges, edges[1:]):
        print a, b
        cross = np.cross(deltas[b], deltas[a])
        normal = cross / np.sqrt((cross ** 2).sum(-1))[..., np.newaxis]
        normals.append(normal)
    normals = sum(normals) / len(normals)
    return normals

def load(path):
    print 'load'
    image = gdal.Open(path, gdalconst.GA_ReadOnly)
    data = image.ReadAsArray()
    data[data < -1e9] = np.nan
    print data.shape
    return data

def normal_from_points(a, b, c):
    x1, y1, z1 = a
    x2, y2, z2 = b
    x3, y3, z3 = c
    ab = (x2 - x1, y2 - y1, z2 - z1)
    ac = (x3 - x1, y3 - y1, z3 - z1)
    x = ab[1] * ac[2] - ab[2] * ac[1]
    y = ab[2] * ac[0] - ab[0] * ac[2]
    z = ab[0] * ac[1] - ab[1] * ac[0]
    d = (x * x + y * y + z * z) ** 0.5
    return (x / d, y / d, z / d)

def save_binary_stl(positions, path):
    print 'save_binary_stl'
    p = positions
    data = []
    data.append('\x00' * 80)
    data.append(struct.pack('<I', len(p) / 3))
    for vertices in zip(p[::3], p[1::3], p[2::3]):
        data.append(struct.pack('<fff', *normal_from_points(*vertices)))
        for vertex in vertices:
            data.append(struct.pack('<fff', *vertex))
        data.append(struct.pack('<H', 0))
    data = ''.join(data)
    with open(path, 'wb') as fp:
        fp.write(data)

def save_normal_map(data, path):
    print 'save_normal_map'
    data = (-data + 1.0) / 2.0
    scaled = (255.0 * data).astype(np.uint8)
    im = Image.fromarray(scaled)
    im.save(path)

def main():
    data = load(sys.argv[1])
    if MESH_STEP:
        positions = compute_mesh(data, MESH_STEP)
        save_binary_stl(positions, 'output.stl')
    if NORMAL_STEP:
        normals = compute_normals(data, NORMAL_STEP)
        save_normal_map(normals, 'output.png')

if __name__ == '__main__':
    main()
