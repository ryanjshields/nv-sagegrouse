#!/usr/bin/env bash
# build_roads_raster.sh -- Euclidean distance-to-road surface on the DEM grid.
#
# All TIGER roads (every MTFCC class) are rasterized at 90 m and distance is
# computed there, then bilinearly resampled to the 30-m DEM grid. Distance
# fields are smooth; the approximation error is bounded by ~1 cell of the
# compute grid (90 m) on a variable whose observed range spans kilometers.
# Output: data-local/dem/nv_distroad_5070.tif (COG, meters)
set -euo pipefail
cd "$(dirname "$0")/.."
D=data-local
TE=$(python3 -c "
import json,subprocess
j=json.loads(subprocess.check_output(['gdalinfo','-json','$D/dem/nv_dem_5070.tif']))
cc=j['cornerCoordinates']; print(f\"{cc['upperLeft'][0]} {cc['lowerRight'][1]} {cc['lowerRight'][0]} {cc['upperLeft'][1]}\")")

uv run --with geopandas,pyogrio,pyarrow python3 -c "import geopandas as gpd; gpd.read_parquet('$D/vectors/nv_roads_all_5070.parquet').to_file('/tmp/nv_roads_all.gpkg', driver='GPKG')"
gdal_rasterize -burn 1 -tr 90 90 -te $TE -ot Byte -init 0 \
  /tmp/nv_roads_all.gpkg "$D/dem/_roads90.tif"
gdal_proximity "$D/dem/_roads90.tif" "$D/dem/_dist90.tif" -distunits GEO -ot Float32 2>/dev/null \
  || gdal_proximity.py "$D/dem/_roads90.tif" "$D/dem/_dist90.tif" -distunits GEO -ot Float32
gdalwarp -overwrite -tr 30 30 -te $TE -r bilinear -of COG \
  -co COMPRESS=DEFLATE -co NUM_THREADS=ALL_CPUS -co BIGTIFF=IF_SAFER \
  "$D/dem/_dist90.tif" "$D/dem/nv_distroad_5070.tif"
rm -f "$D/dem/_roads90.tif" "$D/dem/_dist90.tif"
echo "DISTROAD_COMPLETE"
