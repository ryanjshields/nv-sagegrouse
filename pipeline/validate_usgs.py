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

# Pin the expected release filename; the keyword heuristic is only a fallback
# so a ScienceBase rename cannot silently swap the comparison raster.
EXPECTED = "GrSG_Spring_Selection_Categories.tif"

if (D / "usgs" / EXPECTED).exists():
    # Cache-first: the pinned raster is already on disk, so skip ScienceBase
    # discovery entirely (the API 5xxes routinely and is not needed offline).
    target = {"name": EXPECTED}
else:
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

    target = next((f for f in tifs if f.get("name") == EXPECTED), None)
    if target is None:
        target = pick(tifs)
        if target is not None:
            print(f"WARNING: expected '{EXPECTED}' not found in the item file list; "
                  f"keyword heuristic selected '{target['name']}' -- verify before trusting the comparison")
    if target is None:
        sys.exit("no directly readable .tif candidate; inspect the file list above (may be zipped)")
print("selected:", target["name"])
local = D / "usgs" / target["name"]
local.parent.mkdir(parents=True, exist_ok=True)
if not local.exists():
    urllib.request.urlretrieve(target["url"], local)
url = str(local)

sa = gpd.read_file(D / "design/study_area_5070.gpkg")
# rng=99 is deliberately independent of the pipeline design seed (20260811):
# the validation sample must not couple to the availability draw.
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
# official class names from the release's FGDC metadata (percentile classes
# of the HSI: <5th, 5th-25th, 25th-50th, >50th)
USGS_NAMES = {1: "non-habitat", 2: "low habitat", 3: "moderate habitat",
              4: "high habitat"}
cdf = pd.DataFrame(tab, index=[f"USGS {USGS_NAMES.get(c, f'cat {c}')}" for c in cats],
                   columns=[f"ours {l}" for l in labels5])
(ROOT / "reports/v4/tables").mkdir(parents=True, exist_ok=True)

# shaded HTML table (markdown tables cannot carry cell color); blue intensity
# scales with the row share, so the diagonal gradient reads at a glance
def _cell(v):
    a = min(v * 1.4, 1.0)   # max observed share ~46% -> alpha ~0.64, text stays legible
    return (f'<td style="text-align:right;padding:4px 12px;'
            f'background-color:rgba(46,109,164,{a:.2f})">{v:.0%}</td>')

head = "".join(f'<th style="text-align:right;padding:4px 12px">{c}</th>'
               for c in cdf.columns)
body = "".join(
    '<tr><th style="text-align:left;padding:4px 12px;font-weight:normal">'
    f'{idx}</th>{"".join(_cell(v) for v in row.values)}</tr>'
    for idx, row in cdf.iterrows())
FOOTNOTE = (
    "USGS classes are percentile thresholds of their habitat-selection "
    "index (non-habitat < 5th percentile; low 5th–25th; moderate "
    "25th–50th; high > 50th) — four classes of deliberately unequal "
    "area, unlike our five equal-area quantile bins, so the comparison "
    "is ordinal rather than class-for-class. Because our bins are "
    "equal-area, every cell would read ~20% if the two maps were "
    "unrelated; departures from 20% are the signal.\n")
with open(ROOT / "reports/v4/tables/usgs_contingency.md", "w") as f:
    f.write('<table style="border-collapse:collapse;margin:0.5em 0">'
            f'<thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table>\n\n' + FOOTNOTE)
# plain-markdown twin for non-HTML formats (PDF), which drop raw HTML
with open(ROOT / "reports/v4/tables/usgs_contingency_plain.md", "w") as f:
    f.write(cdf.map(lambda x: f"{x:.0%}").to_markdown() + "\n\n" + FOOTNOTE)
msg = (f"USGS raster: {target['name']}\n"
       f"common valid points: {len(ours):,} of 150,000\n"
       f"Spearman(ours, USGS): {rho:.3f}\n")
(ROOT / "reports/v4").mkdir(parents=True, exist_ok=True)
open(ROOT / "reports/v4/usgs_validation.txt", "w").write(msg)
print(msg)
print("USGS_VALIDATION_COMPLETE")
