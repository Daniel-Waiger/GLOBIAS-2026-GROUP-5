#!/usr/bin/env bash
# Step 3: Automatic (Conservation) Tracking with the shipped conservationTracking.ilp (2014), headless.
# Inputs: raw movie + the step-2 probabilities. The project's own object-count and division
# classifiers (trained in 2014 on the shipped _export.h5 probabilities) are reused as-is.
# Outputs (03_tracking/):
#   *_Tracking-Result.h5    final labels: each pixel = lineage id (0 = background)
#   *_Object-Identities.h5  per-frame object (segment) ids, = labelimageId in the CSV
#   *_Merger-Result.h5      objects detected as merged cells
#   *_CSV-Table.csv.csv     one row per object: frame, ids, track, lineage, parent, features
# usage: scripts/03_tracking.sh 1.3.3post3|1.5.0a3
set -euo pipefail
source scripts/env.sh "$1"
OUT="$RUN/03_tracking"
mkdir -p "$OUT"
cp "$DATA/conservationTracking.ilp" "$OUT/conservationTracking_run.ilp"
# The project needs its original inputs next to it to open (relative paths stored in the .ilp).
ln -sfn "../../../$RAW" "$OUT/$(basename "$RAW")"
ln -sfn "../../../$DATA/mitocheck_94570_2D+t_01-53_export.h5" "$OUT/mitocheck_94570_2D+t_01-53_export.h5"
"$PY" scripts/fix_legacy_tracking_params.py "$OUT/conservationTracking_run.ilp" > "$LOGS/03_fix_legacy_tracking_params.log"
for SRC in Tracking-Result Object-Identities Merger-Result Plugin; do
  if [ "$SRC" = Plugin ]; then
    FMT=(--export_plugin=CSV-Table --output_filename_format="$OUT/{nickname}_CSV-Table.csv")
  else
    FMT=(--output_format=hdf5 --output_filename_format="$OUT/{nickname}_$SRC.h5")
  fi
  { time "$ILASTIK" --headless --project="$OUT/conservationTracking_run.ilp" \
      --raw_data="$RAW/volume/data" --prediction_maps="$PMAPS/exported_data" \
      --export_source="$SRC" "${FMT[@]}" ; } > "$LOGS/03_tracking_$SRC.log" 2>&1
done
