#!/usr/bin/env bash
# Step 0: download and unpack the ilastik MitoCheck example (needs data.ilastik.org network access).
# The zip itself (118 MB) is not committed: GitHub rejects files > 100 MB. Its contents are.
set -euo pipefail
mkdir -p data
curl -sS -o data/mitocheck.zip https://data.ilastik.org/mitocheck.zip
echo "70d8efbae178a34df130d226c6c6af13f086bc94858cc0e79a65f7a932d8920e  data/mitocheck.zip" | sha256sum -c
unzip -q -o data/mitocheck.zip -d data
