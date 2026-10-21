#!/usr/bin/env bash
# Step 1: install the two ilastik versions used here into .work/ (not committed).
#  - ilastik 1.3.3post3: official Linux binary (files.ilastik.org). Main run; it opens the
#    2014 MitoCheck projects with the fewest changes. (1.3.1 is not in ilastik's download
#    archive. 1.3.2post1 fails here: its bundled fast-filters library does not load on current
#    glibc, and the fallback code path has a bug for 2D data; see docs/REFERENCE.md.)
#  - ilastik 1.5.0a3: from the ilastik-forge conda channel, for comparison. (1.4.1 no longer
#    resolves against the current conda channels.)
set -euo pipefail
WORK="${WORK:-$PWD/.work}"
mkdir -p "$WORK/mm" "$WORK/il133"

if [ ! -x "$WORK/il133/ilastik-1.3.3post3-Linux/run_ilastik.sh" ]; then
  curl -sS -o "$WORK/il133.tar.bz2" https://files.ilastik.org/ilastik-1.3.3post3-Linux.tar.bz2
  echo "cfd208eb3e94c747c26991ea8ead199b1f8a1a44ab05a8f85c8c80f8dd392a4c  $WORK/il133.tar.bz2" | sha256sum -c
  tar xjf "$WORK/il133.tar.bz2" -C "$WORK/il133"
fi

export MAMBA_ROOT_PREFIX="$WORK/mamba"
if [ ! -x "$WORK/mm/bin/micromamba" ]; then
  curl -sL https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.9.0-0.tar.bz2 \
    | tar xj -C "$WORK/mm" bin/micromamba
fi
if [ ! -x "$MAMBA_ROOT_PREFIX/envs/ilastik/bin/ilastik" ]; then
  "$WORK/mm/bin/micromamba" create -y -n ilastik \
    -c ilastik-forge -c conda-forge --override-channels "ilastik=1.5.0a3"
fi
