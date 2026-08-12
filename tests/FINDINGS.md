# Findings — pipeline review notes from writing the test suite

Written while building `tests/`. **Nothing in `pipeline/` was modified.** Where a
finding is an actual defect, the test that demonstrates it is marked
`@pytest.mark.xfail(strict=True)`: it fails today, so the suite stays green, and it
turns **red** the moment someone fixes the pipeline — which is the signal to delete
the xfail. Every entry carries `file:line` and a one-line repro.

Severity: **A** = affects a published number · **B** = latent correctness hazard ·
**C** = maintainability / process.

---

## F1 — `reports/v4/*.csv` are gitignored, so CI cannot verify any claim · **A**

`.gitignore:2` is a blanket `*.csv` with only `!versions/*.csv` negated. Every
artifact the manuscript quotes — `averaged_betas.csv`, `diagnostics.csv`,
`spatial_validation.csv`, `boyce_pe.csv`, `calibration.csv`, `model_selection.csv` —
is therefore untracked. `git ls-files reports/v4/` returns only `.md` tables, `.png`
figures and `usgs_validation.txt`.

Consequence: on a fresh clone (including CI) `tests/check_consistency.py` has nothing
to check against and exits **2 (artifacts missing)**. The consistency gate cannot run
in CI until this is resolved.

These files hold aggregate statistics only — coefficients, AUCs, AICc weights,
decile means. **No coordinates.** They are strictly less sensitive than the
already-committed `reports/paper.pdf`, which prints the same numbers.

