#!/usr/bin/env bash
# Step 1: install ilastik (headless use) into a micromamba environment.
# ilastik.org installers are not reachable from the cloud sandbox, so ilastik is
# installed from the ilastik-forge + conda-forge conda channels instead.
# ilastik 1.4.1 (stable) no longer resolves against current channels; 1.5.0a3 does.
set -euo pipefail
WORK="${WORK:-$PWD/.work}"
mkdir -p "$WORK/mm"
export MAMBA_ROOT_PREFIX="$WORK/mamba"

if [ ! -x "$WORK/mm/bin/micromamba" ]; then
  curl -sL https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.9.0-0.tar.bz2 \
    | tar xj -C "$WORK/mm" bin/micromamba
fi

"$WORK/mm/bin/micromamba" create -y -n ilastik \
  -c ilastik-forge -c conda-forge --override-channels \
  "ilastik=1.5.0a3"
