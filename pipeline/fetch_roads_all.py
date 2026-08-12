# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "pyarrow", "pandas"]
# ///
"""fetch_roads_all.py -- all TIGER roads for Nevada (every MTFCC class,
including S1400 local and S1500 vehicular trail / 4WD), county by county,
merged and staged as EPSG:5070 GeoParquet.

Output: data-local/vectors/nv_roads_all_5070.parquet
"""
import io, tempfile, urllib.request, zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data-local/vectors"
FIPS = ["001", "003", "005", "007", "009", "011", "013", "015", "017",
        "019", "021", "023", "027", "029", "031", "033", "510"]

frames = []
import time
def fetch(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return io.BytesIO(r.read())
        except Exception as e:
            if i == tries - 1: raise
            print(f"  retry {i+1} after {e}", flush=True)
            time.sleep(10 * (i + 1))

for f in FIPS:
    url = f"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_32{f}_roads.zip"
    buf = fetch(url)
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(buf).extractall(td)
        shp = next(Path(td).glob("*.shp"))
        frames.append(gpd.read_file(shp))
    print(f"32{f}: {len(frames[-1])} features", flush=True)

roads = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs).to_crs("EPSG:5070")
roads.to_parquet(OUT / "nv_roads_all_5070.parquet")
print(f"TOTAL: {len(roads)} features | MTFCC classes: {sorted(roads.MTFCC.unique())}")
print("ROADS_ALL_COMPLETE")
