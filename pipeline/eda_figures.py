# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "rasterio", "matplotlib", "pandas", "pyarrow", "numpy", "tabulate"]
# ///
"""eda_figures.py -- EDA figures and tables for reports/findings.qmd.

Produces used-vs-available covariate distributions, vegetation class
proportions, an S1-style validation table (study-area raster means vs
available-sample means), summary statistics, model-selection and full
coefficient tables. Reads only pipeline artifacts; plots no lek locations.

Outputs -> reports/v4/figs/*.png and reports/v4/tables/*.md
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"
TABLES = ROOT / "reports/v4/tables"
FIGS.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

pts = pd.read_parquet(D / "design/model_input.parquet")
CONT = [("elevation", "Elevation (m)"), ("slope", "Slope (°)"), ("tri", "Ruggedness (VRM)"),
        ("curvature", "Curvature"), ("dist_road_m", "Distance to road (m)")]

# --- Fig: used vs available distributions --------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
for ax, (col, label) in zip(axes.flat, CONT):
    for use, color, name in [(0, "#9aa5b1", "available"), (1, "#3a6ea5", "used")]:
        v = pts.loc[pts.use == use, col].dropna()
        if col in ("tri", "dist_road_m"):
            v = v[v < v.quantile(0.99)]
        ax.hist(v, bins=40, density=True, alpha=0.55, color=color, label=name)
    ax.set_title(label, fontsize=9); ax.tick_params(labelsize=7)
axes.flat[0].legend(frameon=False, fontsize=8)
axes.flat[-1].set_axis_off()
fig.suptitle("Continuous predictor distributions at used (n=718) and available (n=7,180) sites", fontsize=10)
fig.tight_layout()
fig.savefig(FIGS / "distributions.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- Fig: vegetation class proportions -----------------------------------------
veg = (pts.assign(evt=pts.evt_phys.fillna("Other"))
          .groupby(["evt", "use"]).size().unstack(fill_value=0))
veg = veg / veg.sum(axis=0)
veg = veg.sort_values(1, ascending=True)
fig, ax = plt.subplots(figsize=(7, 4.2))
y = np.arange(len(veg))
ax.barh(y - 0.2, veg[0], height=0.4, color="#9aa5b1", label="available")
ax.barh(y + 0.2, veg[1], height=0.4, color="#3a6ea5", label="used")
ax.set_yticks(y); ax.set_yticklabels(veg.index, fontsize=8)
ax.set_xlabel("proportion of sites"); ax.legend(frameon=False, fontsize=8)
ax.set_title("Vegetation cover (LANDFIRE EVT_PHYS) at used vs available sites", fontsize=10)
fig.savefig(FIGS / "veg_proportions.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --- S1-style validation: study-area means (dense Monte Carlo) vs available-sample means
sa = gpd.read_file(D / "design/study_area_5070.gpkg")
dense = sa.sample_points(100_000, rng=777).explode(index_parts=False)
dx, dy = dense.x.values, dense.y.values
def dense_mean(path):
    with rasterio.open(path) as src:
        vals = np.array([v[0] for v in src.sample(zip(dx, dy))], dtype="float64")
        vals = vals[np.isfinite(vals) & (vals > -1e30)]
        return vals.mean()

rasters = {"elevation": D / "dem/nv_dem_5070.tif", "slope": D / "dem/nv_slope_5070.tif",
           "tri": D / "dem/nv_vrm_5070.tif", "curvature": D / "dem/nv_curv_5070.tif"}
rows = []
for col, label in CONT:
    avail = pts.loc[pts.use == 0, col].dropna()
    m, se = avail.mean(), avail.std() / np.sqrt(len(avail))
    lo, hi = m - 1.44 * se, m + 1.44 * se  # 85% CI, matching the paper's reporting level
    truth = dense_mean(rasters[col]) if col in rasters else float("nan")
    rows.append({"Variable": label, "Study-area mean": truth,
                 "Available-sample mean": m, "85% CI low": lo, "85% CI high": hi,
                 "Covered": "yes" if (np.isnan(truth) or lo <= truth <= hi) else "no"})
val = pd.DataFrame(rows)
def fmt(x):
    return "—" if (isinstance(x, float) and np.isnan(x)) else (f"{x:,.4g}" if isinstance(x, float) else str(x))
with open(TABLES / "validation.md", "w") as f:
    f.write(val.map(fmt).to_markdown(index=False) + "\n")

# --- Summary statistics table ---------------------------------------------------
srows = []
for col, label in CONT:
    for use, name in [(1, "used"), (0, "available")]:
        v = pts.loc[pts.use == use, col].dropna()
        srows.append({"Variable": label, "Sites": name, "Mean": v.mean(), "SD": v.std(),
                      "Min": v.min(), "Max": v.max()})
summ = pd.DataFrame(srows)
with open(TABLES / "summary_stats.md", "w") as f:
    f.write(summ.map(fmt).to_markdown(index=False) + "\n")

# --- Model selection table ------------------------------------------------------
sel = pd.read_csv(ROOT / "reports/v4/model_selection.csv", index_col=0)
keep = [c for c in ("df", "logLik", "AICc", "delta", "weight") if c in sel.columns]
sel_out = sel[keep].head(6).reset_index().rename(columns={"index": "Model"})
with open(TABLES / "model_selection.md", "w") as f:
    f.write(sel_out.map(fmt).to_markdown(index=False) + "\n")

# --- Full coefficient table -----------------------------------------------------
betas = pd.read_csv(ROOT / "reports/v4/averaged_betas.csv", index_col=0)
cof = betas[["Estimate", "ci85_low", "ci85_high"]].reset_index().rename(
    columns={"index": "Term", "ci85_low": "85% CI low", "ci85_high": "85% CI high"})
with open(TABLES / "coefficients.md", "w") as f:
    f.write(cof.map(fmt).to_markdown(index=False) + "\n")

print("EDA_COMPLETE:", sorted(p.name for p in FIGS.glob("*.png")), "|",
      sorted(p.name for p in TABLES.glob("*.md")))
