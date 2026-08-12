# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "pandas", "geopandas>=1.0", "pyogrio", "pyarrow", "matplotlib"]
# ///
"""covariate_multiples.py -- small-multiples atlas of every predictor surface."""
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.features import rasterize
from affine import Affine
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"
nv = gpd.read_parquet(D / "vectors/nv_boundary.parquet")
nv_geom = nv.union_all()

def read_masked(path, oh=700):
    with rasterio.open(path) as src:
        ow = int(oh * src.width / src.height)
        a = src.read(1, out_shape=(oh, ow), masked=True).astype("float64").filled(np.nan)
        t = src.transform * Affine.scale(src.width / ow, src.height / oh)
        b = src.bounds
    a[np.abs(a) > 1e7] = np.nan
    mask = rasterize([(nv_geom, 1)], out_shape=a.shape, transform=t, fill=0).astype(bool)
    a[~mask] = np.nan
    return a, b

PANELS = [
    ("dem/nv_dem_5070.tif", "Elevation (m)", "gist_earth", False),
    ("dem/nv_slope_5070.tif", "Slope (°)", "inferno", False),
    ("dem/nv_vrm_5070.tif", "VRM (×1000)", "viridis", True),
    ("dem/nv_curv_5070.tif", "Curvature", "RdBu_r", False),
    ("dem/nv_distroad_paved_5070.tif", "Dist. to paved road (km)", "mako_r", "km"),
    ("dem/nv_distroad_unpaved_5070.tif", "Dist. to unpaved road (km)", "mako_r", "km"),
]
fig, axes = plt.subplots(2, 4, figsize=(14.5, 8))
for ax, (fname, title, cmap, scalemode) in zip(axes.flat, PANELS):
    a, b = read_masked(D / fname)
    if scalemode is True:
        a = a * 1000.0
    elif scalemode == "km":
        a = a / 1000.0
    if cmap == "mako_r":
        cmap = "viridis_r"
    vmin, vmax = np.nanpercentile(a, [2, 98])
    im = ax.imshow(a, cmap=cmap, vmin=vmin, vmax=vmax, extent=(b.left, b.right, b.bottom, b.top))
    nv.boundary.plot(ax=ax, color="#444", linewidth=0.5)
    ax.set_axis_off(); ax.set_title(title, fontsize=9)
    fig.colorbar(im, ax=ax, orientation="horizontal", shrink=0.7, pad=0.03)

# aspect (categorical 8-way)
a, b = read_masked(D / "dem/nv_aspect_5070.tif")
edges = [0, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, 360]
cyc = plt.cm.twilight(np.linspace(0, 1, 9))
ax = axes.flat[6]
im = ax.imshow(a, cmap=ListedColormap(cyc), norm=BoundaryNorm(edges, 9),
               extent=(b.left, b.right, b.bottom, b.top))
nv.boundary.plot(ax=ax, color="#444", linewidth=0.5)
ax.set_axis_off(); ax.set_title("Aspect (8 directions)", fontsize=9)

# vegetation (top EVT_PHYS classes)
with rasterio.open(D / "landfire/evt_5070_30.tif") as src:
    oh = 700; ow = int(oh * src.width / src.height)
    ev = src.read(1, out_shape=(oh, ow)).astype("int64")
    t = src.transform * Affine.scale(src.width / ow, src.height / oh)
    b = src.bounds
vat = pd.read_csv(D / "landfire/evt_vat.csv")
phys = vat.set_index("Value")["EVT_PHYS"]
CLASSES = ["Conifer", "Shrubland", "Grassland", "Exotic Herbaceous", "Riparian", "Sparsely Vegetated"]
CCOLORS = ["#1b6b48", "#b8a24a", "#8fce6e", "#d9e79c", "#3b8ec2", "#cfc6b8"]
code = np.zeros_like(ev, dtype="float64"); code[:] = np.nan
lut = {}
for v, p in phys.items():
    if str(p) in CLASSES:
        lut[int(v)] = CLASSES.index(str(p))
for v, i in lut.items():
    code[ev == v] = i
mask = rasterize([(nv_geom, 1)], out_shape=code.shape, transform=t, fill=0).astype(bool)
code[~mask] = np.nan
ax = axes.flat[7]
ax.imshow(code, cmap=ListedColormap(CCOLORS), vmin=0, vmax=5, extent=(b.left, b.right, b.bottom, b.top))
nv.boundary.plot(ax=ax, color="#444", linewidth=0.5)
ax.set_axis_off(); ax.set_title("Vegetation (major EVT_PHYS classes)", fontsize=9)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=l) for l, c in zip(CLASSES, CCOLORS)],
          fontsize=6, loc="lower left", frameon=False)
fig.suptitle("Predictor surfaces, 30 m EPSG:5070, clipped to Nevada", fontsize=12)
fig.tight_layout()
fig.savefig(FIGS / "covariate_multiples.png", dpi=150, bbox_inches="tight")
print("COVARIATE_MULTIPLES_COMPLETE")
