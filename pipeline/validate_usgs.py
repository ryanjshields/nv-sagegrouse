# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "pyproj", "tabulate"]
# ///
"""validate_usgs.py -- external correlation of the v4 surface against the USGS
sage-grouse habitat-selection rasters (Coates-lab products; ScienceBase item
65f37677d34e9853bbf0db38, ver. 3.0, Sept 2025).

Discovers the item's files at runtime, picks a habitat-selection raster,
samples it and our surface at a common set of seeded random points in the
study area (via /vsicurl range reads -- no full download), and reports
Spearman correlation. Writes reports/v4/usgs_validation.txt
"""
import json, sys, urllib.request
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from pathlib import Path
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
ITEM = "65f389f9d34e9853bbf0e813"

api = f"https://www.sciencebase.gov/catalog/item/{ITEM}?format=json&fields=files"
with urllib.request.urlopen(api, timeout=120) as r:
    files = json.load(r).get("files", [])
tifs = [f for f in files if f.get("name", "").lower().endswith((".tif", ".tiff", ".img", ".zip"))]
print("candidate files:")
for f in tifs[:40]:
    print("  ", f.get("name"), f.get("size"))

def pick(files):
    scored = []
    for f in files:
        n = f.get("name", "").lower()
        if not n.endswith((".tif", ".tiff")):
            continue
        score = ("select" in n) * 4 + ("hsi" in n) * 3 + ("breed" in n or "spring" in n) * 2 - ("surv" in n) * 3 - ("space" in n)
        scored.append((score, f))
    scored.sort(key=lambda t: -t[0])
    return scored[0][1] if scored else None

target = pick(tifs)
if target is None:
    sys.exit("no directly readable .tif candidate; inspect the file list above (may be zipped)")
print("selected:", target["name"])
local = D / "usgs" / target["name"]
local.parent.mkdir(parents=True, exist_ok=True)
if not local.exists():
    urllib.request.urlretrieve(target["url"], local)
url = str(local)

sa = gpd.read_file(D / "design/study_area_5070.gpkg")
pts = sa.sample_points(150_000, rng=99).explode(index_parts=False)
x5, y5 = pts.x.values, pts.y.values

with rasterio.open(D / "dem/nv_prediction_v4_5070.tif") as src:
    ours = np.array([v[0] for v in src.sample(zip(x5, y5))], dtype="float64")

with rasterio.open(url) as src:
    tr = Transformer.from_crs(5070, src.crs, always_xy=True)
    xt, yt = tr.transform(x5, y5)
    theirs = np.array([v[0] for v in src.sample(zip(xt, yt))], dtype="float64")
    nod = src.nodata

ok = np.isfinite(ours) & (ours >= 0) & np.isfinite(theirs)
if nod is not None:
    ok &= theirs != nod
ours, theirs = ours[ok], theirs[ok]
rank = lambda a: pd.Series(a).rank().values
rho = float(np.corrcoef(rank(ours), rank(theirs))[0, 1])

# contingency at full resolution: our quantile bin x their category
qs = np.quantile(ours, [0.2, 0.4, 0.6, 0.8])
our_bin = np.digitize(ours, qs)
cats = sorted(int(c) for c in np.unique(theirs))
labels5 = ["very low", "low", "moderate", "high", "very high"]
tab = np.zeros((len(cats), 5))
for i, c in enumerate(cats):
    for j in range(5):
        tab[i, j] = np.sum((theirs == c) & (our_bin == j))
tab = tab / tab.sum(axis=1, keepdims=True)
cdf = pd.DataFrame(tab, index=[f"USGS cat {c}" for c in cats],
                   columns=[f"ours {l}" for l in labels5])
(ROOT / "reports/v4/tables").mkdir(parents=True, exist_ok=True)
with open(ROOT / "reports/v4/tables/usgs_contingency.md", "w") as f:
    f.write(cdf.map(lambda x: f"{x:.0%}").to_markdown() + "\n")
msg = (f"USGS raster: {target['name']}\n"
       f"common valid points: {len(ours):,} of 150,000\n"
       f"Spearman(ours, USGS): {rho:.3f}\n")
(ROOT / "reports/v4").mkdir(parents=True, exist_ok=True)
open(ROOT / "reports/v4/usgs_validation.txt", "w").write(msg)
print(msg)
print("USGS_VALIDATION_COMPLETE")
