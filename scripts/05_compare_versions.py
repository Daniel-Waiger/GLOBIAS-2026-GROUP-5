"""Step 5: compare the ilastik 1.3.3post3 and 1.5.0a3 runs with each other and with the 2014 reference.

The 2014 reference is mitocheck_94570_2D+t_01-53_export.h5 (the probability map shipped in the zip).
Prints a plain-text report (run_all.sh saves it to results/version_comparison.txt).
"""
import collections

import h5py
import numpy as np
import pandas as pd

NAME = "mitocheck_94570_2D+t_01-53-volume-data_"
RUNS = {"1.3.3post3": "results/ilastik-1.3.3post3", "1.5.0a3": "results/ilastik-1.5.0a3"}


def load(run, step, kind):
    return h5py.File(f"{run}/{step}/{NAME}{kind}.h5", "r")["exported_data"]


print("== Step 2: pixel classification (cell = probability of channel 1 > 0.5)")
ref = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53_export.h5", "r")["volume/data"]
probs = {v: load(r, "02_pixel_classification", "Probabilities") for v, r in RUNS.items()}
agree = {v: [] for v in RUNS}
max_diff = 0.0
for t in range(ref.shape[0]):
    ref_cell = ref[t][..., 1] > 0.5
    frames = {v: p[t] for v, p in probs.items()}
    for v, f in frames.items():
        agree[v].append(np.mean((f[..., 1] > 0.5) == ref_cell))
    max_diff = max(max_diff, float(np.abs(frames["1.3.3post3"] - frames["1.5.0a3"]).max()))
for v in RUNS:
    print(f"  {v} vs 2014 reference: same cell/background call on {100 * np.mean(agree[v]):.3f}% of pixels")
print(f"  largest per-pixel probability difference 1.3.3post3 vs 1.5.0a3: {max_diff:.3f}")

print("\n== Step 3: tracking")
for v, r in RUNS.items():
    df = pd.read_csv(f"{r}/03_tracking/{NAME}CSV-Table.csv.csv")
    print(f"  {v}: objects {len(df)}, tracks {df.trackId[df.trackId > 0].nunique()}, "
          f"lineages {df.lineageId[df.lineageId > 0].nunique()}, untracked objects (trackId -1) {(df.trackId <= 0).sum()}")

# Lineage ids are arbitrary numbers, so match them by pixel overlap: a lineage "matches" if all of
# its pixels in one version fall on exactly one lineage in the other version (and vice versa).
a = load(RUNS["1.3.3post3"], "03_tracking", "Tracking-Result")
b = load(RUNS["1.5.0a3"], "03_tracking", "Tracking-Result")
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
print(f"  label values matching one-to-one between versions: {one_to_one} of {len(to_b)} (value 1 = untracked objects)")
print(f"  pixels labelled in only one version (all frames): {only_one}")
