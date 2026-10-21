#!/usr/bin/env bash
# Step 2: apply the shipped, pre-trained pixelClassification.ilp (2014) headlessly to the movie.
# Output: per-pixel probabilities, channel 0 = background, channel 1 = cell nucleus (0..1).
# usage: scripts/02_pixel_classification.sh 1.3.3post3|1.5.0a3
set -euo pipefail
source scripts/env.sh "$1"
OUT="$RUN/02_pixel_classification"
mkdir -p "$OUT"
# Work on a copy: headless ilastik opens projects writable and may upgrade them.
cp "$DATA/pixelClassification.ilp" "$OUT/pixelClassification_run.ilp"
# The project references its raw data by a path relative to the .ilp, so link it alongside.
ln -sfn "../../../$RAW" "$OUT/$(basename "$RAW")"
if [ "$VERSION" = 1.5.0a3 ]; then
  # Legacy labels are stored t,x,y,c; ilastik 1.5 expects t,y,x,c.
  "$PY" scripts/fix_legacy_labels.py "$OUT/pixelClassification_run.ilp" > "$LOGS/02_fix_legacy_labels.log"
fi
{ time "$ILASTIK" --headless \
    --project="$OUT/pixelClassification_run.ilp" \
    --export_source="Probabilities" --output_format=hdf5 \
    --output_filename_format="$OUT/{nickname}_Probabilities.h5" \
    "$RAW/volume/data" ; } > "$LOGS/02_pixel_classification.log" 2>&1