**Repro:** `git check-ignore -v reports/v4/averaged_betas.csv`
**Suggested fix (Ryan's call — a data-policy decision, so I did not make it):** add
`!reports/v4/*.csv` to `.gitignore` and `git add reports/v4/*.csv`. The CI job added
in `.github/workflows/smoke.yml` runs the checker in a soft-fail mode until then; see
`tests/README.md`.

---

## F2 — `spatial_validation.csv` is stale relative to `diagnostics.csv` · **A**

`pipeline/validate_spatial.R:63` copies the random-fold AUC straight out of
`diagnostics.csv`:

```r
read.csv(file.path(root, "reports/v4/diagnostics.csv"))$value[2]
```

so the two files must agree by construction. They do not:

| file | value |
|---|---|
| `diagnostics.csv` -> `AUC (5-fold CV, top model)` | `0.799831009900665` |
| `spatial_validation.csv` -> `random-fold AUC (reference)` | `0.791` |

The copied value is written unrounded, so a stored `0.791` means it was copied when
`diagnostics.csv` still held `0.791`. `fit_models.R` has since been rerun and
`validate_spatial.R` has not. **This is the one failing check in
`tests/check_consistency.py` and it is a true positive.**

The paper does not quote `0.791` directly, so no published number is wrong *yet* —
but the paper does claim the spatially blocked AUC is "indistinguishable from the
random-fold value" (`paper.qmd:452-453`, `findings.qmd:209`), and that comparison is
currently drawn against a stale reference.

**Repro:** `uv run tests/check_consistency.py` -> the single FAIL line.
**Fix:** rerun `Rscript pipeline/validate_spatial.R` so the artifacts come from one
run. Longer term, `make validate` should always run both, or the reference value
should be read at report-render time rather than frozen into a CSV.

---

## F3 — nodata aspect (`-9999`) is silently labelled North · **B**

`pipeline/extract_covariates.py:40`

```python
if a is None or a != a or a < 0: return "N"
```

`gdaldem aspect` writes `-9999` for nodata. That value takes the `a < 0` branch and
becomes a real modelling category, `"N"`. NaN takes the `a != a` branch to the same
place. Missing data should be excluded, not folded into a compass bin whose
coefficient the paper interprets (`paper.qmd:437-439`).

**Repro:** `direction(-9999.0)` returns `"N"`.
**Test:** `tests/test_aspect_direction.py::test_nodata_aspect_is_not_folded_into_north` (xfail).

---

## F4 — nodata slope (`-9999`) is silently labelled Flat · **B**

`pipeline/extract_covariates.py:48`

```python
pts["direction"] = _np.where(pts.slope < 0.5, "Flat", pts.aspect_deg.map(direction))
```

`-9999 < 0.5` is `True`, so any point sampling nodata slope is classified `"Flat"`.
`DirectionFlat` is one of the paper's headline effects (beta = -1.20, `paper.qmd:429`),
interpreted as "playa and lake-bed surfaces". Nodata pixels would be pooled into
exactly that category.

Note the asymmetry with the scorer: `build_prediction.py:115` computes `flat = slope < 0.5`
on an array where nodata has already become NaN, and `NaN < 0.5` is `False`. So the
same physical cell can be "Flat" in training and "not Flat" in prediction.

**Repro:** a row with `slope = -9999` gets `direction == "Flat"`.
**Test:** `tests/test_aspect_direction.py::test_nodata_slope_is_not_folded_into_flat` (xfail).

---

## F5 — VRM reads slope/aspect unmasked, so one nodata cell poisons its eight neighbours · **B**

`pipeline/build_vrm.py:34-35` reads with plain `.read(1)` — no `masked=True`, no
nodata handling — then pushes the values through `deg2rad`/`sin`/`cos` and a 3x3
`uniform_filter`. A single `-9999` cell therefore contaminates the focal mean of all
eight neighbours, not just itself.

Compounding it, `build_vrm.py:27` writes `nodata=None` into the output profile, so
downstream `masked=True` reads of `nv_vrm_5070.tif` cannot recover the boundary
either — and `build_prediction.py:96-98` only discards `|a| > 1e5`, which a
corrupted VRM value near 0-1 will never trip.

**Repro:** constant 30deg/135deg field (true VRM == 0) with one `-9999` cell -> the eight
neighbours are no longer 0.
**Test:** `tests/test_vrm.py::test_nodata_does_not_poison_neighboring_vrm_cells` (xfail).

---

## F6 — the scorer's magnitude filter cannot catch a `-9999` sentinel · **B**

`pipeline/build_prediction.py:96-98`

```python
a = srcs[k].read(1, window=win, masked=True).astype("float64").filled(np.nan)
a[np.abs(a) > 1e5] = np.nan
```

`abs(-9999) = 9999 < 1e5`. The sentinel is removed **only** if the source raster
declares `nodata` in its profile; the magnitude filter is not a backstop. Any
covariate COG that carries `-9999` without declaring it flows into the z-scaling at
`build_prediction.py:104` and produces a z-score around -110, saturating the logistic
for that cell.

**Repro:** write a GeoTIFF with a `-9999` cell and `nodata=None`; the cleaning
expression leaves it intact.
**Test:** `tests/test_nodata.py::test_undeclared_sentinel_should_not_reach_the_z_scaling`
(xfail), plus the passing
`test_undeclared_sentinel_produces_an_absurd_z_score` which quantifies the damage.

---

## F7 — `boyce.py` hardcodes the nodata sentinel instead of reading `src.nodata` · **B**

`pipeline/boyce.py:26`

```python
area = area[area != -9999.0]
```

The prediction raster currently declares `nodata = -9999.0`
(`build_prediction.py:82`), so this works **today** by coincidence of the two
constants agreeing. Change the writer's nodata — or point `boyce.py` at any raster
produced by another tool — and the sentinel survives. Because `boyce.py:30` then
takes `lo = area.min()` and `width = (hi - lo)/5`, a single surviving float32 nodata
(-3.4e38) relocates all ten probability classes: the first window's upper edge is
still about -2.7e38, so every real probability lands in the last window and the index
is computed from one class.

**Repro:** `tests/test_nodata.py::test_contaminated_boyce_window_geometry_is_garbage`
(passing — it demonstrates the magnitude of the hazard);
`test_boyce_sentinel_filter_should_respect_declared_nodata` (xfail — demands the fix).

---

## F8 — a degenerate surface yields `BOYCE_INDEX: nan` with no guard · **B**

`pipeline/boyce.py:42` computes `np.corrcoef` on the rank vectors. If every P/E ratio
is equal — a surface with no discrimination, exactly the case the index exists to
detect — the rank vector has zero variance and `corrcoef` returns NaN. That NaN is
printed as the headline result (`boyce.py:63`), written into `boyce_pe.csv`
(`boyce.py:48-49`) and formatted into `boyce.md` (`boyce.py:51`) as
`**Continuous Boyce index: nan**`. Nothing raises.

**Repro:** `boyce_index([0.1..0.5], [2.0]*5)` -> NaN.
**Test:** `tests/test_boyce.py::test_constant_pe_ratio_is_undefined_and_returns_nan`
(passing — it pins current behaviour so the NaN path is at least documented).

---

## F9 — the ten Boyce "classes" overlap, so the observed shares are not a partition · **C**

`pipeline/boyce.py:31-33` sets `width = (hi - lo)/5.0` — one fifth of the range — but
steps through **ten** windows. Consecutive windows overlap by roughly 55% of their
span, so a single used lek is counted in about 1.8 classes and the ten `obs` shares
sum to about 1.6 rather than 1.

This is a legitimate Hirzel-style *moving window* and the module docstring
(`boyce.py:7`) says so, so it is not a defect. It is flagged because the prose
describes P/E as "the share of used leks falling in the class divided by the share of
study-area cells in it" (`paper.qmd:221-224`), which reads as a partition. The
resulting P/E values are autocorrelated, so the Spearman index across them is more
stable than ten independent bins would be — worth a sentence in Methods before a
reviewer asks.

**Repro:** `tests/test_boyce.py::test_overlapping_windows_double_count_used_points` (passing).

---

## F10 — the highest-suitability leks are excluded from every Boyce class · **B**

`hi = np.quantile(area, 0.999)` (`boyce.py:30`) and the final window ends at `hi`
with a strict `<` (`boyce.py:35`). Any used lek whose predicted probability is `>= hi`
therefore falls into **no** class and contributes to no `obs`. Those are the
top-suitability leks — precisely the ones carrying the claim that "lek density rises
nearly monotonically across the predicted-suitability gradient"
(`paper.qmd:456-459`).

**Repro:** `tests/test_boyce.py::test_used_points_above_hi_are_dropped_from_every_class`
(passing) — every `obs` is exactly 0 when all used points sit above `hi`.

---

## F11 — the z-scaling moments are read from the design table with no sentinel guard · **B**

`pipeline/build_prediction.py:39`

```python
SC = {c: (mi[c].mean(), mi[c].std()) for c in (...)}
```

and `extract_covariates.py:30-36` samples every covariate raster with no masking at
all. Any sentinel that reaches `model_input.parquet` moves the mean and standard
deviation used to scale **every cell of the statewide surface**, not just the bad
rows. One `-9999` among 718 elevation rows drags the mean down 16.7 m and inflates
the sd by 84% (289.3 -> 532.7), compressing every z-score toward zero.

**Repro:** `tests/test_nodata.py::test_one_sentinel_in_the_design_table_shifts_every_z_score` (passing).

---

## F12 — `validate_spatial.R` has no Shrubland fallback but `fit_models.R` does · **C**

`pipeline/fit_models.R:42` picks the reference level defensively:

```r
rf <- if ("Shrubland" %in% veg) "Shrubland" else names(sort(table(veg), decreasing=TRUE))[1]
```

`pipeline/validate_spatial.R:24` does not:

```r
rsf$Vegetation <- relevel(as.factor(veg), ref = "Shrubland")
```

If the separation guard ever pools Shrubland away — or a future study area lacks it —
`fit_models.R` proceeds and `validate_spatial.R` dies with
`'ref' must be an existing level`. Two scripts that reimplement the same six
preprocessing steps (`fit_models.R:23-42` vs `validate_spatial.R:13-26`) have already
drifted; that duplication is the underlying issue.

**Repro:** run `validate_spatial.R` on a design whose vegetation column has no
`Shrubland`.

---

## F13 — `validate_spatial.R` indexes `diagnostics.csv` positionally · **C**

`pipeline/validate_spatial.R:63` reads `...$value[2]` — row order, not metric name.
Insert a metric into `diag_df` at `fit_models.R:103-104` and this silently starts
copying the wrong number into `spatial_validation.csv` under the label
"random-fold AUC (reference)". Directly related to **F2**.

**Fix:** index by name, e.g.
`d$value[d$metric == "AUC (5-fold CV, top model)"]`.

---

## F14 — `cut()` on quantile breaks will error on tied predictions · **C**

`pipeline/fit_models.R:98`

```r
dec <- cut(p_full, quantile(p_full, seq(0, 1, 0.1)), include.lowest = TRUE, labels = FALSE)
```

If the fitted probabilities tie across a decile boundary the breaks are non-unique
and `cut()` stops with `'breaks' are not unique`, taking down the calibration and
diagnostics steps at the very end of a long fit. Not currently triggered — the
current fit has no such ties — but it is a hard failure when it happens.

**Fix:** `unique()` the breaks, or use `rank`-based deciles.

---

## F15 — dead assignments in `build_prediction.py` · **C**

`pipeline/build_prediction.py:154-155`

```python
cell_km2 = (30 * 30) / 1e6
n_valid_full = None
```

Neither is read anywhere in the file. `n_valid_full = None` in particular looks like
the remnant of a removed area-reporting path.

**Repro:** `grep -n 'cell_km2\|n_valid_full' pipeline/build_prediction.py` -> each
appears exactly once.

---

## F16 — the `tri` column holds VRM, not TRI · **C**

`pipeline/extract_covariates.py:36` assigns the **VRM** raster to a column named
`tri`, and `fit_models.R:31` maps `rsf$tri` to `scale_Ruggedness`. The comment at
`extract_covariates.py:33-35` explains the history and explicitly warns that the real
Riley TRI must not be modelled (about 0.995 correlated with slope) — so the behaviour
is correct and deliberate, but the name now says the opposite of what it holds. A
future edit that "fixes" the column to point at `nv_tri_5070.tif` would silently
swap the ruggedness instrument and change every reported coefficient.

`build_prediction.py:39` inherits the same name for the moment key.

---

## Verified NOT a problem

Recorded so nobody "fixes" these into bugs:

- **`predict(avg)` vs `coefmat.full`.** `fit_models.R:71` reports full-average
  coefficients while `fit_models.R:90` predicts from the averaging object. In the
  installed MuMIn, `predict.averaging` defaults to `full = TRUE`
  (`args(MuMIn:::predict.averaging)`), so the AUC and the published betas come from
  the same averaging. Do not "align" this by passing `full = FALSE`.
- **Aspect binning agrees across languages.** `extract_covariates.py:41-42` (an
  upper-inclusive ladder) and `build_prediction.py:116-121` (interval tuples with
  `(aspect > lo) & (aspect <= hi)`) produce identical labels at every bin edge,
  including the 337.5/360/0 wrap and the (67.5, 112.5] east reference. Verified over
  the full edge sweep by
  `tests/test_aspect_direction.py::test_build_prediction_bins_match_extract_covariates_at_every_edge`.
- **The Flat threshold is consistent.** Both scripts use a strict `slope < 0.5`, so
  exactly 0.5 deg is a compass bin in training and in prediction.
- **Sample-sd convention is consistent across languages.** `build_prediction.py:39`
  uses pandas `.std()` (ddof=1) and `fit_models.R:24-32` uses R `scale()` (also
  ddof=1). Cross-checked against `Rscript` in
  `tests/test_prediction_scoring.py::test_pandas_std_matches_r_scale_sd`. Swapping in
  `numpy.std()` (ddof=0) would rescale every covariate by `sqrt(n/(n-1))` with no
  error raised.
- **The blocked VRM halo arithmetic is correct.** `build_vrm.py:30-43` reproduces the
  whole-array result exactly (`tests/test_vrm.py::test_block_halo_matches_whole_array_computation`).
- **The base-R AUC is a proper tie-aware Mann-Whitney statistic.** Cross-checked
  against `Rscript` itself in
  `tests/test_auc.py::test_python_rank_sum_auc_matches_rscript_reference_examples`.

---

## Not investigated

- `validate_usgs.py:56` samples 150,000 points with `rng=99`, a different seed from
  the pipeline's `20260811`. Reproducible, but the choice is undocumented.
- `validate_usgs.py:40` scores candidate rasters with a hand-tuned keyword heuristic
  (`"select"*4 + "hsi"*3 + ...`). If ScienceBase renames a file the script may
  silently select a different raster; the selected name is printed and stored in
  `usgs_validation.txt`, so it is auditable after the fact but not pinned.
- The 12 a priori formulas were checked for drift against a canonical hardcoded list
  (`tests/test_r_models.R`) but **not** against
  `history/ModAvg_ActiveOnly_LandJournal.R` itself — the "verbatim from 2023" claim
  at `fit_models.R:2` is pinned to my transcription, not to the historical file.

---

## Resolution log (Cairn, 2026-08-12)

- **F1 RESOLVED** — `.gitignore` now negates `reports/v4/*.csv` (aggregate
  statistics only, no coordinates; verified by inspection of all 8 files). The
  CI `report-consistency` job is a hard gate (`continue-on-error` removed).
- **F2 FIXED** — `Rscript pipeline/validate_spatial.R` rerun; seeded k-means
  reproduced identical folds (0.777/0.834/0.835/0.744/0.812), only the stale
  reference row changed (0.791 → 0.7998). Checker now 51/51. No published
  number was affected.
- **F9 ADDRESSED in prose** — `paper.qmd` Methods now describes the Boyce
  classes as overlapping moving windows, not a partition.
- **Formula verbatim-ness CLOSED** — `fit_models.R:45-56` compared directly
  against `history/ModAvg_ActiveOnly_LandJournal.R:216-227`: term-for-term
  identical, m1–m12, same order (whitespace and `=`/`<-` only).
- **F3–F8, F10–F16 OPEN** — pipeline-code changes; Ryan's call per the
  surgical-fixes rule. The strict xfail tests will flip red when fixed.
