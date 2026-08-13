# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "pyarrow", "pandas", "pyogrio", "geopandas>=1.0"]
# ///
"""extract_covariates.py -- sample all covariate rasters at the design points.

Reads  data-local/design/design_points.parquet  (x, y in EPSG:5070, use 0/1)
Writes data-local/design/model_input.parquet with columns:
  use, elevation, slope, aspect_deg, direction (8-way bin), tri, curvature,
  evt_phys (string), dist_road_m

Aspect binning matches the 2023 R code (22.5-degree wedges, N wraps).
Distance-to-road is computed against TIGER NV primary/secondary roads.
"""
import geopandas as gpd
import pandas as pd
import rasterio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"

pts = pd.read_parquet(D / "design/design_points.parquet")
xy = list(zip(pts.x, pts.y))

def sample(path):
    with rasterio.open(path) as src:
        return [v[0] for v in src.sample(xy)]

pts["elevation"] = sample(D / "dem/nv_dem_5070.tif")
pts["slope"] = sample(D / "dem/nv_slope_5070.tif")
pts["aspect_deg"] = sample(D / "dem/nv_aspect_5070.tif")
# Ruggedness = VRM (Sappington et al. 2007), v4 canonical. Legacy options kept
# as rasters: nv_rugg_5070.tif (manuscript Eq. 1) and nv_tri_5070.tif (Riley --
# do NOT model with it; ~0.995 correlated with slope).
pts["tri"] = sample(D / "dem/nv_vrm_5070.tif")
pts["curvature"] = sample(D / "dem/nv_curv_5070.tif")

import numpy as _np

# Ingestion gate (FINDINGS F3/F4/F11): nodata must never enter the design
# table. A -9999 aspect would classify as "N", a -9999 slope as "Flat", and a
# single sentinel row would shift the z-scaling moments applied to every cell
# of the statewide surface. Reject loudly, per column, at the point of entry.
def reject_invalid(df, cols):
    bad = {c: int(((~_np.isfinite(df[c].astype("float64"))) | (df[c] <= -9998)).sum())
           for c in cols}
    bad = {c: n for c, n in bad.items() if n}
    if bad:
        raise SystemExit(f"INGESTION_GATE_FAILED: sentinel/NaN sampled at design points: {bad}")

reject_invalid(pts, ["elevation", "slope", "aspect_deg", "tri", "curvature"])

def direction(a):
    if a is None or a != a or a < 0:
        raise ValueError(f"invalid aspect {a!r} reached direction(); "
                         "nodata must be caught by the ingestion gate")
    for hi, lab in [(22.5,"N"),(67.5,"NE"),(112.5,"E"),(157.5,"SE"),(202.5,"S"),(247.5,"SW"),(292.5,"W"),(337.5,"NW"),(360.1,"N")]:
        if a <= hi: return lab
    return "N"
# gdaldem -zero_for_flat writes aspect 0 for flat cells, which collides with
# true north. Flat terrain (slope < 0.5 deg) gets its own category -- leks sit
# on flat ground, so folding flat into N would contaminate the aspect effects.
pts["direction"] = _np.where(pts.slope < 0.5, "Flat", pts.aspect_deg.map(direction))

# EVT_PHYS: sample the LANDFIRE grid, then map pixel value -> EVT_PHYS via the CSV attribute table
evt_tifs = sorted((D / "landfire").glob("**/*.tif"))
evt_csvs = sorted((D / "landfire").glob("**/*.csv"))
if evt_tifs:
    with rasterio.open(evt_tifs[0]) as src:
        evt_crs = src.crs
        p5070 = gpd.GeoSeries(gpd.points_from_xy(pts.x, pts.y), crs="EPSG:5070").to_crs(evt_crs)
        pts["evt_val"] = [v[0] for v in src.sample(list(zip(p5070.x, p5070.y)))]
    if evt_csvs:
        att = pd.read_csv(evt_csvs[0])
        vcol = "VALUE" if "VALUE" in att.columns else att.columns[0]
        pcol = next(c for c in att.columns if "PHYS" in c.upper())
        pts["evt_phys"] = pts.evt_val.map(att.set_index(vcol)[pcol])
else:
    print("WARNING: no LANDFIRE tif found -- evt_phys skipped this pass")

# Distance to nearest road (m): sampled from the all-roads Euclidean-distance
# surface (build_roads_raster.sh) so points and prediction grid share one source.
pts["dist_road_m"] = sample(D / "dem/nv_distroad_5070.tif")
reject_invalid(pts, ["dist_road_m"])

out = pts.drop(columns=[c for c in ("evt_val",) if c in pts])
out.to_parquet(D / "design/model_input.parquet", index=False)
out.to_csv(D / "design/model_input.csv", index=False)  # for the R model step
print(f"rows: {len(pts)} | used: {int(pts.use.sum())} | cols: {list(pts.columns)}")
print("EXTRACTION_COMPLETE")
