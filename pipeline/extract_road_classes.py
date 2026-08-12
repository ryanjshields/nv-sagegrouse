# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "pandas", "pyarrow"]
# ///
"""Append paved/unpaved road distances to model_input."""
import pandas as pd, rasterio
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
pts = pd.read_parquet(D / "design/model_input.parquet")
xy = list(zip(pts.x, pts.y))
for cls in ("paved", "unpaved"):
    with rasterio.open(D / f"dem/nv_distroad_{cls}_5070.tif") as src:
        pts[f"dist_{cls}_m"] = [v[0] for v in src.sample(xy)]
pts.to_parquet(D / "design/model_input.parquet", index=False)
pts.to_csv(D / "design/model_input.csv", index=False)
print("ROAD_CLASS_EXTRACT_COMPLETE", pts[["dist_paved_m","dist_unpaved_m"]].mean().round(0).to_dict())
