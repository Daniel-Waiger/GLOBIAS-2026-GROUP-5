# ilastik MitoCheck example: pixel classification → tracking → labels

Headless (no GUI) run of ilastik's MitoCheck 2D+t example (`https://data.ilastik.org/mitocheck.zip`,
data courtesy of the MitoCheck project, movie 94570) using the **pre-trained 2014 projects shipped in the
zip**. Nothing was re-labelled or re-trained by hand.

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
features): `…_CSV-Table.csv.csv` in the same folder. `labelimageId` in the CSV is the pixel value in
`…_Object-Identities.h5` for that frame.

Previews: `results/ilastik-1.3.3post3/04_previews/` (`frames_overview.png`, `tracking_overlay.gif`,
`objects_per_frame.png`, `summary.txt`).

## Steps

| step | script | output |
|---|---|---|
| 0 download data | `scripts/00_download_data.sh` | `data/mitocheck_2d+t/` (zip itself not committed, >100 MB) |
| 1 install ilastik | `scripts/01_install_ilastik.sh` | `.work/` (not committed) |
| 2 pixel classification | `scripts/02_pixel_classification.sh <version>` | `results/ilastik-<version>/02_pixel_classification/` |
| 3 conservation tracking | `scripts/03_tracking.sh <version>` | `results/ilastik-<version>/03_tracking/` |
| 4 previews + summary | `scripts/04_make_previews.py results/ilastik-<version>` | `results/ilastik-<version>/04_previews/` |
| 5 version comparison | `scripts/05_compare_versions.py` | `results/version_comparison.txt` |
| all | `scripts/run_all.sh` | everything above, then compress/split for git |

Logs of every ilastik call: `logs/ilastik-<version>/`.
The `*_run.ilp` files are the exact (patched, see below) project copies ilastik ran with.

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
- ilastik 1.3.1 is not in ilastik's download archive; 1.3.2post1 crashes when opening this pixel
  classification project (`TypeError` in the feature setup), so 1.3.3post3 is used.
- ilastik 1.4.1 no longer installs from the conda channels (dependency conflicts); 1.5.0a3 does.

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
  above 0.5. "Agreement" = number of pixels where two maps make the same call ÷ total pixels.
- **Matching lineages between versions** (`05_compare_versions.py`): label numbers are arbitrary, so
  each pixel gives a pair (value in 1.3.3 run, value in 1.5 run). The pair is packed into one number,
  `a × 1,000,000 + b`, only so that pairs can be counted quickly; it is unpacked again with integer
  division (`// 1,000,000`) and remainder (`% 1,000,000`). A label matches "one-to-one" if all its pixels
  pair with exactly one label in the other run and that label pairs back only with it.
- **Contrast stretch for previews** (`04_make_previews.py`): `(value − low) / (high − low)`, clipped to
  0…1, where `low`/`high` are the 1st and 99.8th percentiles of the movie's brightness. This maps
  "nearly darkest" to black and "nearly brightest" to white, so faint nuclei stay visible and a few very
  bright pixels don't wash out the image. Display only; the data is not changed.
- **Splitting** (`split_join_h5.py`): the first part gets `(53 + 1) // 2 = 27` frames (`//` = divide
  and round down), the second the remaining 26.
