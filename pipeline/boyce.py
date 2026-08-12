# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "pyarrow", "tabulate"]
# ///
"""boyce.py -- continuous Boyce index (Hirzel et al. 2006) for the v4 surface.

Predicted-to-expected ratio in 10 moving-window probability classes:
F_i = (proportion of used leks in class i) / (proportion of study area in class i),
then Spearman rank correlation between F_i and class midpoint.
Writes reports/v4/tables/boyce.md and prints the index.
"""
import numpy as np
import pandas as pd
import rasterio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"

pts = pd.read_parquet(D / "design/design_points.parquet")
used = pts[pts.use == 1]
with rasterio.open(D / "dem/nv_prediction_v4_5070.tif") as src:
    p_used = np.array([v[0] for v in src.sample(zip(used.x, used.y))], dtype="float64")
    oh = 2800; ow = int(oh * src.width / src.height)
    area = src.read(1, out_shape=(oh, ow)).astype("float64")
area = area[area != -9999.0]
area = area[np.isfinite(area)]
p_used = p_used[np.isfinite(p_used) & (p_used >= 0)]

lo, hi = area.min(), np.quantile(area, 0.999)
width = (hi - lo) / 5.0
mids, F = [], []
for start in np.linspace(lo, hi - width, 10):
    end = start + width
    obs = ((p_used >= start) & (p_used < end)).mean()
    exp = ((area >= start) & (area < end)).mean()
    if exp > 0:
        mids.append(start + width / 2)
        F.append(obs / exp)
mids, F = np.array(mids), np.array(F)
rank = lambda a: pd.Series(a).rank().values
boyce = float(np.corrcoef(rank(mids), rank(F))[0, 1])

tbl = pd.DataFrame({"class midpoint": np.round(mids, 4), "P/E ratio": np.round(F, 2)})
(ROOT / "reports/v4/tables").mkdir(parents=True, exist_ok=True)
with open(ROOT / "reports/v4/tables/boyce.md", "w") as f:
    f.write(tbl.to_markdown(index=False) + f"\n\n**Continuous Boyce index: {boyce:.3f}**\n")
print(f"P/E by class: {np.round(F, 2).tolist()}")
print(f"BOYCE_INDEX: {boyce:.3f}")
