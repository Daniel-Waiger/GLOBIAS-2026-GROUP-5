# Reproducibility report: ilastik MitoCheck workflow

Branch `repro/opus-5.5-high`, run on 2026-10-23 in a Claude Code cloud session.

## Agent

| | |
|---|---|
| model | `claude-opus-5-5` (session `configured_model`, `session_context.model` and `last_served_model` all report this) |
| effort | `high` (session `effort_level`) |
| permission mode | auto |
| machine | 4 CPU cores, 15 GB RAM, Linux 6.18 x86_64, glibc 2.39 (Ubuntu), no GPU |
| network | data.ilastik.org, files.ilastik.org and conda.anaconda.org all reachable (HTTP 200) from the start |

## Outcome

**PASS.** The full pipeline (`scripts/run_all.sh`, steps 0–6 plus compression) ran headless, with no code
changes and exit code 0, and produced the final tracking labels for both ilastik versions. Object, track
and lineage counts are identical to the committed results. The ilastik 1.5.0a3 label images are
bit-identical to the committed ones. In ilastik 1.3.3post3, the lineage numbers and the pixels inside
merged objects differ from the committed run (details below), so `results/version_comparison.txt` does
**not** reproduce exactly.

Final labels:
`results/ilastik-1.3.3post3/03_tracking/mitocheck_94570_2D+t_01-53-volume-data_Tracking-Result.h5`
(plus the 1.5.0a3 equivalent).

## What I did

1. Cloned the repo, created branch `repro/opus-5.5-high`.
2. To make sure nothing committed was reused, copied the committed `results/` and `logs/` to a scratch
   folder outside the repo (used only for the comparison afterwards), then deleted `results/` and
   `logs/ilastik-*` from the working tree.
3. Ran `scripts/00_download_data.sh` explicitly. `run_all.sh` skips the download when the data is
   already in the repo, which it is. The zip downloaded and passed the sha256 check, and the unzipped
   files were byte-identical to the committed `data/` (git showed no change).
4. Ran `scripts/run_all.sh` unchanged: installed ilastik 1.3.3post3 (official binary, sha256 OK) and
   1.5.0a3 (micromamba, ilastik-forge), then pixel classification, tracking and previews for both
   versions, the version comparison, the side-by-side GIF, and compression/splitting.
5. Ran `scripts/check_results.py` (the CI consistency check) and my own comparison scripts against the
   committed results (`repro_logs/compare/`).

## Steps

| step | script | result | time |
|---|---|---|---|
| 0 download data | `00_download_data.sh` | PASS (sha256 OK; extracted files identical to committed) | 6.5 s |
| 1 install ilastik 1.3.3post3 + 1.5.0a3 | `01_install_ilastik.sh` | PASS | ~3 min (08:43–08:46, from file times) |
| 2 pixel classification, 1.3.3post3 | `02_pixel_classification.sh` | PASS | 1 m 04 s |
| 3 tracking, 1.3.3post3 (4 exports) | `03_tracking.sh` | PASS | 3 m 10 s (47 + 47 + 46 + 50 s) |
| 4 previews, 1.3.3post3 | `04_make_previews.py` | PASS | <10 s |
| 2 pixel classification, 1.5.0a3 | `02_pixel_classification.sh` | PASS | 57 s |
| 3 tracking, 1.5.0a3 (4 exports) | `03_tracking.sh` | PASS | 2 m 13 s (33 + 33 + 34 + 33 s) |
| 4 previews, 1.5.0a3 | `04_make_previews.py` | PASS | <10 s |
| 5 version comparison | `05_compare_versions.py` | ran; output **differs** from committed (see below) | — |
| 6 side-by-side GIF | `06_side_by_side_gif.py` | PASS | ~16 s (file times 08:54:04 → 08:54:20) |
| compress + split | `compress_h5.py`, `split_join_h5.py` | PASS | ~19 min (08:54:20 → 09:13:40, from file times) |
| consistency check | `check_results.py` | PASS ("all checks passed") | — |

## Wall-clock time

- `run_all.sh`: **30 min 59 s** (`time`: real 30m58.8s, user 36m33.6s, sys 3m25.8s).
- Whole task, from cloning to the report: 08:41:52 → about 09:20 UTC, **≈ 38 min**.
- The ilastik runs themselves took about 7.5 min in total. About 19 min went to
  losslessly compressing and splitting the HDF5 files for git.

## Errors and help needed

- **No errors.** None of the walls described in the README (blocked network, conda solver,
  `size_range` KeyError, label axis order) came up, because the committed scripts already contain the
  fixes. The only warnings were micromamba's routine notices about post-link scripts (`pyopengl`).
- **No help from you was needed.** The network was already open; nothing was asked.

## Comparison with the committed results

Scripts and full output: `repro_logs/compare/` (run them as
`python -I repro_logs/compare/cmpN.py results <folder with the committed results/>`).

### Counts: identical

