# /// script
# requires-python = ">=3.10"
# dependencies = ["rasterio", "pandas", "pyarrow", "numpy", "tabulate"]
# ///
"""veg_change_check.py -- did post-2018 disturbance (e.g., the 2018 Martin
Fire) change the vegetation class at lek sites between LANDFIRE eras?

Cross-tabulates each used lek's EVT_PHYS in LF2016 vs LF2025 on the common
grid, counts class transitions (especially shrubland -> herbaceous, the fire
signature), and writes a flag list for the sensitivity refit.

Outputs: reports/v4/tables/veg_change.md
         data-local/design/veg_changed_lekids.csv  (sensitive dir; ids only)
"""
import numpy as np
import pandas as pd
import rasterio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"

pts = pd.read_parquet(D / "design/model_input.parquet")
used = pts[pts.use == 1].copy()

vat16 = pd.read_csv(D / "landfire/lf2016/evt2016_vat.csv")
phys16 = vat16.set_index("Value")["EVT_PHYS"]
with rasterio.open(D / "landfire/lf2016/evt2016_5070_30.tif") as src:
    v16 = [v[0] for v in src.sample(zip(used.x, used.y))]
used["phys16"] = pd.Series(v16, index=used.index).map(phys16).fillna("Other")
used["phys25"] = used["evt_phys"].fillna("Other")

changed = used[used.phys16 != used.phys25]
shrub_to_herb = changed[(changed.phys16 == "Shrubland") &
                        (changed.phys25.isin(["Exotic Herbaceous", "Grassland"]))]

trans = (changed.groupby(["phys16", "phys25"]).size().sort_values(ascending=False)
         .rename("n leks").reset_index()
         .rename(columns={"phys16": "LF2016 class", "phys25": "LF2025 class"}))
with open(ROOT / "reports/v4/tables/veg_change.md", "w") as f:
    f.write(f"Used leks: {len(used)} | class changed LF2016->LF2025: "
            f"{len(changed)} ({len(changed)/len(used):.1%}) | "
            f"shrubland->herbaceous (fire signature): {len(shrub_to_herb)} "
            f"({len(shrub_to_herb)/len(used):.1%})\n\n")
    f.write(trans.head(12).to_markdown(index=False) + "\n")

changed[["lekid"]].to_csv(D / "design/veg_changed_lekids.csv", index=False)
print(f"changed: {len(changed)}/{len(used)} ({len(changed)/len(used):.1%}) | "
      f"shrub->herb: {len(shrub_to_herb)}")
print("VEG_CHANGE_COMPLETE")
