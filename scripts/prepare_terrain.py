"""Refresh the three 6 km terrain extracts from CTX tiles and public elevation products."""
import argparse
import io
import json
import math
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CTX = "https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX1/MapServer"
GALE = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/MSL/MSL_Gale_DEM_Mosaic_1m_v3.tif"
MOLA = "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/"
MOLA_TILES = {"arcadia": (44, 180), "utopia": (88, 90)}
OFFSETS = range(-3000, 3001, 250)


def fetch(url, span=None):
    cmd = ["curl", "--fail", "--silent", "--show-error", "--location", "--retry", "2", "--max-time", "60"]
    if span:
        start, length = span
        cmd.extend(["--range", f"{start}-{start + length - 1}", "--max-filesize", str(length)])
    data = subprocess.check_output([*cmd, url])
    if span and len(data) != length:
        raise ValueError(f"Expected {length} bytes from {url}, received {len(data)}")
    return data


def ctx_image(lat, lon, tile_info):
    level = 12
    step = next(lod["resolution"] for lod in tile_info["lods"] if lod["level"] == level)
    size = tile_info["cols"]
    origin = tile_info["origin"]
    lat_span = math.degrees(3000 / 3396190)
    lon_span = lat_span / math.cos(math.radians(lat))
    lng = (lon + 180) % 360 - 180
    box = ((lng-lon_span-origin["x"])/step, (origin["y"]-lat-lat_span)/step,
           (lng+lon_span-origin["x"])/step, (origin["y"]-lat+lat_span)/step)
    left, top, right, bottom = [math.floor(x / size) for x in box]
    mosaic = Image.new("L", ((right-left+1)*size, (bottom-top+1)*size))

    def tile(pos):
        col, row = pos
        raw = fetch(f"{CTX}/tile/{level}/{row}/{col}")
        with Image.open(io.BytesIO(raw)) as im:
            if im.size != (size, size):
                raise ValueError("Unexpected CTX tile dimensions")
            return pos, im.convert("L")

    with ThreadPoolExecutor(5) as pool:
        positions = [(x, y) for x in range(left, right+1) for y in range(top, bottom+1)]
        for (x, y), image in pool.map(tile, positions):
            mosaic.paste(image, ((x-left)*size, (y-top)*size))
    region = tuple(v - offset*size for v, offset in zip(box, (left, top, left, top)))
    return mosaic.transform((768, 768), Image.Transform.EXTENT, region, Image.Resampling.BICUBIC)


def mola_grid(lat, lon, tile):
    north, west = tile
    url = MOLA + f"megt{north}n{west:03}hb.img"
    rows = [(north-lat+math.degrees(d/3396000))*128-.5 for d in OFFSETS]
    cols = [(lon-west+math.degrees(d/3396000/math.cos(math.radians(lat))))*128-.5 for d in OFFSETS]
    stride = 11520*2  # native columns, 16-bit signed big-endian samples
    first, last = math.floor(rows[0]), math.floor(rows[-1])+1
    raw = fetch(url, (first*stride, (last-first+1)*stride))

    def interpolate(y, x):
        i, j = math.floor(x), math.floor(y)
        fx, fy = x-i, y-j
        value = 0
        for dy, wy in enumerate((1-fy, fy)):
            for dx, wx in enumerate((1-fx, fx)):
                sample = struct.unpack_from(">h", raw, (j+dy-first)*stride+2*(i+dx))[0]
                value += wx*wy*sample
        return round(value)

    return [[interpolate(y, x) for x in cols] for y in rows]


def decode_gale_row(data, width):
    # Give Pillow a one-row TIFF wrapping the original floating-point LZW strip.
    tags = [(256, 4, width), (257, 4, 1), (258, 3, 32), (259, 3, 5), (262, 3, 1),
            (273, 4, 134), (277, 3, 1), (278, 4, 1), (279, 4, len(data)), (339, 3, 3)]
    header = b"II" + struct.pack("<HIH", 42, 8, len(tags))
    entries = b"".join(struct.pack("<HHII", key, kind, 1, val) for key, kind, val in tags)
    return Image.open(io.BytesIO(header + entries + bytes(4) + data))


def gale_grid(lat, lon):
    # Read only the directory, geotransform and required scanlines of the large USGS TIFF.
    header = fetch(GALE, (0, 8))
    if header[:4] != b"II*\0":
        raise ValueError("Expected a little-endian classic TIFF for Gale")
    directory = struct.unpack_from("<I", header, 4)[0]
    count = struct.unpack("<H", fetch(GALE, (directory, 2)))[0]
    entries = fetch(GALE, (directory+2, count*12))
    tags = {key: (kind, n, val) for key, kind, n, val in struct.iter_unpack("<HHII", entries)}
    width = tags[256][2]
    if [tags[k][2] for k in (258, 259, 278, 317, 339)] != [32, 5, 1, 1, 3]:
        raise ValueError("Unexpected encoding in the Gale DEM")

    def tag_values(key, fmt):
        _, n, addr = tags[key]
        return struct.unpack("<" + str(n) + fmt, fetch(GALE, (addr, n*struct.calcsize("<"+fmt))))

    offsets, counts = tag_values(273, "I"), tag_values(279, "I")
    dx, dy, _ = tag_values(33550, "d")
    _, _, _, west, north, _ = tag_values(33922, "d")
    radius = 3396190
    x0, y0 = radius*math.radians(lon)-west, north-radius*math.radians(lat)
    cols = [math.floor((x0+d/math.cos(math.radians(lat)))/dx) for d in OFFSETS]

    def row(d):
        j = math.floor((y0+d)/dy)
        with decode_gale_row(fetch(GALE, (offsets[j], counts[j])), width) as im:
            return [round(im.getpixel((i, 0))) for i in cols]

    with ThreadPoolExecutor(5) as pool:
        return list(pool.map(row, OFFSETS))


def main():
    sites = json.loads((ROOT / "data/sites.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", choices=list(sites))
    parser.add_argument("--layer", choices=["imagery", "elevation", "both"], default="both")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    tiles = None
    if args.layer != "elevation":
        tiles = json.loads(fetch(CTX + "?f=pjson"))["tileInfo"]
    for site in ([args.site] if args.site else sites):
        lat, lon = sites[site]["lat"], sites[site]["lon"]
        if tiles:
            path = args.output_root / "assets/terrain" / (site + ".jpg")
            image = ctx_image(lat, lon, tiles)
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, quality=90)
            print(path, flush=True)
        if args.layer != "imagery":
            grid = gale_grid(lat, lon) if site == "gale" else mola_grid(lat, lon, MOLA_TILES[site])
            path = args.output_root / "data/elevation" / (site + ".json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[\n" + ",\n".join("  "+json.dumps(row, separators=(",", ":")) for row in grid) + "\n]\n", encoding="utf-8")
            print(path, flush=True)


if __name__ == "__main__":
    main()
