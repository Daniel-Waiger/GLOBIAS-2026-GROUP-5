# Technical reference

Headless (no GUI) run of ilastik's MitoCheck 2D+t example (`https://data.ilastik.org/mitocheck.zip`,
data courtesy of the MitoCheck project, movie 94570) using the **pre-trained 2014 projects shipped in the
zip**. Nothing was re-labelled or re-trained by hand. The story of how it got here is in the
[README](../README.md).

Main run: **ilastik 1.3.3post3** (`results/ilastik-1.3.3post3/`).
Comparison run: **ilastik 1.5.0a3** (`results/ilastik-1.5.0a3/`).

## Final labels

`results/ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_Tracking-Result.h5`
(dataset `exported_data`, shape `(t=53, x=1344, y=1024, c=1)`, uint32):

| pixel value | meaning |
|---|---|
| 0 | background |
| 1 | object detected but not assigned to any track (`trackId = -1` in the CSV) |
| 2 … 118 | lineage id: a cell and all its descendants after divisions keep the same value |

Per-object details (frame, object id, track id, lineage id, parent track, merger id, shape/intensity
features): `…_CSV-Table.csv.csv` in the same folder (ilastik appends the second `.csv`). `labelimageId`
in the CSV is the pixel value in `…_Object-Identities.h5` for that frame.

Note the axis order: every HDF5 file here is stored `t, x, y, c`. Displaying `data[t, ..., 0]` directly
shows the frame transposed; use `data[t, ..., 0].T` for the usual orientation.

Previews: `results/ilastik-<version>/04_previews/` (`frames_overview.png`, `tracking_overlay.gif`,
`objects_per_frame.png`, `summary.txt`) and `results/side_by_side_tracking.gif` (both versions).

## Steps

| step | script | output |
|---|---|---|
| 0 download data | `scripts/00_download_data.sh` | `data/mitocheck_2d+t/` (zip itself not committed, >100 MB) |
| 1 install ilastik | `scripts/01_install_ilastik.sh` | `.work/` (not committed) |
| 2 pixel classification | `scripts/02_pixel_classification.sh <version>` | `results/ilastik-<version>/02_pixel_classification/` |
| 3 conservation tracking | `scripts/03_tracking.sh <version>` | `results/ilastik-<version>/03_tracking/` |
| 4 previews + summary | `scripts/04_make_previews.py results/ilastik-<version>` | `results/ilastik-<version>/04_previews/` |
| 5 version comparison | `scripts/05_compare_versions.py` | `results/version_comparison.txt` |
| 6 side-by-side GIF | `scripts/06_side_by_side_gif.py` | `results/side_by_side_tracking.gif` |
| all | `scripts/run_all.sh` | steps 0–6, then compress/split for git |

Logs of every ilastik call: `logs/ilastik-<version>/`.

**CI** (`.github/workflows/ci.yml`): on every push and pull request, the shell scripts are parsed, the
Python scripts compiled, `scripts/check_results.py` checks that the committed results are complete and
consistent (probability halves rejoin; label images match the CSV tables; previews exist; doc links
resolve), and `05_compare_versions.py` must reproduce `results/version_comparison.txt` exactly. No
ilastik is needed for this. Started manually (*Actions → CI → Run workflow*, tick *full_pipeline*), it
also re-runs `scripts/run_all.sh` from scratch (about an hour; ilastik limited to 2 threads / 5 GB RAM)
and fails if the regenerated summaries differ from the committed ones.
The `*_run.ilp` files are the exact (patched, see below) project copies ilastik ran with.
Images for the README: `docs/chronicle/make_images.py` (terminal renderings of the excerpts in
`docs/chronicle/screens/`, plus two figures).

## Results

From `results/version_comparison.txt` (cell = probability of the nucleus channel > 0.5):

| | 1.3.3post3 | 1.5.0a3 |
|---|---|---|
| pixel agreement with the 2014 probability map | 99.9888% | 99.9888% |
| cell IoU with the 2014 probability map | 99.7757% | 99.7757% |
| objects / tracks / lineages / untracked objects | 7485 / 357 / 117 / 328 | 7485 / 357 / 117 / 328 |

Between the two versions: cell IoU 99.9993%; 161 of 3,605,410 labelled pixels have a different
Tracking-Result value (0.0045%; median 1 px per frame, max 62 in frame 44). 137 of these lie in objects
that ilastik's merger resolution split into two cells, 24 are cell/background edge pixels. Lineage
numbers were the same in both runs. Two later reruns showed that 1.3.3post3 tracking is not exactly
repeatable (merged objects split differently; in one rerun lineages 117 and 118 swapped numbers), so
this comparison mixes version differences with run-to-run variation; see
[session_comparison.md](session_comparison.md).

