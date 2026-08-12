# nv-sagegrouse pipeline. `make v4` runs everything (lek data required locally;
# request from NDOW -- see data/MANIFEST.md). `make smoke` runs the CI-safe
# raster smoke test (public data only, tiny AOI).
SHELL := /bin/bash
EMAIL ?= you@example.com

help:
	@echo "targets: vectors dem vrm landfire roads design extract fit predict validate report v4 smoke"

vectors:
	uv run pipeline/fetch_vectors.py

dem:
	python3 pipeline/fetch_tnm.py --dataset "National Elevation Dataset (NED) 1 arc-second" \
	  --bbox="-120.01,35.0,-114.03,42.01" --manifest data/manifest-3dep-v4.json > data-local/dem/urls.txt
	mkdir -p data-local/dem/tiles && cd data-local/dem && xargs -P 4 -I{} curl -sL -O --output-dir tiles {} < urls.txt
	bash pipeline/build_dem.sh

vrm:
	uv run pipeline/build_vrm.py

landfire:
	mkdir -p data-local/landfire
	python3 pipeline/fetch_landfire.py --layer LF2025_EVT --bbox "-120.01 35.0 -114.03 42.01" \
	  --email $(EMAIL) --out data-local/landfire/evt.zip

roads:
	uv run pipeline/fetch_roads_all.py
	bash pipeline/build_roads_raster.sh
	bash pipeline/build_roads_by_class.sh

design:
	uv run pipeline/prepare_design.py

extract:
	uv run pipeline/extract_covariates.py
	uv run pipeline/extract_road_classes.py

fit:
	Rscript pipeline/fit_models.R

predict:
	uv run pipeline/build_prediction.py tag=v4

validate:
	Rscript pipeline/validate_spatial.R
	uv run pipeline/boyce.py
	uv run pipeline/validate_usgs.py

report:
	uv run pipeline/render_figures.py
	uv run pipeline/eda_figures.py
	quarto render reports/findings.qmd
	quarto render reports/paper.qmd

v4: vectors dem vrm landfire roads design extract fit predict validate report

smoke:
	bash pipeline/smoke_test.sh
