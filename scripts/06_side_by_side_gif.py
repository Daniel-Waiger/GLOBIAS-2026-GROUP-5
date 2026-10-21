"""Step 6: side-by-side GIF of the tracking results of ilastik 1.3.3post3 (left) and 1.5.0a3 (right).

Both runs number their lineages identically (checked in 05_compare_versions.py), so the same lineage id
gets the same colour in both panels. Places where the label of any pixel differs between the two runs
are circled in magenta in both panels; the header gives the number of differing pixels in that frame.

usage: python 06_side_by_side_gif.py   -> results/side_by_side_tracking.gif
"""
from pathlib import Path

import h5py
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from overlay import MAGENTA, contrast_limits, gif_palette, lineage_colours, overlay, to_gif_frame

NAME = "mitocheck_94570_2D+t_01-53-volume-data_Tracking-Result.h5"
RUNS = ["1.3.3post3", "1.5.0a3"]
SCALE = 0.5          # display size relative to the 1344 x 1024 original
HEADER = 34          # pixels of title bar above the panels
GAP = 8              # pixels between the panels

raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
tracks = [h5py.File(f"results/ilastik-{v}/03_tracking/{NAME}", "r")["exported_data"] for v in RUNS]

colours = lineage_colours(int(max(t[:].max() for t in tracks)))
palette = gif_palette(colours)
lo, hi = contrast_limits(raw)
font = ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"), 16)
w, h = int(raw.shape[1] * SCALE), int(raw.shape[2] * SCALE)

frames = []
for t in range(raw.shape[0]):
    gray = np.clip((raw[t, ..., 0].T - lo) / (hi - lo), 0, 1)
    labels = [np.asarray(tr[t, ..., 0]).T for tr in tracks]
    diff = labels[0] != labels[1]
    # Group differing pixels that lie close together (within ~5 px) into one spot to circle.
    spots, n_spots = ndimage.label(ndimage.binary_dilation(diff, iterations=5))
    centres = ndimage.center_of_mass(diff, spots, range(1, n_spots + 1))

    canvas = Image.new("RGB", (2 * w + GAP, h + HEADER), "black")
    draw = ImageDraw.Draw(canvas)
    for i, (version, lab) in enumerate(zip(RUNS, labels)):
        x0 = i * (w + GAP)
        canvas.paste(overlay(gray, lab, colours, (w, h)), (x0, HEADER))
        draw.text((x0 + 6, 8), f"ilastik {version}", fill="white", font=font)
        for cy, cx in centres:
            px, py = x0 + cx * SCALE, HEADER + cy * SCALE
            draw.ellipse((px - 14, py - 14, px + 14, py + 14), outline=MAGENTA, width=2)
    note = f"frame {t:2d}   {int(diff.sum())} px differ"
    draw.text((2 * w + GAP - draw.textlength(note, font=font) - 6, 8), note, fill=MAGENTA, font=font)
    frames.append(to_gif_frame(canvas, palette))

out = Path("results/side_by_side_tracking.gif")
frames[0].save(out, save_all=True, append_images=frames[1:], duration=250, loop=0)
print(out, f"{out.stat().st_size / 1e6:.1f} MB")
