# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "matplotlib", "tabulate"]
# ///
"""build_prediction.py -- score the study area through the averaged model.

Reads the aligned covariate COGs, applies the model-averaged coefficients
(z-scaled with the training means/sds from model_input), and writes:
  data-local/dem/nv_prediction_5070.tif    probability COG (masked to study area)
  reports/v4/figs/prediction_map.png       quantile 5-bin map (the paper's Fig 4)
  reports/v4/tables/prediction_bins.md     area per bin
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from affine import Affine
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"; FIGS.mkdir(parents=True, exist_ok=True)
TABLES = ROOT / "reports/v4/tables"; TABLES.mkdir(parents=True, exist_ok=True)

import sys
ARGS = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
BETAS_PATH = ARGS.get("betas", str(ROOT / "reports/v4/averaged_betas.csv"))
RUGG_MODE = ARGS.get("rugg", "vrm")          # vrm | eq1binary
EVT_PATH = ARGS.get("evt", str(D / "landfire/evt_5070_30.tif"))
VAT_PATH = ARGS.get("vat", str(D / "landfire/evt_vat.csv"))
TAG = ARGS.get("tag", "v4")
betas = pd.read_csv(BETAS_PATH, index_col=0)["Estimate"]
mi = pd.read_parquet(D / "design/model_input.parquet")
SC = {c: (mi[c].mean(), mi[c].std()) for c in ("curvature", "dist_road_m", "elevation", "tri", "slope")}
if ARGS.get("rugg", "vrm") == "eq1binary":
    # The era covariate is binary 0/1: z-scale by the binary's own moments,
    # not VRM's (which would send z(1) to ~+170 and saturate the logistic).
    SC["tri"] = (0.4543, 0.4979)

def b(name): return float(betas.get(name, 0.0))
DIR_BETA = {d: b(f"Direction{d}") for d in ("N", "NE", "NW", "S", "SE", "SW", "W", "Flat")}  # ref E = 0

# Vegetation: EVT raster value -> EVT_PHYS -> beta (ref Shrubland = 0; rare->Other)
vat = pd.read_csv(VAT_PATH)
vcol = "Value" if "Value" in vat.columns else vat.columns[0]
phys = vat.set_index(vcol)["EVT_PHYS"]
kept = {i.replace("Vegetation", "") for i in betas.index if i.startswith("Vegetation")}
def veg_beta(p):
    if p == "Shrubland": return 0.0
    key = p if p in kept else "Other"
    return b(f"Vegetation{key}")
maxval = int(phys.index.max())
VEG_LUT = np.zeros(maxval + 2, dtype="float64")
for v, p in phys.items():
    VEG_LUT[int(v)] = veg_beta(str(p))

paths = {k: D / "dem" / f"nv_{k}_5070.tif" for k in ("dem", "slope", "aspect", "vrm", "curv", "distroad")}
HAS_CLASS = "scale_PavedProximity" in betas.index
if HAS_CLASS:
    paths["distpaved"] = D / "dem/nv_distroad_paved_5070.tif"
    paths["distunpaved"] = D / "dem/nv_distroad_unpaved_5070.tif"
    SC["dist_paved_m"] = (mi["dist_paved_m"].mean(), mi["dist_paved_m"].std())
    SC["dist_unpaved_m"] = (mi["dist_unpaved_m"].mean(), mi["dist_unpaved_m"].std())
paths["evt"] = Path(EVT_PATH)
srcs = {k: rasterio.open(p) for k, p in paths.items()}
eq1_src = rasterio.open(D / "dem/nv_rugg_5070.tif")
def rd_eq1(win):
    a = eq1_src.read(1, window=win, masked=True).astype("float64").filled(np.nan)
    a[np.abs(a) > 1e5] = np.nan
    return a
ref = srcs["dem"]
H, W = ref.height, ref.width

sa = gpd.read_file(D / "design/study_area_5070.gpkg").geometry.iloc[0]
profile = ref.profile.copy()
profile.update(driver="GTiff", dtype="float32", compress="deflate", tiled=True,
               bigtiff="IF_SAFER", nodata=-9999.0)

BLOCK = 2048
out = rasterio.open(D / f"dem/nv_prediction_{TAG}_5070.tif", "w", **profile)
from rasterio.windows import Window
b0 = float(betas.get("(Intercept)", 0.0))
for row0 in range(0, H, BLOCK):
    h = min(BLOCK, H - row0)
    win = Window(0, row0, W, h)
    t = ref.window_transform(win)
    mask = rasterize([(sa, 1)], out_shape=(h, W), transform=t, fill=0).astype(bool)
    if not mask.any():
        out.write(np.full((h, W), -9999.0, "float32"), 1, window=win); continue
    def rd(k):
        a = srcs[k].read(1, window=win, masked=True).astype("float64").filled(np.nan)
        a[np.abs(a) > 1e5] = np.nan
        return a
    dem, slope, aspect, vrm, curv, dist = rd("dem"), rd("slope"), rd("aspect"), rd("vrm"), rd("curv"), rd("distroad")
    if RUGG_MODE == "eq1binary":
        vrm = np.round(rd_eq1(win))
    evt = srcs["evt"].read(1, window=win).astype("int64")
    evt = np.clip(evt, 0, maxval + 1)
    z = lambda a, k: (a - SC[k][0]) / SC[k][1]
    eta = (b0
           + b("scale_Ruggedness") * z(vrm, "tri")
           + b("scale_Slope") * z(slope, "slope")
           + b("scale_Elevation") * z(dem, "elevation")
           + b("scale_Curvature") * z(curv, "curvature")
           + b("scale_RoadsProximity") * z(dist, "dist_road_m"))
    if HAS_CLASS:
        eta += (b("scale_PavedProximity") * z(rd("distpaved"), "dist_paved_m")
                + b("scale_UnpavedProximity") * z(rd("distunpaved"), "dist_unpaved_m"))
    dir_arr = np.zeros_like(aspect)
    flat = slope < 0.5
    for lab, (lo, hi) in {"N": (337.5, 22.5), "NE": (22.5, 67.5), "SE": (112.5, 157.5),
                          "S": (157.5, 202.5), "SW": (202.5, 247.5), "W": (247.5, 292.5),
                          "NW": (292.5, 337.5)}.items():
        m = ((aspect > lo) & (aspect <= hi)) if lo < hi else ((aspect > lo) | (aspect <= hi))
        dir_arr[m] = DIR_BETA[lab]
    dir_arr[flat] = DIR_BETA["Flat"]
    eta += dir_arr + VEG_LUT[evt]
    p = 1.0 / (1.0 + np.exp(-eta))
    p[~mask | ~np.isfinite(p)] = -9999.0
    out.write(p.astype("float32"), 1, window=win)
out.close()
for s in srcs.values(): s.close()

# Quantile 5-bin classification + map + bin areas
with rasterio.open(D / f"dem/nv_prediction_{TAG}_5070.tif") as src:
    oh = 1400; ow = int(oh * src.width / src.height)
    a = src.read(1, out_shape=(oh, ow)).astype("float64")
a[a == -9999.0] = np.nan
valid = a[np.isfinite(a)]
qs = np.nanquantile(valid, [0.2, 0.4, 0.6, 0.8])
bins = np.digitize(a, qs)
bins = np.where(np.isfinite(a), bins, -1).astype("float64")
bins[bins < 0] = np.nan

nv = gpd.read_parquet(D / "vectors/nv_boundary.parquet")
with rasterio.open(D / f"dem/nv_prediction_{TAG}_5070.tif") as src:
    bnd = src.bounds
colors = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
fig, ax = plt.subplots(figsize=(6.5, 7.5))
im = ax.imshow(bins, cmap=ListedColormap(colors), extent=(bnd.left, bnd.right, bnd.bottom, bnd.top), vmin=0, vmax=4)
nv.boundary.plot(ax=ax, color="#444", linewidth=0.7)
ax.set_axis_off()
ax.set_title("Predicted probability of greater sage-grouse lek occurrence\n(quantile classification, five bins)", fontsize=10)
cbar = fig.colorbar(im, ax=ax, shrink=0.55, ticks=[0.4, 1.2, 2.0, 2.8, 3.6])
cbar.ax.set_yticklabels(["very low", "low", "moderate", "high", "very high"], fontsize=8)
fig.savefig(FIGS / f"prediction_map_{TAG}.png", dpi=150, bbox_inches="tight")
plt.close(fig)

cell_km2 = (30 * 30) / 1e6
n_valid_full = None
labels = ["very low", "low", "moderate", "high", "very high"]
counts = [int(np.nansum(bins == i)) for i in range(5)]
tot = sum(counts)
rows = [{"Bin": l, "Share of study area": f"{c/tot:.1%}",
         "Probability range": r} for l, c, r in zip(labels, counts,
         [f"< {qs[0]:.3f}", f"{qs[0]:.3f}–{qs[1]:.3f}", f"{qs[1]:.3f}–{qs[2]:.3f}",
          f"{qs[2]:.3f}–{qs[3]:.3f}", f"> {qs[3]:.3f}"])]
pd.DataFrame(rows).to_markdown(TABLES / f"prediction_bins_{TAG}.md", index=False)
print(f"quantile breaks: {np.round(qs, 4)}")
print("PREDICTION_COMPLETE")
