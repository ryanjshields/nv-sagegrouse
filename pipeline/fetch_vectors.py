# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "pyarrow"]
# ///
"""fetch_vectors.py -- fetch all vector inputs and stage them as GeoParquet.

Sources (resolved at run time, no hardcoded file URLs):
  - USFWS 2015 Status Review sage-grouse Current Range  (ScienceBase item API)
  - Census TIGER NV primary/secondary roads
  - Census cartographic state boundaries (NV extracted)

Outputs -> data-local/vectors/  (all EPSG:5070 GeoParquet)
  grsg_range_2015.parquet      full range polygon
  nv_boundary.parquet          Nevada state boundary
  grsg_range_nv_5070.parquet   range clipped to Nevada  (study-area basis)
  nv_prisecroads_5070.parquet  TIGER primary/secondary roads

Run:  uv run pipeline/fetch_vectors.py
"""
import io, json, tempfile, urllib.request, zipfile
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data-local/vectors"
OUT.mkdir(parents=True, exist_ok=True)

SB_ITEM = "56f96693e4b0a6037df06034"  # GRSG 2015 USFWS Status Review Current Range
TIGER_ROADS = "https://www2.census.gov/geo/tiger/TIGER2024/PRISECROADS/tl_2024_32_prisecroads.zip"
STATES = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_500k.zip"

def fetch_zip_gdf(url: str) -> gpd.GeoDataFrame:
    with urllib.request.urlopen(url, timeout=300) as r:
        buf = io.BytesIO(r.read())
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(buf).extractall(td)
        shp = next(Path(td).glob("**/*.shp"))
        return gpd.read_file(shp)

def sciencebase_zip_url(item: str) -> str:
    api = f"https://www.sciencebase.gov/catalog/item/{item}?format=json&fields=files"
    with urllib.request.urlopen(api, timeout=120) as r:
        files = json.load(r).get("files", [])
    zips = [f for f in files if f.get("name", "").lower().endswith(".zip")]
    if not zips:
        raise SystemExit(f"no zip attached to ScienceBase item {item}")
    return zips[0]["url"]

print("fetching USFWS 2015 range from ScienceBase ...")
rng = fetch_zip_gdf(sciencebase_zip_url(SB_ITEM)).to_crs("EPSG:5070")
rng.to_parquet(OUT / "grsg_range_2015.parquet")

print("fetching state boundaries ...")
states = fetch_zip_gdf(STATES).to_crs("EPSG:5070")
nv = states[states["STUSPS"] == "NV"]
nv.to_parquet(OUT / "nv_boundary.parquet")

print("clipping range to Nevada ...")
rng_nv = gpd.clip(rng, nv)
rng_nv.to_parquet(OUT / "grsg_range_nv_5070.parquet")

print("fetching TIGER NV primary/secondary roads ...")
roads = fetch_zip_gdf(TIGER_ROADS).to_crs("EPSG:5070")
roads.to_parquet(OUT / "nv_prisecroads_5070.parquet")

km2 = rng_nv.union_all().area / 1e6
print(f"range-in-NV area: {km2:,.0f} km2 | roads: {len(roads)} features")
print("VECTORS_COMPLETE")
