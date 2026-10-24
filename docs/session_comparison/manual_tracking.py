"""Compare the hand-made tracks in manualTracking.ilp (2014) with Session 0's automatic tracking runs.

The manual tracks: data/mitocheck_2d+t/manualTracking.ilp, made in ilastik's Manual Tracking workflow on
11 Feb 2014. It stores
  ObjectExtraction/LabelImage/0   its own object segmentation (hysteresis threshold 0.2/0.5 of the 2014
                                  probability map), one dataset per frame, axes t,x,y,z,c
  ManualTracking/Labels/0/<t>/<object id>   the track id(s) a person gave that object; two ids = two
                                  touching cells in one object; -1 = marked as a false detection
  ManualTracking/Divisions/0      rows (parent track, child track, child track, last frame of the parent)
The automatic tracks: results/<version>/03_tracking/ (Object-Identities.h5 and the CSV table).

Each annotated object is matched to the automatic object(s) that cover its pixels. Then, for every
step the person drew (same track in frame t and t+1, or parent at t -> child at t+1 for a division), the
step counts as followed if the matched automatic objects are joined the same way: same track, or the
automatic parent -> child. A division counts as found if the automatic tracking splits the matched parent
into the two matched children within +-2 frames of the manual division.

usage (repo root, a python with h5py, numpy, pandas, matplotlib, scikit-image):
    python docs/session_comparison/manual_tracking.py
"""
import collections
import sys
import textwrap
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from scipy import ndimage
from skimage.segmentation import find_boundaries

sys.path.insert(0, "scripts")
from overlay import contrast_limits  # noqa: E402

OUT_TREE = Path(__file__).parent / "img" / "manual_tracks.png"
OUT_CASES = Path(__file__).parent / "img" / "manual_tracks_cases.png"
NAME = "mitocheck_94570_2D+t_01-53-volume-data_"
RUNS = {"1.3.3post3": "results/ilastik-1.3.3post3/03_tracking", "1.5.0a3": "results/ilastik-1.5.0a3/03_tracking"}
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
GRAY, INK, INK2, SURFACE = "#a8a7a2", "#0b0b0b", "#52514e", "#fcfcfb"
GROW = 3  # px; see Auto.match
REUSED = 112  # the second cell the person labelled "12" (see manual_annotations)

ilp = h5py.File("data/mitocheck_2d+t/manualTracking.ilp", "r")
T = 53


def manual_frame(t):
    return ilp[f"ObjectExtraction/LabelImage/0/[[{t}, 0, 0, 0, 0], [{t + 1}, 1344, 1024, 1, 1]]"][0, :, :, 0, 0]


def manual_annotations():
    """{(t, object id): [track ids]} and the division table.

    The person used track 12 twice: for a cell in frames 0-25 (divides into 14 + 15) and again for a
    daughter of 8 in frames 51-52. The second use is renamed REUSED so the two cells stay apart.
    """
    ann = {}
    for t, objs in ilp["ManualTracking/Labels/0"].items():
        for o, tracks in objs.items():
            ann[int(t), int(o)] = [REUSED if (x == 12 and int(t) >= 51) else int(x) for x in tracks[()]]
    divisions = ilp["ManualTracking/Divisions/0"][()].copy()
    divisions[(divisions[:, 0] == 8) & (divisions[:, 1] == 12), 1] = REUSED
    return ann, divisions


def manual_steps(ann, divisions):
    """Every link the person drew: (kind, t, object at t, object at t+1, track label at t+1)."""
    where = collections.defaultdict(dict)  # track -> {t: object}
    for (t, o), tracks in ann.items():
        for k in tracks:
            if k > 0:
                where[k][t] = o
    steps = []
    for k, frames in where.items():
        for t, o in frames.items():
            if t + 1 in frames:
                steps.append(("same cell", t, o, frames[t + 1], k))
    for parent, c1, c2, t in divisions:
        for c in (c1, c2):
            steps.append(("division", int(t), where[parent][t], where[c][t + 1], int(c)))
    return steps, where


