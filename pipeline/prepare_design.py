# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "pyarrow"]
# ///
"""prepare_design.py -- build the study area and the used/available point design.

Method (McGinn et al., PLOS draft Feb 2024, with documented v4 deltas):
  study area = USFWS 2015 sage-grouse range clipped to NV
               + 5-km buffers around ACTIVE leks falling outside that range
  used       = active leks within Nevada (paper: n=716)
  available  = seeded uniform random points in study area, 10 per used lek

Run:  uv run pipeline/prepare_design.py
Outputs (SENSITIVE -- gitignored, secure-bucket only):
  data-local/design/study_area_5070.gpkg
  data-local/design/design_points.parquet   (x, y in EPSG:5070, use 0/1)
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20260811
RATIO = 10

leks = pd.read_csv(ROOT / "data-local/leks_all.csv")
leks.columns = [c.strip() for c in leks.columns]
active = leks[leks["LEK STATUS"].str.strip().str.lower() == "active"].copy()
g_active = gpd.GeoDataFrame(
    active,
    geometry=gpd.points_from_xy(active["UTME NAD83"], active["UTMN NAD83"]),
    crs="EPSG:26911",
).to_crs("EPSG:5070")

rng_nv = gpd.read_parquet(ROOT / "data-local/vectors/grsg_range_nv_5070.parquet").to_crs("EPSG:5070")
range_union = rng_nv.union_all()

# 5-km buffers around active leks OUTSIDE the range polygon (v4: active-only, per Dec-2023 bug fix)
outside = g_active[~g_active.geometry.within(range_union)]
study_area = range_union
if len(outside):
    study_area = study_area.union(outside.buffer(5000).union_all())
sa = gpd.GeoDataFrame(geometry=[study_area], crs="EPSG:5070")
out_dir = ROOT / "data-local/design"
out_dir.mkdir(parents=True, exist_ok=True)
sa.to_file(out_dir / "study_area_5070.gpkg", driver="GPKG")

used = g_active[g_active["STATE"].str.strip().str.upper() == "NV"]
n_avail = RATIO * len(used)
avail_pts = sa.sample_points(n_avail, rng=SEED).explode(index_parts=False)

design = pd.concat(
    [
        pd.DataFrame({"x": used.geometry.x, "y": used.geometry.y, "use": 1, "lekid": used["LEKID"].values}),
        pd.DataFrame({"x": avail_pts.x.values, "y": avail_pts.y.values, "use": 0, "lekid": None}),
    ],
    ignore_index=True,
)
design.to_parquet(out_dir / "design_points.parquet", index=False)

area_km2 = study_area.area / 1e6
print(f"active leks total: {len(g_active)} | used (NV): {len(used)} | outside-range buffered: {len(outside)}")
print(f"study area: {area_km2:,.0f} km2 | available points: {len(avail_pts)} (seed {SEED})")
print("DESIGN_COMPLETE")