## Changes needed to run the 2014 projects

The original files in `data/mitocheck_2d+t/` are untouched; fixes are applied to the `*_run.ilp` copies.

- **Tracking project, both versions** (`scripts/fix_legacy_tracking_params.py`): the 2014 file stores the
  tracking parameters one level deeper (`Parameters/0/…`) than ilastik 1.3.3+ reads them
  (`Parameters/…`). The values are moved up unchanged. `max_nearest_neighbors` (did not exist in 2014) is
  set to 3, the current default.
- **Pixel classification, 1.5.0a3 only** (`scripts/fix_legacy_labels.py`): the hand-drawn training labels
  are stored in `t,x,y,c` order; ilastik 1.5 expects `t,y,x,c`. The x and y axes of each label block
  are swapped so every label stays on the same pixel.
- The tracking project only opens if its original input `mitocheck_94570_2D+t_01-53_export.h5` (2014
  probabilities) is present; it is linked next to the project. The object classifiers stored in the
  project were trained on that file; the actual tracking run uses the new step-2 probabilities.
- ilastik 1.3.1 is not in ilastik's download archive (only 1.3.1b1, a beta).
- ilastik 1.3.2post1 fails to open the pixel classification project **in this environment**: its bundled
  fast-filters library does not load (`undefined symbol: __atan2_finite`; the system has glibc 2.39), so
  ilastik falls back to vigra filters, and that fallback path raises
  `TypeError: '>' not supported between instances of 'tuple' and 'float'` for 2D data
  (`lazyflow/operators/filterOperators.py`, line 101). [Inference] On a system where fast filters load,
  this code path is not used.
- ilastik 1.4.1 no longer installs from the conda channels (dependency conflicts); 1.5.0a3 does.
- The probability maps of the two versions differ by up to 0.12 per pixel although both use the same
  project. I did not determine why.

## Large files

ilastik writes HDF5 uncompressed. `scripts/compress_h5.py` re-writes each result with gzip compression;
values are checked to be bit-identical. The probability maps are still 110 MB compressed, over GitHub's
100 MB per-file limit, so each is split into `.part1.h5` (frames 0–26) and `.part2.h5` (frames 27–52).
To rebuild the full file:

```bash
python scripts/split_join_h5.py join results/ilastik-1.3.3post3/02_pixel_classification/mitocheck_94570_2D+t_01-53-volume-data_Probabilities.h5
```

## The arithmetic in the scripts

- **Cell/background call** (`05_compare_versions.py`): channel 1 of the probability map is the
  classifier's estimate (0 to 1) that a pixel belongs to a nucleus; a pixel is called "cell" when it is
  above 0.5.
- **Pixel agreement vs IoU** (`05_compare_versions.py`): pixel agreement = pixels where two maps make the
  same call ÷ all pixels. Because nuclei cover only 5% of a frame, two maps that agree on the empty
  background already score ~95%. IoU ("intersection over union") = pixels called cell in **both** maps ÷
  pixels called cell in **either** map; shared background does not count, so it measures agreement on
  the cells only. 100% means identical cell masks.
- **Matching lineages between versions** (`05_compare_versions.py`): each pixel gives a pair (value in
  the 1.3.3 run, value in the 1.5 run). The pair is packed into one number, `a × 1,000,000 + b`, only so
  that pairs can be counted quickly; it is unpacked again with integer division (`// 1,000,000`) and
  remainder (`% 1,000,000`). A label matches "one-to-one" if all its pixels pair with exactly one label
  in the other run and that label pairs back only with it.
- **Contrast stretch for previews** (`overlay.py`, `contrast_limits`): `(value − low) / (high − low)`,
  clipped to 0…1, where `low`/`high` are the 1st and 99.8th percentiles of the movie's brightness. This
  maps "nearly darkest" to black and "nearly brightest" to white. Display only.
- **Circling differences** (`06_side_by_side_gif.py`): differing pixels are grown by 5 pixels in every
  direction ("dilation") so that pixels lying close together merge into one spot; each spot is circled at
  its centre of mass (the average x and y of its pixels).
- **Splitting** (`split_join_h5.py`): the first part gets `(53 + 1) // 2 = 27` frames (`//` = divide
  and round down), the second the remaining 26.
