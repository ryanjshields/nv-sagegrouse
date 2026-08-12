# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "matplotlib", "tabulate"]
# ///
"""compare_predictions.py -- old (v3-replica) vs new (v4) prediction surfaces.

Produces:
  reports/v4/figs/prediction_compare.png    side-by-side quantile maps + agreement map
  reports/v4/tables/bin_agreement.md        5x5 bin agreement matrix (row = v3, col = v4)
  prints Spearman correlation of probabilities and same-bin share
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"
TABLES = ROOT / "reports/v4/tables"

def read_binned(tag, oh=1400):
    with rasterio.open(D / f"dem/nv_prediction_{tag}_5070.tif") as src:
        ow = int(oh * src.width / src.height)
        a = src.read(1, out_shape=(oh, ow)).astype("float64")
        bnd = src.bounds
    a[a == -9999.0] = np.nan
    valid = a[np.isfinite(a)]
    qs = np.nanquantile(valid, [0.2, 0.4, 0.6, 0.8])
    bins = np.where(np.isfinite(a), np.digitize(a, qs), np.nan)
    return a, bins, bnd

p3, b3, bnd = read_binned("v3replica")
p4, b4, _ = read_binned("v4")

both = np.isfinite(b3) & np.isfinite(b4)
# Spearman via rank correlation on a large sample
idx = np.flatnonzero(both.ravel())
samp = np.random.default_rng(7).choice(idx, size=min(500_000, idx.size), replace=False)
r3 = pd.Series(p3.ravel()[samp]).rank()
r4 = pd.Series(p4.ravel()[samp]).rank()
spearman = float(np.corrcoef(r3, r4)[0, 1])
agree = float((b3[both] == b4[both]).mean())
within1 = float((np.abs(b3[both] - b4[both]) <= 1).mean())

mat = np.zeros((5, 5))
for i in range(5):
    for j in range(5):
        mat[i, j] = np.sum((b3 == i) & (b4 == j))
mat = mat / mat.sum()
labels = ["very low", "low", "moderate", "high", "very high"]
mdf = pd.DataFrame(mat, index=[f"v3 {l}" for l in labels], columns=[f"v4 {l}" for l in labels])
with open(TABLES / "bin_agreement.md", "w") as f:
    f.write(mdf.map(lambda x: f"{x:.1%}").to_markdown() + "\n")

nv = gpd.read_parquet(D / "vectors/nv_boundary.parquet")
colors = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
fig, axes = plt.subplots(1, 3, figsize=(13, 5.6))
for ax, (bins, title) in zip(axes[:2], [(b3, "2024 model, era covariates (v3 replica)"),
                                        (b4, "v4 (2026)")]):
    ax.imshow(bins, cmap=ListedColormap(colors), extent=(bnd.left, bnd.right, bnd.bottom, bnd.top), vmin=0, vmax=4)
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.6)
    ax.set_axis_off(); ax.set_title(title, fontsize=10)
diff = np.where(both, b4 - b3, np.nan)
im = axes[2].imshow(diff, cmap="PuOr_r", vmin=-4, vmax=4, extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
nv.boundary.plot(ax=axes[2], color="#444", linewidth=0.6)
axes[2].set_axis_off(); axes[2].set_title("bin shift (v4 − v3)", fontsize=10)
fig.colorbar(im, ax=axes[2], shrink=0.6, ticks=[-4, -2, 0, 2, 4])
fig.suptitle("Predicted lek-occurrence probability: old vs new, quantile five-bin", fontsize=11)
fig.savefig(FIGS / "prediction_compare.png", dpi=150, bbox_inches="tight")

print(f"spearman(prob): {spearman:.3f} | same bin: {agree:.1%} | within one bin: {within1:.1%}")
print("COMPARE_COMPLETE")
