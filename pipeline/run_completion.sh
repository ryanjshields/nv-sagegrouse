#!/usr/bin/env bash
# run_completion.sh -- everything between "roads data" and "both prediction maps".
# No output pipes: every failure propagates.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== [1/7] fetch all TIGER roads (patient retries; Census is flaky tonight)"
ok=0
for i in $(seq 1 25); do
  if uv run pipeline/fetch_roads_all.py; then ok=1; break; fi
  echo "--- fetch attempt $i failed; sleeping 180s"
  sleep 180
done
[ "$ok" -eq 1 ] || { echo "CENSUS_UNREACHABLE_AFTER_25_ATTEMPTS"; exit 1; }

echo "=== [2/7] distance-to-roads surface"
bash pipeline/build_roads_raster.sh

echo "=== [3/7] covariate extraction"
uv run pipeline/extract_covariates.py

echo "=== [4/7] model fit + diagnostics"
Rscript pipeline/fit_models.R

echo "=== [5/7] v4 prediction surface"
uv run pipeline/build_prediction.py tag=v4

echo "=== [6/7] v3-replica prediction surface (2024 betas, Eq.1-binary ruggedness, LF2016 EVT)"
uv run pipeline/build_prediction.py \
  betas=reports/ground-truth/betas_2024_scorer.csv \
  rugg=eq1binary \
  evt=data-local/landfire/lf2016/evt2016_5070_30.tif \
  vat=data-local/landfire/lf2016/evt2016_vat.csv \
  tag=v3replica

echo "=== [7/7] old-vs-new comparison"
uv run pipeline/compare_predictions.py

echo "FULL_CHAIN_COMPLETE"
