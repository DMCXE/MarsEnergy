"""Compose the two atlas maps from the three local Solar System Scope originals."""
import argparse
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def resize(path):
    with Image.open(path) as image:
        return image.convert("RGB").resize((1024, 512), Image.Resampling.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ASSETS / "originals" / "planets")
    parser.add_argument("--output", type=Path, default=ASSETS / "planets")
    args = parser.parse_args()
    day = resize(args.source / "earth-day.jpg")
    cloud_mask = resize(args.source / "earth-clouds.jpg").convert("L").point(lambda x: min(246, int(.98 * x)))
    earth = Image.composite(Image.new("RGB", day.size, (244, 246, 247)), day, cloud_mask)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, image in (("earth", earth), ("mars", resize(args.source / "mars.jpg"))):
        image.save(args.output / (name + ".jpg"), quality=86, optimize=True)


if __name__ == "__main__":
    main()
