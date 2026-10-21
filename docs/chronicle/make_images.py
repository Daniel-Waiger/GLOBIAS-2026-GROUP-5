"""Build the images for docs/chronicle (run from the repo root with ilastik 1.5's python).

1. screens/*.txt -> img/<name>.png: terminal-style renderings of verbatim log/terminal excerpts.
   Line 1 of each .txt is the title, line 2 the source; '[…]' marks lines left out; lines starting with
   'fix:', 'note:', '->', 'before:' or 'added:' are annotations for the reader and are drawn in blue.
   These are renderings of real output, not screen captures of the session.
2. img/axis_trap.png: where the 2014 label blocks land when read as t,x,y (as saved) vs t,y,x (ilastik 1.5).
3. img/difference_zoom.png: the frame where the 1.3.3post3 and 1.5.0a3 tracking labels differ most, zoomed.
"""
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import sys
sys.path.insert(0, "scripts")
from overlay import MAGENTA, contrast_limits, lineage_colours, overlay  # noqa: E402

HERE = Path(__file__).parent
IMG = HERE / "img"
IMG.mkdir(exist_ok=True)
FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
MONO = ImageFont.truetype(str(FONTS / "DejaVuSansMono.ttf"), 15)
SANS = ImageFont.truetype(str(FONTS / "DejaVuSans.ttf"), 15)

BG, BAR, FG, DIM = (24, 26, 31), (46, 49, 57), (215, 218, 224), (128, 134, 146)
GREEN, RED, YELLOW, BLUE = (126, 211, 132), (255, 123, 114), (235, 200, 110), (120, 170, 255)
ANNOTATION = ("fix:", "note:", "->", "before:", "added:")
WRAP = 128  # characters per rendered line


def line_colour(line):
    s = line.strip()
    if s.startswith("$"):
        return GREEN
    if s == "[…]":
        return DIM
    if any(k in line for k in ("Error", "ERROR", "error ", "critical", "404", "Rois do not")):
        return RED
    if s.startswith(ANNOTATION):
        return BLUE
    if "Completed Batch" in line:
        return YELLOW
    return FG


def render_screen(txt):
    lines = txt.read_text().splitlines()
    title, source, body = lines[0].lstrip("# "), lines[1].lstrip("# "), lines[2:]
    if any(l.strip().startswith(ANNOTATION) for l in body):
        source += "   ·   blue = annotation added for this document, not program output"
    wrapped = []
    for line in body:
        while len(line) > WRAP:
            wrapped.append(line[:WRAP])
            line = "    " + line[WRAP:]
        wrapped.append(line)
    cw, lh, pad, bar = MONO.getlength("M"), 20, 18, 34
    width = int(max(cw * max(len(l) for l in wrapped), SANS.getlength(title) + 90, SANS.getlength(source)) + 2 * pad)
    height = bar + pad + lh * len(wrapped) + pad + 26
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, width, bar), fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((14 + 20 * i, 11, 26 + 20 * i, 23), fill=c)
    d.text((80, 8), title, fill=FG, font=SANS)
    for i, line in enumerate(wrapped):
        d.text((pad, bar + pad + i * lh), line, fill=line_colour(line), font=MONO)
    d.text((pad, height - 26), source, fill=DIM, font=SANS)
    out = IMG / f"{txt.stem}.png"
    img.save(out)
    return out


