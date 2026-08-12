#!/usr/bin/env python3
"""prep_v3_betas.py -- translate the manuscript's Table 4 (reports/ground-truth/
coefficients_2024.csv) into the scorer's beta format. Stdlib only.

The manuscript reference class is unlisted (absorbed in the intercept); for
quantile-binned maps any constant offset is rank-invariant, so unlisted
classes score 0 and the comparison remains honest.
"""
import csv, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.reader(open(ROOT / "reports/ground-truth/coefficients_2024.csv")))
NAME_MAP = {"Intercept": "(Intercept)", "Ruggedness": "scale_Ruggedness",
            "Slope": "scale_Slope", "Elevation": "scale_Elevation",
            "Road Proximity": "scale_RoadsProximity"}
out = [("term", "Estimate")]
for r in rows[1:]:
    if len(r) < 2 or not r[1].strip():
        continue
    name, est = r[0].strip(), r[1].strip()
    try:
        val = float(est)
    except ValueError:
        continue
    if name in NAME_MAP:
        out.append((NAME_MAP[name], val))
    elif name.startswith("Direction "):
        out.append(("Direction" + name.split()[-1], val))
    else:
        clean = re.sub(r"\s+", " ", name.replace('"', "")).strip()
        if "Quarries" in clean:
            clean = "Quarries-Strip Mines-Gravel Pits-Well and Wind Pads"
        out.append((f"Vegetation{clean}", val))
with open(ROOT / "reports/ground-truth/betas_2024_scorer.csv", "w", newline="") as f:
    csv.writer(f).writerows(out)
print(f"{len(out)-1} coefficients translated")
