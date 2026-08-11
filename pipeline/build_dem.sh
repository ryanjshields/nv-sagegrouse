#!/usr/bin/env bash
# build_dem.sh -- mosaic 3DEP COG tiles into an analysis-ready DEM + terrain derivative COGs.
#
# Input:  data-local/dem/tiles/*.tif   (from fetch_tnm.py URL list)
# Output: data-local/dem/nv_dem_5070.tif        30 m, EPSG:5070, COG
#         data-local/dem/nv_{slope,aspect,tri}_5070.tif   COGs via gdaldem
#
# Curvature is computed separately (GRASS r.slope.aspect) -- see pipeline notes:
# ArcGIS "Curvature" and GRASS profile/tangential curvature differ by sign/scale
# convention; the equivalence choice is documented in the findings report.
set -euo pipefail
cd "$(dirname "$0")/.."
DEM_DIR=data-local/dem
COG_OPTS=(-of COG -co COMPRESS=DEFLATE -co PREDICTOR=2 -co NUM_THREADS=ALL_CPUS -co BIGTIFF=IF_SAFER)

echo "[1/5] VRT over $(ls "$DEM_DIR"/tiles/*.tif | wc -l | tr -d ' ') tiles"
gdalbuildvrt -overwrite "$DEM_DIR/nv_dem.vrt" "$DEM_DIR"/tiles/*.tif

echo "[2/5] Warp to EPSG:5070 @ 30 m (COG)"
gdalwarp -overwrite -t_srs EPSG:5070 -tr 30 30 -r bilinear \
  -multi -wo NUM_THREADS=ALL_CPUS "${COG_OPTS[@]}" \
  "$DEM_DIR/nv_dem.vrt" "$DEM_DIR/nv_dem_5070.tif"

echo "[3/5] Slope (degrees)"
gdaldem slope "$DEM_DIR/nv_dem_5070.tif" "$DEM_DIR/nv_slope_5070.tif" "${COG_OPTS[@]}"

echo "[4/5] Aspect (degrees, 0-360)"
gdaldem aspect "$DEM_DIR/nv_dem_5070.tif" "$DEM_DIR/nv_aspect_5070.tif" -zero_for_flat "${COG_OPTS[@]}"

echo "[5/5] TRI (Riley, 3x3 = 90 m window)"
gdaldem TRI "$DEM_DIR/nv_dem_5070.tif" "$DEM_DIR/nv_tri_5070.tif" -alg Riley "${COG_OPTS[@]}"

echo "DEM_BUILD_COMPLETE"; ls -lh "$DEM_DIR"/nv_*_5070.tif | awk '{print $9, $5}'
