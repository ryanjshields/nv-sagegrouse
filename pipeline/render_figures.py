# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "rasterio", "matplotlib", "pandas", "pyarrow"]
# ///
"""render_figures.py -- generate the figures consumed by reports/findings.qmd.

Reads only pipeline artifacts. Never plots lek locations (sensitive).
Outputs -> reports/v4/figs/*.png
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "data-local/vectors"
D = ROOT / "data-local/dem"
FIGS = ROOT / "reports/v4/figs"
FIGS.mkdir(parents=True, exist_ok=True)

# --- Fig 1: study area ---------------------------------------------------------
nv = gpd.read_parquet(V / "nv_boundary.parquet")
rng = gpd.read_parquet(V / "grsg_range_nv_5070.parquet")
fig, ax = plt.subplots(figsize=(5, 6))
nv.plot(ax=ax, facecolor="none", edgecolor="#555", linewidth=1)
rng.plot(ax=ax, facecolor="#7c9c6b", edgecolor="none", alpha=0.75)
ax.set_axis_off()
ax.set_title("Study area: sage-grouse range in Nevada\n(USFWS 2015 range; 152,458 km² with lek buffers)", fontsize=9)
fig.savefig(FIGS / "study_area.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- Fig 2: terrain covariate thumbnails (COG overview reads, masked to NV) ---
from affine import Affine
from rasterio.features import rasterize

nv_geom = nv.union_all()
panels = [("nv_dem_5070.tif", "Elevation (m)", "gist_earth", False),
          ("nv_slope_5070.tif", "Slope (\u00b0)", "inferno", False),
          ("nv_vrm_5070.tif", "VRM (\u00d71000)", "viridis", True)]
fig, axes = plt.subplots(1, 3, figsize=(11, 4.6))
for ax, (fname, title, cmap, is_vrm) in zip(axes, panels):
    with rasterio.open(D / fname) as src_r:
        oh = 800
        ow = int(oh * src_r.width / src_r.height)
        a = src_r.read(1, out_shape=(oh, ow), masked=True).astype("float64").filled(np.nan)
        t = src_r.transform * Affine.scale(src_r.width / ow, src_r.height / oh)
        b = src_r.bounds
    a[np.abs(a) > 1e5] = np.nan
    if is_vrm:
        a = a * 1000.0
    state_mask = rasterize([(nv_geom, 1)], out_shape=(oh, ow), transform=t, fill=0).astype(bool)
    a[~state_mask] = np.nan
    vmin, vmax = np.nanpercentile(a, [2, 98])
    im = ax.imshow(a, cmap=cmap, vmin=vmin, vmax=vmax,
                   extent=(b.left, b.right, b.bottom, b.top))
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.6)
    ax.set_axis_off(); ax.set_title(title, fontsize=10)
    fig.colorbar(im, ax=ax, orientation="horizontal", shrink=0.75, pad=0.03)
fig.suptitle("Terrain covariates, 30 m EPSG:5070, clipped to Nevada", fontsize=11)
fig.tight_layout()
fig.savefig(FIGS / "terrain.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- Fig 3: coefficient comparison ---------------------------------------------
betas = pd.read_csv(ROOT / "reports/v4/averaged_betas.csv", index_col=0)
ours = {"Ruggedness": "scale_Ruggedness", "Slope": "scale_Slope", "Elevation": "scale_Elevation"}
paper = {"Ruggedness": (0.14, 0.08, 0.20), "Slope": (-1.42, -1.55, -1.28), "Elevation": (0.78, 0.69, 0.86)}
fig, ax = plt.subplots(figsize=(6.5, 3.4))
for i, (label, term) in enumerate(ours.items()):
    est, lo, hi = betas.loc[term, ["Estimate", "ci85_low", "ci85_high"]]
    p_est, p_lo, p_hi = paper[label]
    ax.errorbar(p_est, i + 0.12, xerr=[[p_est - p_lo], [p_hi - p_est]], fmt="s", color="#b08640", label="2024 draft" if i == 0 else None)
    ax.errorbar(est, i - 0.12, xerr=[[est - lo], [hi - est]], fmt="o", color="#3a6ea5", label="v4 (2026)" if i == 0 else None)
ax.axvline(0, color="#999", linewidth=0.8)
ax.set_yticks(range(len(ours))); ax.set_yticklabels(ours.keys())
ax.set_xlabel("standardized coefficient (85% CI)")
ax.legend(frameon=False, fontsize=8)
ax.set_title("Model-averaged terrain effects: 2024 draft vs v4", fontsize=10)
fig.savefig(FIGS / "betas.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- Fig 4: vegetation contrasts -----------------------------------------------
veg = betas[betas.index.str.startswith("Vegetation")].copy()
veg["label"] = veg.index.str.replace("Vegetation", "", regex=False)
veg = veg.sort_values("Estimate")
fig, ax = plt.subplots(figsize=(6.5, 3.8))
colors = ["#a05252" if v < 0 else "#5f8f5a" for v in veg["Estimate"]]
ax.barh(veg["label"], veg["Estimate"], color=colors)
ax.axvline(0, color="#555", linewidth=0.8)
ax.set_xlabel("coefficient vs. Shrubland reference")
ax.set_title("Vegetation selection relative to shrubland (v4)", fontsize=10)
ax.tick_params(labelsize=8)
fig.savefig(FIGS / "vegetation.png", dpi=150, bbox_inches="tight")
plt.close(fig)

print("FIGURES_COMPLETE:", sorted(p.name for p in FIGS.glob("*.png")))

# --- Forest plot: single-axis sjPlot style --------------------------------------
# (Viable since the <5-used-leks pooling guard: without it, separation-fossil
# CIs of width ~20 blew the axis out and squashed every terrain effect.)
betas = pd.read_csv(ROOT / "reports/v4/averaged_betas.csv", index_col=0)
b = betas[~betas.index.str.contains("Intercept")][["Estimate", "ci85_low", "ci85_high"]]
b = b[(b.ci85_high - b.ci85_low) < 20]
def clean(ix):
    return (ix.str.replace("scale_", "", regex=False)
              .str.replace("Direction", "Aspect: ", regex=False)
              .str.replace("Vegetation", "Veg: ", regex=False))
NEG, POS = "#c0392b", "#2e6da4"   # sjPlot convention: red negative, blue positive
d = b.sort_values("Estimate")
yy = np.arange(len(d))
colors = [NEG if v < 0 else POS for v in d.Estimate]
sig = (d.ci85_low > 0) | (d.ci85_high < 0)   # CI excludes zero
face = [c if s else "white" for c, s in zip(colors, sig)]
fig, ax = plt.subplots(figsize=(7, 6.5))
ax.hlines(yy, d.ci85_low, d.ci85_high, color=colors, linewidth=1.6)
ax.scatter(d.Estimate, yy, facecolor=face, edgecolor=colors,
           linewidth=1.3, zorder=3, s=30)
ax.axvline(0, color="#777", linewidth=0.9)
ax.set_yticks(yy); ax.set_yticklabels(clean(d.index), fontsize=8)
ax.set_xlabel("standardized coefficient (85% CI)")
from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([], [], marker="o", color=NEG, linestyle="", label="negative"),
    Line2D([], [], marker="o", color=POS, linestyle="", label="positive"),
    Line2D([], [], marker="o", markerfacecolor="white", color="#555",
           linestyle="", label="85% CI crosses zero")],
    frameon=False, fontsize=8, loc="upper left")
ax.set_title("Model-averaged effects, top three models", fontsize=11)
fig.tight_layout()
fig.savefig(FIGS / "forest.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("FOREST_COMPLETE")
