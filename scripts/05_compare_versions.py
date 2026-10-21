"""Step 5: compare the ilastik 1.3.3post3 and 1.5.0a3 runs with each other and with the 2014 reference.

The 2014 reference is mitocheck_94570_2D+t_01-53_export.h5 (the probability map shipped in the zip).
Prints a plain-text report (run_all.sh saves it to results/version_comparison.txt).

Two agreement measures for the cell masks (cell = probability of channel 1 > 0.5):
  pixel agreement = pixels with the same call / all pixels  (dominated by background: nuclei are ~5% of a frame)
  IoU             = pixels called cell in both / pixels called cell in either  (ignores shared background)
"""
import collections

import h5py
import numpy as np
import pandas as pd

NAME = "mitocheck_94570_2D+t_01-53-volume-data_"
RUNS = {"1.3.3post3": "results/ilastik-1.3.3post3", "1.5.0a3": "results/ilastik-1.5.0a3"}


def load(run, step, kind):
    return h5py.File(f"{run}/{step}/{NAME}{kind}.h5", "r")["exported_data"]


class Probabilities:
    """Probability map of one run; reads the committed .part1/.part2 halves if the full file is absent."""

    def __init__(self, run):
        try:
            self.parts = [load(run, "02_pixel_classification", "Probabilities")]
        except FileNotFoundError:
            self.parts = [load(run, "02_pixel_classification", f"Probabilities.part{i}") for i in (1, 2)]

    def __getitem__(self, t):
        first = self.parts[0].shape[0]
        return self.parts[0][t] if t < first else self.parts[1][t - first]


print("== Step 2: pixel classification (cell = probability of channel 1 > 0.5)")
ref = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53_export.h5", "r")["volume/data"]
probs = {v: Probabilities(r) for v, r in RUNS.items()}
pairs = {"1.3.3post3 vs 2014 reference": ("1.3.3post3", "ref"), "1.5.0a3 vs 2014 reference": ("1.5.0a3", "ref"),
         "1.3.3post3 vs 1.5.0a3": ("1.3.3post3", "1.5.0a3")}
same, both, either, cell_px, total_px = (collections.Counter() for _ in range(5))
max_diff = 0.0
for t in range(ref.shape[0]):
    frames = {v: p[t] for v, p in probs.items()}
    cells = {v: f[..., 1] > 0.5 for v, f in frames.items()}
    cells["ref"] = ref[t][..., 1] > 0.5
    for label, (p, q) in pairs.items():
        same[label] += int(np.sum(cells[p] == cells[q]))
        both[label] += int(np.sum(cells[p] & cells[q]))
        either[label] += int(np.sum(cells[p] | cells[q]))
    cell_px["ref"] += int(cells["ref"].sum())
    total_px["ref"] += cells["ref"].size
    max_diff = max(max_diff, float(np.abs(frames["1.3.3post3"] - frames["1.5.0a3"]).max()))
print(f"  nuclei cover {100 * cell_px['ref'] / total_px['ref']:.1f}% of the pixels (2014 reference)")
for label in pairs:
    print(f"  {label}: pixel agreement {100 * same[label] / total_px['ref']:.4f}%, "
          f"cell IoU {100 * both[label] / either[label]:.4f}%")
print(f"  largest per-pixel probability difference 1.3.3post3 vs 1.5.0a3: {max_diff:.3f}")

print("\n== Step 3: tracking")
for v, r in RUNS.items():
    df = pd.read_csv(f"{r}/03_tracking/{NAME}CSV-Table.csv.csv")
    print(f"  {v}: objects {len(df)}, tracks {df.trackId[df.trackId > 0].nunique()}, "
          f"lineages {df.lineageId[df.lineageId > 0].nunique()}, untracked objects (trackId -1) {(df.trackId <= 0).sum()}")

a = load(RUNS["1.3.3post3"], "03_tracking", "Tracking-Result")
b = load(RUNS["1.5.0a3"], "03_tracking", "Tracking-Result")
differ = [int(np.sum(a[t] != b[t])) for t in range(a.shape[0])]
fg = sum(int(np.sum(a[t] > 0)) for t in range(a.shape[0]))
print(f"  pixels whose Tracking-Result value differs: {sum(differ)} of {fg} labelled pixels "
      f"({100 * sum(differ) / fg:.4f}%); per frame min {min(differ)}, median {int(np.median(differ))}, max {max(differ)}")

# Lineage ids could in principle be numbered differently, so also match them by pixel overlap: a lineage "matches" if all of
# its pixels in one version fall on exactly one lineage in the other version (and vice versa).
pairs = collections.Counter()
for t in range(a.shape[0]):
    x, y = a[t].ravel().astype(np.int64), b[t].ravel().astype(np.int64)
    m = (x > 0) | (y > 0)
    keys, counts = np.unique(x[m] * 1_000_000 + y[m], return_counts=True)
    for k, c in zip(keys, counts):
        pairs[(int(k // 1_000_000), int(k % 1_000_000))] += int(c)
to_b, to_a = collections.defaultdict(set), collections.defaultdict(set)
only_one = 0
for (i, j), c in pairs.items():
    if i and j:
        to_b[i].add(j)
        to_a[j].add(i)
    else:
        only_one += c
one_to_one = sum(1 for i, s in to_b.items() if len(s) == 1 and len(to_a[next(iter(s))]) == 1)
same_number = sum(1 for i, s in to_b.items() if max(s, key=lambda j: pairs[(i, j)]) == i)
print(f"  label values whose main overlap in the other run has the same number: {same_number} of {len(to_b)}")
print(f"  label values matching strictly one-to-one (no pixel overlaps any other label): {one_to_one} of {len(to_b)}"
      " (value 1 = untracked objects)")
print(f"  pixels labelled in only one version (all frames): {only_one}")
