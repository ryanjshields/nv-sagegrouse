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

# --- Fig 2: terrain covariate thumbnails (COG overview reads) ------------------
panels = [("nv_dem_5070.tif", "Elevation (m)", "terrain", None),
          ("nv_slope_5070.tif", "Slope (°)", "magma", (0, 40)),
          ("nv_vrm_5070.tif", "VRM (×1000)", "viridis", (0, 20))]
fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.2))
for ax, (fname, title, cmap, clim) in zip(axes, panels):
    with rasterio.open(D / fname) as src:
        a = src.read(1, out_shape=(1, 700, int(700 * src.width / src.height))).astype("float64")
    if "vrm" in fname:
        a = a * 1000.0
    a[a < -1e30] = np.nan
    im = ax.imshow(a, cmap=cmap, vmin=None if clim is None else clim[0],
                   vmax=None if clim is None else clim[1])
    ax.set_axis_off(); ax.set_title(title, fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.6)
fig.suptitle("Terrain covariates, 30 m EPSG:5070 (COG overview reads)", fontsize=10)
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
