# Shared settings, sourced by the step scripts. Usage: source scripts/env.sh <ilastik-version>
VERSION="$1"
WORK="${WORK:-$PWD/.work}"
PY="$WORK/mamba/envs/ilastik/bin/python"          # helper scripts (h5py, numpy, matplotlib)
case "$VERSION" in
  1.3.3post3) ILASTIK="$WORK/il133/ilastik-1.3.3post3-Linux/run_ilastik.sh" ;;
  1.5.0a3)    ILASTIK="$WORK/mamba/envs/ilastik/bin/ilastik" ;;
  *) echo "unknown ilastik version: $VERSION" >&2; exit 1 ;;
esac
RUN="results/ilastik-$VERSION"
LOGS="logs/ilastik-$VERSION"
DATA="data/mitocheck_2d+t"
RAW="$DATA/mitocheck_94570_2D+t_01-53.h5"
PMAPS="$RUN/02_pixel_classification/mitocheck_94570_2D+t_01-53-volume-data_Probabilities.h5"
# Threads and RAM for ilastik; override from the environment on smaller machines (e.g. CI).
export QT_QPA_PLATFORM=offscreen LAZYFLOW_THREADS="${LAZYFLOW_THREADS:-4}" LAZYFLOW_TOTAL_RAM_MB="${LAZYFLOW_TOTAL_RAM_MB:-12000}"
mkdir -p "$RUN" "$LOGS"
