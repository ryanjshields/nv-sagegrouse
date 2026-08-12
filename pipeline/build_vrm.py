# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "numpy", "scipy"]
# ///
"""build_vrm.py -- Vector Ruggedness Measure (Sappington et al. 2007), 3x3 (90 m) window.

Decomposes each cell's surface normal from the slope and aspect rasters,
takes the focal mean of the normal components, and measures dispersion:
  VRM = 1 - |R| / n,  R = (sum sin(s)sin(a), sum sin(s)cos(a), sum cos(s))

Inputs:  data-local/dem/nv_slope_5070.tif, nv_aspect_5070.tif (degrees)
Output:  data-local/dem/nv_vrm_5070.tif (float32, deflate-tiled)
Processed in row blocks with a 1-cell halo; constant memory.
"""
import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import uniform_filter
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data-local/dem"
BLOCK = 2048

with rasterio.open(D / "nv_slope_5070.tif") as s_src, rasterio.open(D / "nv_aspect_5070.tif") as a_src:
    profile = s_src.profile.copy()
    profile.update(driver="GTiff", dtype="float32", compress="deflate", tiled=True,
                   bigtiff="IF_SAFER", nodata=None)
    H, W = s_src.height, s_src.width
    with rasterio.open(D / "nv_vrm_5070.tif", "w", **profile) as dst:
        for row0 in range(0, H, BLOCK):
            r_lo = max(row0 - 1, 0)
            r_hi = min(row0 + BLOCK + 1, H)
            win = Window(0, r_lo, W, r_hi - r_lo)
            slope = np.deg2rad(s_src.read(1, window=win).astype("float64"))
            aspect = np.deg2rad(a_src.read(1, window=win).astype("float64"))
            xy = np.sin(slope)
            x, y, z = xy * np.sin(aspect), xy * np.cos(aspect), np.cos(slope)
            # focal MEANS of components; |R|/n == |mean vector|
            rx, ry, rz = (uniform_filter(c, size=3, mode="nearest") for c in (x, y, z))
            vrm = 1.0 - np.sqrt(rx**2 + ry**2 + rz**2)
            crop_lo = row0 - r_lo
            out = vrm[crop_lo: crop_lo + min(BLOCK, H - row0)].astype("float32")
            dst.write(out, 1, window=Window(0, row0, W, out.shape[0]))
print("VRM_COMPLETE")
