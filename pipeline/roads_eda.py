# /// script
# requires-python = ">=3.10"
# dependencies = ["geopandas>=1.0", "pyogrio", "pyarrow", "pandas", "matplotlib", "tabulate"]
# ///
"""roads_eda.py -- road length by MTFCC class and by usage group within the
study area (the 2024 draft's Figs 2-3 and Tables 1-2, regenerated on TIGER).

Outputs: reports/v4/figs/roads_by_class.png, roads_by_usage.png
         reports/v4/tables/mtfcc_codes.md, mtfcc_usage.md
"""
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data-local"
FIGS = ROOT / "reports/v4/figs"
TABLES = ROOT / "reports/v4/tables"

DESC = {"S1100": "Primary road (interstate/major highway)",
        "S1200": "Secondary road (state/county highway)",
        "S1400": "Local neighborhood road, rural road, city street",
        "S1500": "Vehicular trail (4WD, unimproved)",
        "S1630": "Ramp",
        "S1640": "Service drive",
        "S1710": "Walkway/pedestrian trail",
        "S1720": "Stairway",
        "S1730": "Alley",
        "S1740": "Private road for service vehicles",
        "S1750": "Internal U.S. Census Bureau use",
        "S1780": "Parking lot road",
        "S1820": "Bike path or trail"}
USAGE = {"S1100": "High-usage", "S1200": "High-usage", "S1630": "High-usage",
         "S1400": "Low-usage", "S1740": "Low-usage", "S1640": "Low-usage",
         "S1500": "Very low-usage"}

roads = gpd.read_parquet(D / "vectors/nv_roads_all_5070.parquet")
sa = gpd.read_file(D / "design/study_area_5070.gpkg").geometry.iloc[0]
idx = roads.sindex.query(sa, predicate="intersects")
r = roads.iloc[idx].copy()
r["geometry"] = r.geometry.intersection(sa)
r["km"] = r.geometry.length / 1000.0

by_class = r.groupby("MTFCC")["km"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(by_class.index, by_class.values, color="#3a6ea5")
ax.set_xlabel("total road length in study area (km)")
ax.set_title("Road length by MTFCC class (TIGER 2024, study area)", fontsize=10)
for i, v in enumerate(by_class.values):
    ax.text(v, i, f" {v:,.0f}", va="center", fontsize=7)
fig.savefig(FIGS / "roads_by_class.png", dpi=150, bbox_inches="tight")
plt.close(fig)

r["usage"] = r.MTFCC.map(USAGE).fillna("Other/non-vehicular")
by_use = r.groupby("usage")["km"].sum().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(6.5, 2.8))
ax.barh(by_use.index, by_use.values, color="#7c9c6b")
ax.set_xlabel("total road length in study area (km)")
ax.set_title("Road length by usage group", fontsize=10)
for i, v in enumerate(by_use.values):
    ax.text(v, i, f" {v:,.0f}", va="center", fontsize=8)
fig.savefig(FIGS / "roads_by_usage.png", dpi=150, bbox_inches="tight")
plt.close(fig)

t1 = pd.DataFrame({"MTFCC": by_class.index[::-1],
                   "Description": [DESC.get(c, "—") for c in by_class.index[::-1]],
                   "Length (km)": [f"{v:,.0f}" for v in by_class.values[::-1]]})
with open(TABLES / "mtfcc_codes.md", "w") as f:
    f.write(t1.to_markdown(index=False) + "\n")
t2 = pd.DataFrame({"Usage group": by_use.index[::-1],
                   "MTFCC classes": [", ".join(sorted(k for k, v in USAGE.items() if v == u)) or "all others"
                                     for u in by_use.index[::-1]],
                   "Length (km)": [f"{v:,.0f}" for v in by_use.values[::-1]]})
with open(TABLES / "mtfcc_usage.md", "w") as f:
    f.write(t2.to_markdown(index=False) + "\n")
print(f"study-area road km: {r.km.sum():,.0f} | classes: {len(by_class)}")
print("ROADS_EDA_COMPLETE")