def axis_trap():
    raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
    lo, hi = contrast_limits(raw)
    frame0 = np.clip((raw[0, ..., 0].T - lo) / (hi - lo), 0, 1)  # shown as y (rows) x x (columns)
    with h5py.File("data/mitocheck_2d+t/pixelClassification.ilp", "r") as p:
        blocks = [b.attrs["blockSlice"] for b in p["PixelClassification/LabelSets/labels000"].values()]
    ranges = []
    for s in blocks:
        parts = [tuple(int(v) for v in r.split(":")) for r in s.strip("[]").split(",")]
        ranges.append((parts[1], parts[2]))  # (axis-1 range, axis-2 range) as stored
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
    titles = ["As saved in 2014: axis 1 = x, axis 2 = y\nall 27 label blocks fall on the image",
              "As ilastik 1.5 reads it: axis 1 = y, axis 2 = x\nblocks beyond y = 1024 fall off the image (red)"]
    outside = 0
    for k, (ax, title) in enumerate(zip(axes, titles)):
        ax.imshow(frame0, cmap="gray", extent=(0, 1344, 1024, 0))
        for a1, a2 in ranges:
            x, y = (a1, a2) if k == 0 else (a2, a1)
            off = k == 1 and y[1] > 1024
            outside += off
            ax.add_patch(patches.Rectangle((x[0], y[0]), x[1] - x[0], y[1] - y[0], fill=False, lw=1.6,
                                           ec="#ff6b6b" if off else "#4fd1ff"))
        ax.add_patch(patches.Rectangle((0, 0), 1344, 1024, fill=False, lw=1, ec="white", ls="--"))
        ax.set_xlim(-20, 1364); ax.set_ylim(1180, -20)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("x (pixels)"); ax.set_ylabel("y (pixels)")
    fig.suptitle(f"The axis-order trap: 27 hand-drawn label blocks (64×64 px), {outside} land outside the image "
                 "when x and y are swapped", fontsize=12)
    fig.tight_layout()
    out = IMG / "axis_trap.png"
    fig.savefig(out, dpi=90)
    return out


def difference_zoom():
    name = "mitocheck_94570_2D+t_01-53-volume-data_Tracking-Result.h5"
    runs = ["1.3.3post3", "1.5.0a3"]
    tracks = [h5py.File(f"results/ilastik-{v}/03_tracking/{name}", "r")["exported_data"] for v in runs]
    raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
    diffs = [int(np.sum(tracks[0][t] != tracks[1][t])) for t in range(raw.shape[0])]
    t = int(np.argmax(diffs))
    labels = [np.asarray(tr[t, ..., 0]).T for tr in tracks]
    diff = labels[0] != labels[1]
    cy, cx = (int(v) for v in ndimage.center_of_mass(diff))
    r = 60
    y0, x0 = max(cy - r, 0), max(cx - r, 0)
    win = (slice(y0, y0 + 2 * r), slice(x0, x0 + 2 * r))
    lo, hi = contrast_limits(raw)
    gray = np.clip((raw[t, ..., 0].T - lo) / (hi - lo), 0, 1)[win]
    colours = lineage_colours(int(max(l.max() for l in labels)))
    zoom = 4
    tiles = [overlay(gray, lab[win], colours, (2 * r * zoom, 2 * r * zoom)) for lab in labels]
    d = np.zeros((2 * r, 2 * r, 3), np.uint8)
    d[diff[win]] = MAGENTA
    tiles.append(Image.fromarray(d).resize((2 * r * zoom, 2 * r * zoom), Image.NEAREST))
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8))
    for ax, tile, title in zip(axes, tiles, [f"ilastik {runs[0]}", f"ilastik {runs[1]}",
                                             f"pixels with a different label ({int(diff[win].sum())})"]):
        ax.imshow(tile); ax.set_title(title, fontsize=11); ax.axis("off")
    fig.suptitle(f"Frame {t}, the frame with the most differences ({diffs[t]} px); "
                 f"crop x {x0}–{x0 + 2 * r}, y {y0}–{y0 + 2 * r}, magnified {zoom}×", fontsize=12)
    fig.tight_layout()
    out = IMG / "difference_zoom.png"
    fig.savefig(out, dpi=90)
    return out


if __name__ == "__main__":
    for txt in sorted((HERE / "screens").glob("*.txt")):
        print(render_screen(txt))
    print(axis_trap())
    print(difference_zoom())
