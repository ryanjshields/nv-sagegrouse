# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "matplotlib"]
# ///
"""map_panels.py -- the fine-scale zoom panel, USGS side-by-side, and Boyce
P/E curve figure. Zoom window fixed on the Tuscarora Mountains area, chosen
for terrain diversity (not on lek data). No lek locations are plotted.

Outputs: reports/v4/figs/{prediction_zoom.png, usgs_side_by_side.png, boyce_curve.png}
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from rasterio.vrt import WarpedVRT
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"
COLORS = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
nv = gpd.read_parquet(D / "vectors/nv_boundary.parquet")

with rasterio.open(D / "dem/nv_prediction_v4_5070.tif") as src:
    oh = 1400; ow = int(oh * src.width / src.height)
    state = src.read(1, out_shape=(oh, ow)).astype("float64")
    bnd = src.bounds
    # zoom window: Tuscarora Mountains area, ~60 km on a side
    zx, zy, half = -1_705_000, 2_255_000, 30_000
    zwin = from_bounds(zx - half, zy - half, zx + half, zy + half, src.transform)
    zoom = src.read(1, window=zwin).astype("float64")
state[state == -9999.0] = np.nan
zoom[zoom == -9999.0] = np.nan
valid = state[np.isfinite(state)]
qs = np.nanquantile(valid, [0.2, 0.4, 0.6, 0.8])
bin_state = np.where(np.isfinite(state), np.digitize(state, qs), np.nan)
bin_zoom = np.where(np.isfinite(zoom), np.digitize(zoom, qs), np.nan)

fig, axes = plt.subplots(1, 2, figsize=(11, 5.8), gridspec_kw={"width_ratios": [1, 1.15]})
axes[0].imshow(bin_state, cmap=ListedColormap(COLORS), vmin=0, vmax=4,
               extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
nv.boundary.plot(ax=axes[0], color="#444", linewidth=0.6)
axes[0].add_patch(Rectangle((zx - half, zy - half), 2 * half, 2 * half,
                            fill=False, edgecolor="black", linewidth=1.4))
axes[0].set_axis_off(); axes[0].set_title("statewide (30 m)", fontsize=10)
axes[1].imshow(bin_zoom, cmap=ListedColormap(COLORS), vmin=0, vmax=4,
               extent=(zx - half, zx + half, zy - half, zy + half))
axes[1].set_axis_off(); axes[1].set_title("60-km window: 30-m structure", fontsize=10)
fig.suptitle("Fine-scale prediction structure invisible at state scale", fontsize=11)
fig.savefig(FIGS / "prediction_zoom.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- USGS side-by-side: their spring selection categories on our grid ----------
with rasterio.open(D / "usgs/GrSG_Spring_Selection_Categories.tif") as usrc:
    with WarpedVRT(usrc, crs="EPSG:5070") as vrt:
        uwin = from_bounds(bnd.left, bnd.bottom, bnd.right, bnd.top, vrt.transform)
        theirs = vrt.read(1, window=uwin, out_shape=(oh, ow)).astype("float64")
        und = usrc.nodata
if und is not None:
    theirs[theirs == und] = np.nan
theirs[theirs < 0] = np.nan

fig, axes = plt.subplots(1, 2, figsize=(11, 5.8))
axes[0].imshow(bin_state, cmap=ListedColormap(COLORS), vmin=0, vmax=4,
               extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
axes[0].set_title("this study: lek-site RSF (quantile bins)", fontsize=10)
im = axes[1].imshow(theirs, cmap="viridis",
                    extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
axes[1].set_title("USGS spring habitat-selection categories\n(telemetry-based; ver. 3.0 2025)", fontsize=10)
for ax in axes:
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.6)
    ax.set_axis_off()
fig.suptitle("External comparison: Spearman ρ = 0.52 at 147,036 locations", fontsize=11)
fig.savefig(FIGS / "usgs_side_by_side.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- Boyce P/E curve -------------------------------------------------------------
pts = pd.read_parquet(D / "design/design_points.parquet")
used = pts[pts.use == 1]
with rasterio.open(D / "dem/nv_prediction_v4_5070.tif") as src:
    p_used = np.array([v[0] for v in src.sample(zip(used.x, used.y))], dtype="float64")
p_used = p_used[np.isfinite(p_used) & (p_used >= 0)]
lo, hi = valid.min(), np.quantile(valid, 0.999)
width = (hi - lo) / 5.0
mids, F = [], []
for start in np.linspace(lo, hi - width, 10):
    end = start + width
    exp = ((valid >= start) & (valid < end)).mean()
    if exp > 0:
        mids.append(start + width / 2)
        F.append(((p_used >= start) & (p_used < end)).mean() / exp)
fig, ax = plt.subplots(figsize=(5.2, 4))
ax.plot(mids, F, "-o", color="#3a6ea5")
ax.axhline(1.0, color="#999", linestyle="--", linewidth=0.8)
ax.set_xlabel("predicted probability (class midpoint)")
ax.set_ylabel("predicted-to-expected ratio")
ax.set_title("Boyce evaluation: P/E by probability class (index = 0.99)", fontsize=10)
fig.savefig(FIGS / "boyce_curve.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("MAP_PANELS_COMPLETE")
