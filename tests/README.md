# tests

Adversarial test suite for the science pipeline. Every input is **synthetic** —
generated in `tmp_path` or constructed inline. No test reads `data-local/`, and CI
enforces that with a grep guard rather than trusting it.

## Run everything

```bash
make test
```

## Run the pieces

```bash
make test-unit          # pytest, synthetic data only
make test-unit-fast     # skips @pytest.mark.slow (subprocess + Rscript tests)
make test-r             # Rscript tests/test_r_models.R
make test-consistency   # report numbers vs reports/v4/ artifacts
```

The system `python3` on a GDAL/GRASS machine usually lacks pandas and rasterio, so
the suite runs through `uv`:

```bash
uv run --with pytest --with numpy --with pandas --with rasterio --with scipy \
  --with geopandas --with pyarrow --with pyogrio pytest tests/ -v
```

`tests/check_consistency.py` carries a PEP 723 header like the pipeline scripts:

```bash
uv run tests/check_consistency.py                    # full listing, untraced numbers included
uv run tests/check_consistency.py --quiet-warnings   # failures only
uv run tests/check_consistency.py --strict           # untraced numbers also fail
```

## What is covered

| File | Defends |
|---|---|
| `test_design_determinism.py` | seeded `sample_points` reproducibility; the real `prepare_design.py` run twice in a synthetic repo skeleton and compared **byte-for-byte**, then re-run with a changed seed |
| `test_aspect_direction.py` | the 0.5° Flat boundary (0.49 → Flat, 0.5 → compass, 0.51 → compass), all 8 compass bins at their edges, and that `extract_covariates.py` and `build_prediction.py` agree at every edge |
| `test_vrm.py` | flat plane = 0, any *constant* plane = 0, a hand-derived 2/9 case, rough ≫ smooth, range [0,1], and blocked-halo equivalence |
| `test_boyce.py` | Spearman on P/E — exact 1.0, exact 0.9, exact −1.0 counter-prediction, tie averaging, the NaN degenerate case, window overlap, and top-end truncation |
| `test_auc.py` | the base-R rank-sum AUC — hand-computed 0.75, all-ties 0.5, symmetry, monotone invariance, and a cross-check against `Rscript` running the pipeline's own function |
| `test_prediction_scoring.py` | the scorer's z-scaling and factor handling against a hand-computed 2×2 stack to 1e-9, plus the pandas/R/numpy sample-sd trap |
| `test_nodata.py` | nodata must not contaminate means, quantiles or focal windows |
| `test_r_models.R` | the 12 a priori formulas match a canonical list verbatim, the separation guard's 4-vs-5-used-lek boundary, AICc determinism, and the base-R VIF helper |
| `check_consistency.py` | every numeric claim in `reports/paper.qmd` and `reports/findings.qmd` against `reports/v4/` |

## `xfail` means "known bug"

Tests marked `@pytest.mark.xfail(strict=True)` assert the **correct** behaviour and
fail today. `strict=True` means they turn red if someone fixes the pipeline — that is
the signal to delete the xfail. Each one is written up in
[`FINDINGS.md`](./FINDINGS.md) with `file:line` and a repro.

Nothing in `pipeline/` was modified to make these pass.

## Known blocker

`reports/v4/*.csv` are excluded by the repo's blanket `*.csv` gitignore rule, so a
fresh clone has no artifacts and `check_consistency.py` exits **2**. The CI job runs
with `continue-on-error` until that is resolved — see `FINDINGS.md` **F1**.
