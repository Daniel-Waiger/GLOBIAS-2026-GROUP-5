#!/usr/bin/env bash
# Full pipeline: download, install, then for each ilastik version pixel classification -> tracking ->
# previews; finally compress/split the large HDF5 files for git and compare the two versions.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f "data/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5" ] || scripts/00_download_data.sh
scripts/01_install_ilastik.sh
PY=.work/mamba/envs/ilastik/bin/python
for V in 1.3.3post3 1.5.0a3; do
  scripts/02_pixel_classification.sh "$V"
  scripts/03_tracking.sh "$V"
  "$PY" scripts/04_make_previews.py "results/ilastik-$V"
done
"$PY" scripts/05_compare_versions.py > results/version_comparison.txt
for V in 1.3.3post3 1.5.0a3; do
  "$PY" scripts/compress_h5.py results/ilastik-$V/0[23]_*/*-volume-data_*.h5
  "$PY" scripts/split_join_h5.py split results/ilastik-$V/02_pixel_classification/*_Probabilities.h5
done
