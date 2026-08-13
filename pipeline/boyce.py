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
    nod = src.nodata
area = area[np.isfinite(area)]
area = area[area != -9999.0]
if nod is not None:
    area = area[area != nod]   # FINDINGS F7: respect the declared nodata, not just the -9999 convention
p_used = p_used[np.isfinite(p_used) & (p_used >= 0)]
if nod is not None:
    p_used = p_used[p_used != nod]   # FINDINGS F7: same nodata scrub as area, kept symmetric

lo, hi = area.min(), np.quantile(area, 0.999)
# FINDINGS F10: clip values above the 99.9th-percentile ceiling into the top
# window instead of excluding them -- the highest-suitability leks are exactly
# the ones the monotonicity claim leans on.
area = np.minimum(area, hi)
p_used = np.minimum(p_used, hi)
width = (hi - lo) / 5.0
starts = np.linspace(lo, hi - width, 10)
mids, F = [], []
for i, start in enumerate(starts):
    end = start + width
    last = i == len(starts) - 1   # top window is upper-inclusive so p == hi is counted
    obs = ((p_used >= start) & ((p_used <= end) if last else (p_used < end))).mean()
    exp = ((area >= start) & ((area <= end) if last else (area < end))).mean()
    if exp > 0:
        mids.append(start + width / 2)
        F.append(obs / exp)
mids, F = np.array(mids), np.array(F)
rank = lambda a: pd.Series(a).rank().values
boyce = float(np.corrcoef(rank(mids), rank(F))[0, 1])
if not np.isfinite(boyce):
    # FINDINGS F8: a zero-variance P/E ladder is the no-discrimination case the
    # index exists to detect -- refuse to write a nan headline into the artifacts.
    raise SystemExit("BOYCE_DEGENERATE: index is non-finite (zero-variance P/E ranks); artifacts not written")

tbl = pd.DataFrame({"Predicted probability (class midpoint)": np.round(mids, 3),
                    "P/E ratio (lek share / area share)": np.round(F, 2)})
(ROOT / "reports/v4/tables").mkdir(parents=True, exist_ok=True)
# single source of truth for the P/E curve figure (map_panels.py plots this)
pd.DataFrame({"midpoint": mids, "pe": F, "boyce": boyce}).to_csv(
    ROOT / "reports/v4/boyce_pe.csv", index=False)
with open(ROOT / "reports/v4/tables/boyce.md", "w") as f:
    f.write(tbl.to_markdown(index=False) + f"\n\n**Continuous Boyce index: {boyce:.3f}**\n\n"
            "P/E is the predicted-to-expected ratio: the proportion of the used "
            "leks whose predicted probability falls in a class, divided by the "
            "proportion of the study area in that class. P/E = 1 means leks occur "
            "in the class at exactly the rate its area alone would predict; P/E > 1 "
            "means the class captures more leks than its share of the landscape. "
            "The continuous Boyce index (Hirzel et al. 2006) is the Spearman rank "
            "correlation between P/E and class midpoint: it ranges from −1 to 1, "
            "where values near 1 indicate lek density rises monotonically with "
            "predicted suitability, 0 indicates a surface no better than chance, "
            "and negative values indicate counter-prediction.\n")
print(f"P/E by class: {np.round(F, 2).tolist()}")
print(f"BOYCE_INDEX: {boyce:.3f}")
