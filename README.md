# nv-sagegrouse

Replicable Resource Selection Function (RSF) analysis of Greater Sage-Grouse
lek site selection in Nevada. Rebuilt 2026 as a version-configured, open,
cloud-native pipeline; successor to the 2021-2024 analyses behind
*Predicting fine-scale lek site selection of Greater Sage-Grouse
(Centrocercus urophasianus) in Nevada, USA* (McGinn et al., unpublished).

## Stack

GDAL · Python 3 (stdlib fetchers; `uv run` scripts with inline deps) · DuckDB · R
(model step only — 12 a priori GLMs, AICc, top-3 model averaging).
No GIS suite installs required.

## Structure

- `versions/` — one YAML per analysis era. The configs ARE the narrative:
  `v4-2026-latest.yaml` is canonical (current 3DEP + LANDFIRE, VRM ruggedness,
  seeded 1:10 design). Earlier eras are being backfilled as configs.
- `pipeline/` — fetch and build steps, in run order:
  `fetch_tnm.py` (3DEP tiles, vintage-deduped + manifested) →
  `build_dem.sh` (COG mosaic + slope/aspect/TRI) →
  `build_vrm.py` (Vector Ruggedness Measure, Sappington et al. 2007) →
  `fetch_landfire.py` (LFPS v2 API) →
  `prepare_design.py` (study area, used/available points) →
  `extract_covariates.py` → `fit_models.R`
- `reports/` — generated model outputs per version (no coordinates).
- `history/` — verbatim provenance: the 2022/2023 analysis code as received,
  and `2023-rebuild/` (the December 2023 PostGIS/R modular pipeline and its
  results, superseded by `pipeline/`).
- `data/` — manifests only. **No data lives in git.**

## Data access

Terrain, vegetation, and roads inputs are public (USGS 3DEP, LANDFIRE, TIGER);
the fetch scripts pull them and write provenance manifests. **Lek locations are
sensitive wildlife data** and are not distributed here or in any public bucket —
request them from the Nevada Department of Wildlife. The pipeline reads them
from a private bucket; see `data/MANIFEST.md`.

## Notable methods corrections (2026)

- The manuscript's Equation 1 ruggedness is a DEM-texture statistic that was
  additionally binarized by an integer-raster step in the original workflow;
  v4 replaces it with VRM. Legacy rasters are still built for era replication.
- The manuscript's study-area figure (~3,548 km²) is inconsistent with the
  range polygon (152,458 km²); the operative design is 10 available points
  per used lek.