`04_previews/summary.txt` is byte-identical to the committed file for both versions:
7485 objects, 357 tracks, 117 lineages, 328 untracked objects, 240 tracks starting at a division,
166 objects in merger regions, 80–232 objects per frame.

### ilastik 1.5.0a3: identical

- Probability maps (both split halves): byte-identical (git shows no change).
- Tracking-Result, Object-Identities, Merger-Result: every pixel is equal.
- CSV table: same rows and values. Only the order of the feature **columns** differs. [Inference] The
  plugin probably writes the feature columns in a non-fixed order, e.g. from a set or dictionary.
- Previews: byte-identical.

### ilastik 1.3.3post3: same segmentation, different numbering inside merged objects

- Probability maps: byte-identical. Pixel classification reproduced exactly.
- Foreground masks of all three label images are identical (same 3,605,410 labelled pixels).
- **Tracking-Result**: 57,881 pixels have a different value, in two groups:
  - 57,784 px: lineages **117 and 118 swapped numbers** (every 117 is now 118 and vice versa). Same
    cells, different lineage ID.
  - 97 px, frames 44–47: lineages 53 and 65 trade some pixels. All 97 lie inside merged objects
    (Merger-Result > 0).
- **Object-Identities**: 45,235 differing pixels, **all inside merged objects**. In 19 frames, one object
  ID in the new run covers pixels that had two IDs in the committed run. That means the merger
  resolution split those blobs differently, not just under a new number.
- **CSV**: 190 of 7,485 rows differ after aligning columns by name (IDs and/or shape features of
  merger-split objects).
- [Inference] The cause is likely that ilastik 1.3.3post3's merger resolution (which splits a blob
  containing several touching nuclei into single cells) is not deterministic between runs, e.g. a
  random initialisation when it fits the cells. I did not verify this in the ilastik source. The 1.5.0a3
  run, which uses the same inputs, came out identical, which fits but does not prove this.
  [Unverified] One rerun per version is not enough to say how often each version varies.

### `results/version_comparison.txt`

```diff
-  pixels whose Tracking-Result value differs: 161 of 3605410 labelled pixels (0.0045%); per frame min 0, median 1, max 62
-  label values whose main overlap in the other run has the same number: 118 of 118
+  pixels whose Tracking-Result value differs: 57822 of 3605410 labelled pixels (1.6038%); per frame min 322, median 1049, max 1606
+  label values whose main overlap in the other run has the same number: 116 of 118
```

All other lines are identical, including the probability agreement (99.9888%), cell IoU (99.7757%),
the 0.120 maximum probability difference between versions, the counts, the 114 of 118 strict
one-to-one matches, and the 24 pixels labelled in only one version.

The jump from 161 to 57,822 differing pixels is almost entirely the 117↔118 swap in the 1.3.3post3 run.
After swapping those two numbers back, the new 1.3.3post3 differs from the new 1.5.0a3 in **69 pixels**,
versus 161 in the committed pair. So the README claim "Lineage numbers are the same in both runs" held
in the committed run but **not in this rerun** (two of 118 lineages swapped numbers). Consequence: in
the regenerated `results/side_by_side_tracking.gif`, those two lineages have different colours in the
two panels and are circled as differences throughout.

A CI run on this branch will fail its "`05_compare_versions.py` must reproduce
`version_comparison.txt` exactly" check against the **committed** text. On this branch the committed
text is the regenerated one, so it passes as long as the Python helpers give the same output.

### How the comparison numbers are computed (plain language)

- **"Differing pixels"** (`cmp.py`): the two label images are laid on top of each other and the pixels
  whose numbers differ are counted. Same cells with different numbers count as different.
- **"Swap"** (`cmp.py`, `cmp2.py`): for each differing pixel I record the pair (new number, old number).
  To count pairs quickly, a pair is packed into one number, `new × 1,000,000 + old`. It is unpacked with
  integer division (`// 1,000,000` gives `new`) and remainder (`% 1,000,000` gives `old`). The most
  common pairs were (117, 118) and (118, 117), which means the two numbers were exchanged.
- **"One-to-one per frame"** (`cmp2.py`, `cmp3.py`): within each frame I list every (new ID, old ID)
  pair that occurs on the same pixel. If each new ID appears with exactly one old ID and the reverse,
  the two runs drew the same objects and only renumbered them. A new ID that appears with two old IDs
  means the object outlines themselves changed.
- **"Inside merged objects"** (`cmp4.py`): the differing pixels are checked against Merger-Result, which
  is non-zero only where ilastik detected several touching cells as one blob.

## Files added on this branch

- `REPRO_REPORT.md`: this report.
- `repro_logs/run_all.log`: full output of `run_all.sh`; `repro_logs/00_download.log`.
- `repro_logs/compare/`: comparison scripts and their output.
- `results/`, `logs/`: regenerated by the pipeline. Git records changes only where bytes differ:
  1.3.3post3 tracking outputs, CSVs, 1.3.3post3 previews, the side-by-side GIF,
  `version_comparison.txt`, and the ilastik logs (timestamps). Everything else in `results/` came out
  byte-identical to `main`.
