#!/usr/bin/env bash
# build_roads_by_class.sh -- class-specific Euclidean distance surfaces.
#   paved:   MTFCC S1100 (primary), S1200 (secondary), S1630 (ramps)
#   unpaved: MTFCC S1400 (local/neighborhood), S1500 (vehicular trail / 4WD)
# Same 90-m-compute -> 30-m-resample approach as build_roads_raster.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
D=data-local
TE="-2266193.922 1353823.079 -1371023.922 2488033.079"

uv run --with geopandas,pyogrio,pyarrow python3 - <<'PY'
import geopandas as gpd
r = gpd.read_parquet("data-local/vectors/nv_roads_all_5070.parquet")
r[r.MTFCC.isin(["S1100","S1200","S1630"])].to_file("/tmp/nv_roads_paved.gpkg", driver="GPKG")
r[r.MTFCC.isin(["S1400","S1500"])].to_file("/tmp/nv_roads_unpaved.gpkg", driver="GPKG")
print("paved:", (r.MTFCC.isin(["S1100","S1200","S1630"])).sum(),
      "| unpaved:", (r.MTFCC.isin(["S1400","S1500"])).sum())
PY

for cls in paved unpaved; do
  gdal_rasterize -burn 1 -tr 90 90 -te $TE -ot Byte -init 0 "/tmp/nv_roads_${cls}.gpkg" "$D/dem/_r90.tif"
  gdal_proximity "$D/dem/_r90.tif" "$D/dem/_d90.tif" -distunits GEO -ot Float32 2>/dev/null \
    || gdal_proximity.py "$D/dem/_r90.tif" "$D/dem/_d90.tif" -distunits GEO -ot Float32
  gdalwarp -overwrite -tr 30 30 -te $TE -r bilinear -of COG \
    -co COMPRESS=DEFLATE -co NUM_THREADS=ALL_CPUS -co BIGTIFF=IF_SAFER \
    "$D/dem/_d90.tif" "$D/dem/nv_distroad_${cls}_5070.tif"
  rm -f "$D/dem/_r90.tif" "$D/dem/_d90.tif"
  echo "${cls}_DONE"
done
echo "ROAD_CLASS_SURFACES_COMPLETE"