class Auto:
    """One automatic run: object image + per-object track table.

    Objects are matched through the CSV table's object centres, not the Object-Identities image: in the
    1.3.3post3 run, 81 of the 166 objects made by splitting merged nuclei carry a different id in the image
    than in the table (1.5.0a3: none), so joining image ids to table rows would mix up those cells.
    """

    def __init__(self, run):
        self.ids = h5py.File(f"{run}/{NAME}Object-Identities.h5", "r")["exported_data"]
        df = pd.read_csv(f"{run}/{NAME}CSV-Table.csv.csv",
                         usecols=["frame", "labelimageId", "trackId", "lineageId", "parentTrackId", "mergerLabelId",
                                  "Center_of_the_object_0", "Center_of_the_object_1"])
        df["cx"] = df.Center_of_the_object_0.round().astype(int)
        df["cy"] = df.Center_of_the_object_1.round().astype(int)
        self.table = df.set_index(["frame", "labelimageId"])
        self.centres = {t: g for t, g in df.groupby("frame")}
        self.frames = {}

    def frame(self, t):
        if t not in self.frames:
            self.frames[t] = self.ids[t, ..., 0]
        return self.frames[t]

    def match(self, t, mask):
        """Automatic objects of a manual object: the table rows whose centre lies inside it, grown by GROW px.

        Growing catches curved objects and split-up merged nuclei whose centre falls just outside. Checked
        on 1.5.0a3, where image and table agree: for all 404 annotated objects this gives exactly the image
        objects that cover at least 20% of the manual pixels.
        """
        g = self.centres[t]
        grown = ndimage.binary_dilation(mask, iterations=GROW)
        return [int(i) for i in g[grown[g.cx.values, g.cy.values]].labelimageId]

    def row(self, t, i):
        return self.table.loc[(t, i)]


def joined(auto, t, a_objs, b_objs):
    """Are any of the automatic objects at t joined to any at t+1? -> 'same track', 'division' or None."""
    for a in a_objs:
        ra = auto.row(t, a)
        if ra.trackId <= 0:
            continue
        for b in b_objs:
            rb = auto.row(t + 1, b)
            if rb.trackId == ra.trackId:
                return "same track"
            if rb.parentTrackId == ra.trackId:
                return "division"
    return None


def evaluate(version, run, ann, steps, divisions, where):
    auto = Auto(run)
    matches = {}
    for (t, o) in sorted(ann):
        matches[t, o] = auto.match(t, manual_frame(t) == o)
    cells = {k: v for k, v in ann.items() if max(v) > 0}
    found = sum(bool(matches[k]) for k in cells)
    single = sum(len(matches[k]) == 1 for k in cells)
    # Objects the person labelled as two cells: did the automatic run split them into two objects?
    merged = {k: v for k, v in cells.items() if len(v) > 1}
    merged_split = sum(len(matches[k]) >= 2 for k in merged)
    false_det = {k: [(i, int(auto.row(k[0], i).trackId)) for i in matches[k]] for k, v in ann.items() if max(v) < 0}

    result = collections.Counter()
    failures = []
    for kind, t, oa, ob, k in steps:
        how = joined(auto, t, matches[t, oa], matches[t + 1, ob])
        ok = how == ("same track" if kind == "same cell" else "division")
        result[kind, ok] += 1
        if not ok:
            failures.append((kind, t, k, how))

    # Divisions: did the automatic run split the matched parent into the matched children near the manual frame?
    div_found = []
    for parent, c1, c2, t in divisions:
        t = int(t)
        hit = None
        for dt in (0, -1, 1, -2, 2):
            tp = t + dt
            if tp not in where[parent] and tp not in where[c1]:
                continue
            pa = where[parent].get(tp, where[c1].get(tp))
            kids = [where[c][tp + 1] for c in (c1, c2) if tp + 1 in where[c]]
            if len(kids) < 2 or pa is None:
                continue
            ok = all(joined(auto, tp, matches[tp, pa], matches[tp + 1, kid]) == "division"
                     for kid in kids)
            if ok:
                hit = dt
                break
        div_found.append((int(parent), int(c1), int(c2), t, hit))

    # Whole lineages: how many automatic lineages does each manual lineage touch?
    root = {}
    children = {int(p): (int(a), int(b)) for p, a, b, _ in divisions}
    parents = {c: p for p, cs in children.items() for c in cs}
    for k in where:
        r = k
        while r in parents:
            r = parents[r]
        root[k] = r
    lineages = collections.defaultdict(collections.Counter)
    for (t, o), tracks in cells.items():
        for k in tracks:
            for i in matches[t, o]:
                lid = int(auto.row(t, i).lineageId)
                if lid > 0:
                    lineages[root[k]][lid] += 1
    return dict(version=version, cells=len(cells), found=found, single=single, merged=len(merged),
                merged_split=merged_split, false_det=false_det, steps=result,
                failures=failures, divisions=div_found, lineages=dict(lineages), matches=matches, auto=auto)


