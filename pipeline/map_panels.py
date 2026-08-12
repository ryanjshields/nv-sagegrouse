# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "matplotlib", "tabulate"]
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

# --- USGS side-by-side v2: study-area clipped, legended, bin-vs-category ------
from rasterio.features import rasterize as rasterize_feat
sa_gdf = gpd.read_file(D / "design/study_area_5070.gpkg")
sa_geom = sa_gdf.geometry.iloc[0]
with rasterio.open(D / "usgs/GrSG_Spring_Selection_Categories.tif") as usrc:
    with WarpedVRT(usrc, crs="EPSG:5070") as vrt:
        uwin = from_bounds(bnd.left, bnd.bottom, bnd.right, bnd.top, vrt.transform)
        theirs = vrt.read(1, window=uwin, out_shape=(oh, ow)).astype("float64")
        und = usrc.nodata
if und is not None:
    theirs[theirs == und] = np.nan
theirs[theirs < 0] = np.nan
# mask both layers to the study area on the display grid
t_disp = rasterio.transform.from_bounds(bnd.left, bnd.bottom, bnd.right, bnd.top, ow, oh)
sa_mask = rasterize_feat([(sa_geom, 1)], out_shape=(oh, ow), transform=t_disp, fill=0).astype(bool)
theirs[~sa_mask] = np.nan
bin_state_sa = np.where(sa_mask, bin_state, np.nan)

cats = sorted(int(c) for c in np.unique(theirs[np.isfinite(theirs)]))
cat_cmap = ListedColormap(plt.cm.viridis(np.linspace(0, 1, len(cats))))
fig, axes = plt.subplots(1, 2, figsize=(11.5, 6))
im0 = axes[0].imshow(bin_state_sa, cmap=ListedColormap(COLORS), vmin=0, vmax=4,
                     extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
axes[0].set_title("this study: lek-site RSF, quantile bins", fontsize=10)
cb0 = fig.colorbar(im0, ax=axes[0], shrink=0.5, ticks=[0.4, 1.2, 2.0, 2.8, 3.6])
cb0.ax.set_yticklabels(["very low", "low", "moderate", "high", "very high"], fontsize=7)
theirs_idx = np.full_like(theirs, np.nan)
for i, c in enumerate(cats):
    theirs_idx[theirs == c] = i
im1 = axes[1].imshow(theirs_idx, cmap=cat_cmap, vmin=-0.5, vmax=len(cats) - 0.5,
                     extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
axes[1].set_title("USGS spring habitat-selection categories\n(telemetry-based, ver. 3.0 2025)", fontsize=10)
cb1 = fig.colorbar(im1, ax=axes[1], shrink=0.5, ticks=range(len(cats)))
cb1.ax.set_yticklabels([f"category {c}" for c in cats], fontsize=7)
for ax in axes:
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.6)
    ax.set_axis_off()
fig.suptitle("External comparison within the study area (Spearman \u03c1 = 0.52)", fontsize=11)
fig.savefig(FIGS / "usgs_side_by_side.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# contingency: their category (rows) x our bin (cols), row-normalized
both_ok = np.isfinite(theirs_idx) & np.isfinite(bin_state_sa)
tab = np.zeros((len(cats), 5))
for i in range(len(cats)):
    for j in range(5):
        tab[i, j] = np.sum((theirs_idx == i) & (bin_state_sa == j) & both_ok)
row_tot = tab.sum(axis=1, keepdims=True); row_tot[row_tot == 0] = 1
tab_pct = tab / row_tot
labels5 = ["very low", "low", "moderate", "high", "very high"]
cdf = pd.DataFrame(tab_pct, index=[f"USGS cat {c}" for c in cats],
                   columns=[f"ours {l}" for l in labels5])
with open(ROOT / "reports/v4/tables/usgs_contingency.md", "w") as f:
    f.write(cdf.map(lambda x: f"{x:.0%}").to_markdown() + "\n")

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

# --- Small multiples: each quantile bin isolated --------------------------------
labels5 = ["very low", "low", "moderate", "high", "very high"]
fig, axes = plt.subplots(1, 5, figsize=(16, 4.6))
share = [np.nansum(bin_state_sa == i) / np.nansum(np.isfinite(bin_state_sa)) for i in range(5)]
for i, (ax, lab) in enumerate(zip(axes, labels5)):
    solo = np.where(bin_state_sa == i, 1.0, np.nan)
    ax.imshow(solo, cmap=ListedColormap(["#1a1a1a"]), vmin=0, vmax=1,
              extent=(bnd.left, bnd.right, bnd.bottom, bnd.top))
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.5)
    ax.set_axis_off()
    ax.set_title(f"{lab}\n({share[i]:.0%} of study area)", fontsize=9)
fig.suptitle("Predicted lek-occurrence probability: each quantile class isolated", fontsize=11)
fig.tight_layout()
fig.savefig(FIGS / "prediction_bins_multiples.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("BIN_MULTIPLES_COMPLETE")
