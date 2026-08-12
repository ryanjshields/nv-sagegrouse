#!/usr/bin/env bash
# smoke_test.sh -- CI-safe pipeline smoke test. Public data only, one-tile AOI
# (no lek data in CI). Exercises: TNM fetch + vintage dedup, mosaic/warp,
# terrain derivatives, VRM math, and sanity assertions on the outputs.
set -euo pipefail
cd "$(dirname "$0")/.."
SMOKE=data-local/smoke
mkdir -p "$SMOKE/tiles"

echo "[1/4] fetch one 3DEP tile (Elko-area AOI)"
python3 pipeline/fetch_tnm.py \
  --dataset "National Elevation Dataset (NED) 1 arc-second" \
  --bbox="-115.9,40.1,-115.2,40.9" --manifest "$SMOKE/manifest.json" > "$SMOKE/urls.txt"
head -2 "$SMOKE/urls.txt" | xargs -I{} curl -sL -O --output-dir "$SMOKE/tiles" {}

echo "[2/4] mosaic + warp + derivatives"
gdalbuildvrt -overwrite "$SMOKE/dem.vrt" "$SMOKE"/tiles/*.tif
gdalwarp -overwrite -t_srs EPSG:5070 -tr 30 30 -r bilinear \
  "$SMOKE/dem.vrt" "$SMOKE/nv_dem_5070.tif"
gdaldem slope "$SMOKE/nv_dem_5070.tif" "$SMOKE/nv_slope_5070.tif"
gdaldem aspect "$SMOKE/nv_dem_5070.tif" "$SMOKE/nv_aspect_5070.tif" -zero_for_flat

echo "[3/4] VRM on the smoke grid"
SMOKE_DIR="$SMOKE" uv run - <<'PY'
import os
from pathlib import Path
import numpy as np, rasterio
from scipy.ndimage import uniform_filter
S = Path(os.environ["SMOKE_DIR"])
with rasterio.open(S/"nv_slope_5070.tif") as s, rasterio.open(S/"nv_aspect_5070.tif") as a:
    slope = np.deg2rad(s.read(1).astype("float64"))
    aspect = np.deg2rad(a.read(1).astype("float64"))
xy = np.sin(slope)
x, y, z = xy*np.sin(aspect), xy*np.cos(aspect), np.cos(slope)
rx, ry, rz = (uniform_filter(c, 3, mode="nearest") for c in (x, y, z))
vrm = 1.0 - np.sqrt(rx**2 + ry**2 + rz**2)
assert np.nanmin(vrm) >= -1e-9 and np.nanmax(vrm) <= 1.0, "VRM out of [0,1]"
assert 0.0 < np.nanmean(vrm) < 0.05, f"VRM mean implausible: {np.nanmean(vrm)}"
print(f"VRM mean {np.nanmean(vrm):.5f} max {np.nanmax(vrm):.4f} -- OK")
PY

echo "[4/4] sanity: DEM stats in Great Basin range"
python3 - <<'PY'
import json, subprocess, sys
j = json.loads(subprocess.check_output(
    ["gdalinfo", "-json", "-stats", "data-local/smoke/nv_dem_5070.tif"]))
b = j["bands"][0]
mn, mx = b["minimum"], b["maximum"]
assert 500 < mn < 3000 and 1500 < mx < 4500, f"elevation range implausible: {mn}-{mx}"
print(f"DEM {mn:.0f}-{mx:.0f} m -- OK")
PY
echo "SMOKE_OK"