def report(r):
    s = r["steps"]
    print(f"\n== ilastik {r['version']}")
    print(f"  annotated cell objects: {r['cells']}; matched to an automatic object: {r['found']}; "
          f"to exactly one: {r['single']}")
    print(f"  objects the person labelled as two touching cells: {r['merged']}; split into >= 2 automatic objects: "
          f"{r['merged_split']}")
    print(f"  object marked as a false detection: {r['false_det']}  (automatic trackId -1 = left untracked)")
    for kind in ("same cell", "division"):
        n_ok, n = s[kind, True], s[kind, True] + s[kind, False]
        print(f"  manual steps '{kind}': {n_ok} of {n} followed ({100 * n_ok / n:.1f}%)")
    for kind, t, k, how in r["failures"]:
        print(f"    missed: {kind} into track {k}, frame {t} -> {t + 1} (automatic: {how or 'not joined'})")
    for p, a, b, t, hit in r["divisions"]:
        print(f"  division {p} -> {a} + {b} after frame {t}: "
              + ("not found within +-2 frames" if hit is None else f"found, {hit:+d} frames"))
    for rt, c in sorted(r["lineages"].items()):
        print(f"  manual lineage of track {rt}: automatic lineages {dict(c.most_common())}")


def tree_figure(r, where, divisions, ann):
    """The manual lineage trees, coloured by whether the automatic run followed each step."""
    children = {int(p): (int(a), int(b)) for p, a, b, _ in divisions}
    order = []

    def visit(k):
        order.append(k)
        for c in children.get(k, ()):
            visit(c)

    parents = {c for cs in children.values() for c in cs}
    for k in sorted(where):
        if k not in parents:
            visit(k)
    y = {k: i for i, k in enumerate(order)}
    missed = {(t, k) for kind, t, k, how in r["failures"] if kind == "same cell"}
    missed_div = {(t, k) for kind, t, k, how in r["failures"] if kind == "division"}

    fig, ax = plt.subplots(figsize=(13, 6.2))
    for k, frames in where.items():
        a, b = min(frames), max(frames)
        for t in range(a, b):
            ax.plot([t, t + 1], [y[k], y[k]], color=ORANGE if (t, k) in missed else BLUE, lw=3.5,
                    solid_capstyle="butt")
        ax.text(a - 0.7, y[k], "12" if k == REUSED else str(k), ha="right", va="center", fontsize=8.5, color=INK2)
    for p, c1, c2, t in divisions:
        for c in (c1, c2):
            ax.plot([t, t + 1], [y[p], y[c]], color=ORANGE if (t, c) in missed_div else BLUE, lw=1.8)
    # Cell 12, frames 0-25: ilastik saw two touching nuclei where the person saw one.
    for dy in (-0.22, 0.22):
        ax.plot([0, 25], [y[12] + dy] * 2, color=ORANGE, lw=1.2)
    merged = collections.defaultdict(list)
    for (t, o), tracks in ann.items():
        if len(tracks) > 1:
            for k in tracks:
                merged[k].append(t)
    for k, ts in merged.items():
        ax.scatter(ts, [y[k]] * len(ts), s=16, color=YELLOW, zorder=3, edgecolor=INK2, lw=0.4)
    badges = [(25.5, y[12] - 0.75), (12.2, (y[17] + y[19]) / 2), (20.5, y[16] - 0.6), (51, y[21] - 0.6)]
    for n, (t, yy) in enumerate(badges, start=1):
        ax.text(t, yy, str(n), ha="center", va="center", fontsize=9, fontweight="bold", color=SURFACE,
                bbox=dict(boxstyle="circle,pad=0.2", fc=ORANGE, ec="none"))
    ax.set_xlim(-3, 53)
    ax.set_ylim(len(y) - 0.4, -1.2)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("frame", color=INK2)
    s = r["steps"]
    n_same = s["same cell", True] + s["same cell", False]
    found = sum(d[4] is not None for d in r["divisions"])
    ax.set_title(f"The 2014 hand-made tracks, as followed by Session 0's tracking: {s['same cell', True]} of {n_same} "
                 f"steps, {found} of {len(divisions)} divisions", loc="left", fontsize=11, fontweight="bold")
    ax.legend(handles=[Line2D([], [], color=BLUE, lw=3.5, label="step ilastik also made"),
                       Line2D([], [], color=ORANGE, lw=3.5, label="step ilastik did not make (cases 1-4)"),
                       Line2D([], [], color=ORANGE, lw=1.2, label="ilastik: two cells here"),
                       Line2D([], [], marker="o", ls="", color=YELLOW, markeredgecolor=INK2,
                              label="person: two touching cells in one object")],
              loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False, fontsize=9)
    fig.text(0.01, 0.01, "The same for ilastik 1.3.3post3 and 1.5.0a3. Numbers are the person's track labels; "
             "the person used 12 twice (the short track under 8 is the second use).", fontsize=8.5, color=INK2)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT_TREE, dpi=100, facecolor=SURFACE)
    print(OUT_TREE)


