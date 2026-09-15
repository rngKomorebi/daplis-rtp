"""Render the application icon from the master artwork.

The icon is drawn once, large, and lives in 'assets'. Everything the
application and the installer need is rendered from it by this script
into 'src/daplis_rtp/resources', which is the only copy that ships: the
master is a few hundred kilobytes of artwork that no user of the
package has any use for.

Run it after the artwork changes, and commit what it writes - the
release build has no image library available to it and does not render
anything itself:

    pip install pillow
    python tools/make_icons.py

Qt is handed every PNG size rather than one large one because it scales
whatever it is given: a 16 px title-bar icon downscaled on the fly from
the master loses the peak and the bar row to blur, while the same size
resampled here, once, with a proper filter, keeps them. The '.ico' is
what Windows itself reads - the executable, the desktop shortcut, the
Explorer listing - and holds the same set in one file.

"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "assets" / "daplis-rtp-icon.png"
OUT_DIR = ROOT / "src" / "daplis_rtp" / "resources"

# Sizes Qt is given to choose between. 16 is the title bar, 32 the task
# bar, 256 the largest Explorer view; the rest are the steps in between
# that Windows and the Linux desktops actually ask for.
PNG_SIZES = (16, 32, 48, 64, 128, 256)

# The '.ico' carries 24 as well: Windows uses it for small toolbar and
# jump-list entries, and an icon that lacks a size is stretched to it.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def trim(master: Image.Image) -> Image.Image:
    """The artwork without its transparent margin, kept square.

    The master is exported with about five per cent of clear space on
    every side, which is the convention for macOS artwork. Windows
    draws its icons to the edge, so an icon keeping that margin sits
    visibly smaller than everything beside it on the taskbar - the tile
    is rendered at 90 % of the size the neighbouring icons get. The
    margin is cropped here rather than in the artwork, so that a fresh
    export from the same tool needs no hand-editing.
    """
    box = master.getchannel("A").getbbox()
    if box is None:
        return master
    art = master.crop(box)
    side = max(art.size)
    if art.size == (side, side):
        return art
    # Centred in a square, so that art which is not square itself is
    # padded rather than stretched
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(art, ((side - art.width) // 2, (side - art.height) // 2))
    return square


def render(master: Image.Image, size: int) -> Image.Image:
    """The master at 'size', resampled rather than scaled by Qt."""
    return master.resize((size, size), Image.LANCZOS)


def main() -> int:
    if not MASTER.is_file():
        print("No master artwork at {}".format(MASTER), file=sys.stderr)
        return 1

    original = Image.open(MASTER).convert("RGBA")
    master = trim(original)
    print(
        "master {}x{}, artwork {}x{} ({:.0f} % of it), rendering:".format(
            original.width,
            original.height,
            master.width,
            master.height,
            100.0 * master.width / original.width,
        )
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for size in PNG_SIZES:
        path = OUT_DIR / "daplis-rtp-{}.png".format(size)
        render(master, size).save(path, format="PNG", optimize=True)
        print("{:>6} bytes  {}".format(path.stat().st_size, path.name))

    # Pillow would resample these itself, but only from the image it is
    # handed and with a filter of its choosing; rendering them here uses
    # the same path as the PNGs, so the two sets cannot differ.
    frames = [render(master, size) for size in ICO_SIZES]
    ico = OUT_DIR / "daplis-rtp.ico"
    frames[-1].save(
        ico,
        format="ICO",
        sizes=[(size, size) for size in ICO_SIZES],
        append_images=frames[:-1],
    )
    print("{:>6} bytes  {}".format(ico.stat().st_size, ico.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
