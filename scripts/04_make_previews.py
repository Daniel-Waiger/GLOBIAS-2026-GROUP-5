"""Step 4: make PNG/GIF previews and a summary of the ilastik results for one ilastik version.

usage: python 04_make_previews.py results/ilastik-<version>

Writes into results/ilastik-<version>/04_previews/:
  frames_overview.png   raw | cell probability | tracking labels, for frames 0, 26, 52
  tracking_overlay.gif  all 53 frames, each lineage outlined in its own colour on the raw image
  objects_per_frame.png  tracked and untracked objects per frame
  summary.txt           counts taken from the CSV table
"""
import sys
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from skimage.segmentation import find_boundaries

run = Path(sys.argv[1])
name = "mitocheck_94570_2D+t_01-53-volume-data_"
out = run / "04_previews"
out.mkdir(exist_ok=True)

raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
prob = h5py.File(run / "02_pixel_classification" / f"{name}Probabilities.h5", "r")["exported_data"]
track = h5py.File(run / "03_tracking" / f"{name}Tracking-Result.h5", "r")["exported_data"]
table = pd.read_csv(run / "03_tracking" / f"{name}CSV-Table.csv.csv")

# Data is stored t,x,y,c; transpose each frame to y,x for display.
def frame(ds, t, c=0):
    return np.asarray(ds[t, ..., c]).T

# Contrast stretch: map the 1st..99.8th percentile of the whole movie to 0..1.
lo, hi = np.percentile(raw[::4, ::4, ::4, 0], [1, 99.8])
def scaled(t):
    return np.clip((frame(raw, t) - lo) / (hi - lo), 0, 1)

# One fixed random colour per lineage id; 0 = background (black), 1 = untracked objects (grey).
rng = np.random.default_rng(0)
palette = rng.uniform(0.25, 1.0, size=(int(table["lineageId"].max()) + 2, 3))
palette[0] = 0
palette[1] = 0.45
def coloured(labels):
    return palette[np.clip(labels, 0, len(palette) - 1)]

ilastik_version = run.name.removeprefix("ilastik-")
frames = [0, 26, 52]
fig, axes = plt.subplots(len(frames), 3, figsize=(12, 3.4 * len(frames)))
for row, t in zip(axes, frames):
    row[0].imshow(scaled(t), cmap="gray"); row[0].set_title(f"raw, frame {t}")
    row[1].imshow(frame(prob, t, 1), cmap="magma", vmin=0, vmax=1); row[1].set_title("cell probability (step 2)")
    row[2].imshow(coloured(frame(track, t))); row[2].set_title("tracking labels = lineage id (grey = untracked)")
    for ax in row:
        ax.axis("off")
fig.suptitle(f"MitoCheck 94570, ilastik {ilastik_version}")
fig.tight_layout()
fig.savefig(out / "frames_overview.png", dpi=80)

gif = []
for t in range(raw.shape[0]):
    labels = frame(track, t)
    rgb = np.repeat(scaled(t)[..., None], 3, axis=2)
    edge = find_boundaries(labels, mode="inner")
    rgb[edge] = coloured(labels)[edge]
    img = Image.fromarray((rgb * 255).astype(np.uint8)).resize((672, 512))
    gif.append(img.quantize(colors=128))
gif[0].save(out / "tracking_overlay.gif", save_all=True, append_images=gif[1:], duration=200, loop=0)

per_frame = table.groupby("frame").size()
tracked = table[table.trackId > 0].groupby("frame").size()
untracked = table[table.trackId <= 0].groupby("frame").size().reindex(per_frame.index, fill_value=0)
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(tracked.index, tracked.values, marker="o", ms=3, label="tracked")
ax.plot(untracked.index, untracked.values, marker="o", ms=3, color="grey", label="untracked (trackId -1)")
ax.set_xlabel("frame"); ax.set_ylabel("objects"); ax.set_title("objects per frame")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(out / "objects_per_frame.png", dpi=90)

parents = table.loc[table["parentTrackId"] > 0, ["trackId", "parentTrackId"]].drop_duplicates()
summary = [
    f"ilastik version: {ilastik_version}",
    f"frames: {raw.shape[0]}  image size (x, y): {raw.shape[1]} x {raw.shape[2]}",
    f"objects (all frames): {len(table)}",
    f"tracks (trackId > 0; a track ends at a division): {table.trackId[table.trackId > 0].nunique()}",
    f"lineages (lineageId > 0 = pixel value in Tracking-Result image): {table.lineageId[table.lineageId > 0].nunique()}",
    f"untracked objects (trackId -1; pixel value 1 in Tracking-Result image): {(table.trackId <= 0).sum()}",
    f"tracks that start from a division (have a parent track): {parents['trackId'].nunique()}",
    f"objects in merger regions (mergerLabelId > 0): {(table['mergerLabelId'] > 0).sum()}",
    f"objects per frame: min {per_frame.min()}, median {int(per_frame.median())}, max {per_frame.max()}",
]
(out / "summary.txt").write_text("\n".join(summary) + "\n")
print("\n".join(summary))