# The four disagreements: frames, the person's tracks and ilastik's tracks with colours, caption.
CASES = [
    ((0, 25, 26), {12: BLUE, 14: AQUA, 15: GREEN}, {117: AQUA, 118: GREEN},
     "1  Cell 12. The person: one large nucleus that divides after frame 25. ilastik: two touching nuclei "
     "from frame 0 on (117, 118), so no division."),
    ((10, 11, 12), {17: BLUE, 19: AQUA, 18: GREEN}, {36: BLUE, 253: AQUA, 82: GREEN, 254: ORANGE},
     "2  Cell 17 divides after frame 10. ilastik takes as its second daughter a daughter of the neighbouring "
     "division (254); the real sister starts as a new cell (82)."),
    ((20, 21, 22), {16: BLUE}, {28: BLUE, 21: ORANGE},
     "3  Cell 16 divides after frame 20, and neither records it. The person follows one daughter; ilastik "
     "follows the other and gives the first to a neighbour's track (21), leaving that neighbour untracked."),
    ((50, 51, 52), {21: BLUE, 20: AQUA}, {138: BLUE, 137: AQUA},
     "4  Frame 51: ilastik moves track 138 to another cell for one frame and back; cell 21 is left "
     "untracked."),
]


def cases_figure(auto, ann):
    """Each disagreement in three frames: the person's tracks (left), ilastik's (right)."""
    raw = h5py.File("data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5", "r")["volume/data"]
    lo, hi = contrast_limits(raw)
    r, zoom = 48, 3
    up = lambda img: np.kron(img, np.ones((zoom, zoom), dtype=img.dtype))
    halo = [patheffects.withStroke(linewidth=2.5, foreground=INK)]
    fig, axes = plt.subplots(len(CASES), 6, figsize=(13, 11.5))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.01, hspace=0.62, wspace=0.06)
    for row, (frames, person, ilastik, caption) in zip(axes, CASES):
        for j, t in enumerate(frames):
            # Centre each frame on the person's cells in it, so the crop follows them.
            cs = [ndimage.center_of_mass(manual_frame(t) == o) for (tt, o), tr in ann.items()
                  if tt == t and set(tr) & set(person)]
            cx, cy = (int(np.mean([c[i] for c in cs])) for i in (0, 1))
            win = (slice(cx - r, cx + r), slice(cy - r, cy + r))
            gray = up(np.clip((raw[t, ..., 0][win] - lo) / (hi - lo), 0, 1).T)
            for ax, lab, is_auto in [(row[j], manual_frame(t)[win].T, False), (row[j + 3], auto.frame(t)[win].T, True)]:
                lab = up(lab)
                rgb = np.repeat(gray[..., None] * 0.9, 3, axis=2)
                rgb[find_boundaries(lab, mode="inner")] = 0.45
                names = []
                for o in np.unique(lab[lab > 0]):
                    if is_auto:
                        k = int(auto.row(t, int(o)).trackId)
                        name, colour = (str(k), ilastik[k]) if k in ilastik else ("untracked", GRAY) if k < 0 else ("", None)
                    else:
                        tracks = [k for k in ann.get((t, int(o)), []) if k in person]
                        name, colour = ",".join(map(str, tracks)), (person[tracks[0]] if tracks else None)
                    if colour is None:
                        continue
                    m = lab == o
                    yy, xx = np.nonzero(m)
                    rgb[ndimage.binary_dilation(find_boundaries(m, mode="inner"))] = matplotlib.colors.to_rgb(colour)
                    names.append((xx.mean(), yy.mean(), name))
                ax.imshow(rgb, interpolation="nearest")
                for x, y, name in names:
                    ax.text(x, y, name, ha="center", va="center", fontsize=8.5, color="white", path_effects=halo)
                ax.set_xticks([])
                ax.set_yticks([])
                for sp in ax.spines.values():
                    sp.set_visible(False)
                ax.set_title(f"frame {t}", fontsize=9, color=INK2)
        row[0].annotate(textwrap.fill(caption, 125), (0, 1.13), xycoords="axes fraction", fontsize=9.5, color=INK,
                        va="bottom")
    fig.text(0.25, 0.975, "the person (2014, manualTracking.ilp)", ha="center", fontsize=11, fontweight="bold")
    fig.text(0.75, 0.975, "ilastik (Session 0; 1.3.3post3 and 1.5.0a3 the same)", ha="center", fontsize=11,
             fontweight="bold")
    fig.patch.set_facecolor(SURFACE)
    fig.savefig(OUT_CASES, dpi=100, facecolor=SURFACE)
    print(OUT_CASES)


def main():
    ann, divisions = manual_annotations()
    steps, where = manual_steps(ann, divisions)
    n_tracks = len({k for v in ann.values() for k in v if k > 0})
    print(f"manualTracking.ilp: {len(ann)} annotated objects in {len({t for t, _ in ann})} frames, "
          f"{n_tracks} track labels, {len(divisions)} divisions, {len(steps)} manual steps")
    results = {}
    for version, run in RUNS.items():
        results[version] = evaluate(version, run, ann, steps, divisions, where)
        report(results[version])
    tree_figure(results["1.5.0a3"], where, divisions, ann)
    cases_figure(results["1.5.0a3"]["auto"], ann)


if __name__ == "__main__":
    main()
