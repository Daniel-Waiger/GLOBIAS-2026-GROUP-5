"""CI check: the committed results are complete and internally consistent, and the docs' links resolve.

Runs on a fresh clone (no ilastik needed). Checks, for each ilastik version:
  - the probability map halves rejoin (split_join_h5.py) into 53 frames of shape (1344, 1024, 2)
  - the tracking label images have the movie's shape, and every lineage/object id in the CSV table
    appears in the label images (and vice versa for lineages)
  - the preview files exist
and that every relative link/image in README.md and docs/REFERENCE.md points to an existing file.
Exits non-zero with a list of problems if anything fails.

usage: python scripts/check_results.py
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

NAME = "mitocheck_94570_2D+t_01-53-volume-data_"
FRAMES, X, Y = 53, 1344, 1024
problems = []


def check(ok, message):
    print(("ok    " if ok else "FAIL  ") + message)
    if not ok:
        problems.append(message)


for version in ["1.3.3post3", "1.5.0a3"]:
    run = Path(f"results/ilastik-{version}")
    pc, tr = run / "02_pixel_classification", run / "03_tracking"

    with tempfile.TemporaryDirectory() as tmp:
        for i in (1, 2):
            os.symlink((pc / f"{NAME}Probabilities.part{i}.h5").resolve(), Path(tmp) / f"p.part{i}.h5")
        subprocess.run([sys.executable, "scripts/split_join_h5.py", "join", f"{tmp}/p.h5"], check=True,
                       stdout=subprocess.DEVNULL)
        with h5py.File(f"{tmp}/p.h5", "r") as f:
            shape = f["exported_data"].shape
    check(shape == (FRAMES, X, Y, 2), f"{version}: probability halves rejoin to {shape}")

    images = {}
    for kind in ["Tracking-Result", "Object-Identities", "Merger-Result"]:
        with h5py.File(tr / f"{NAME}{kind}.h5", "r") as f:
            ds = f["exported_data"]
            check(ds.shape == (FRAMES, X, Y, 1), f"{version}: {kind} shape {ds.shape}")
            images[kind] = ds[...]
    table = pd.read_csv(tr / f"{NAME}CSV-Table.csv.csv")

    lineages_img = set(np.unique(images["Tracking-Result"]).tolist()) - {0, 1}
    lineages_csv = set(table.lineageId[table.lineageId > 0].tolist())
    check(lineages_img == lineages_csv,
          f"{version}: {len(lineages_csv)} lineages in CSV match the Tracking-Result values")

    objects_ok = all(
        set(table.labelimageId[table.frame == t].tolist())
        == set(np.unique(images["Object-Identities"][t]).tolist()) - {0}
        for t in range(FRAMES))
    check(objects_ok, f"{version}: CSV object ids match Object-Identities in all {FRAMES} frames")

    for name in ["frames_overview.png", "objects_per_frame.png", "summary.txt", "tracking_overlay.gif"]:
        check((run / "04_previews" / name).exists(), f"{version}: 04_previews/{name} exists")

for doc in ["README.md", "docs/REFERENCE.md"]:
    text = Path(doc).read_text()
    targets = [a or b for a, b in re.findall(r'\]\(([^)#\s]+)\)|src="([^"]+)"', text)]
    missing = [t for t in targets if not t.startswith("http")
               and not (Path(doc).parent / t).exists()]
    check(not missing, f"{doc}: {len(targets)} links, missing: {missing or 'none'}")

if problems:
    print(f"\n{len(problems)} problem(s)")
    sys.exit(1)
print("\nall checks passed")
