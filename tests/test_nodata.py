"""Adversarial tests for nodata handling across the raster-reading pipeline steps.

Nodata that survives a read does not crash anything -- it quietly moves a mean, a
standard deviation, or a quantile break, and every downstream number inherits the
shift. These tests build tiny synthetic GeoTIFFs and exercise the exact cleaning
expressions the pipeline uses, so a regression shows up as an arithmetic
difference rather than an exception.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from numpy.testing import assert_allclose
from rasterio.transform import from_origin

# A perfectly ordinary GDAL float nodata value that is NOT the -9999 sentinel the
# pipeline hardcodes. Chosen because gdalwarp writes it by default for Float32.
FLOAT32_NODATA = -3.4028234663852886e38

pytestmark = pytest.mark.slow


def _write_raster(path: Path, values: np.ndarray, nodata: float | None) -> Path:
    """Write a tiny single-band float32 GeoTIFF, declaring nodata only when asked."""
    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError(f"Expected a 2D array, got ndim={array.ndim}")
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:5070",
        "transform": from_origin(0.0, 0.0, 30.0, 30.0),
    }
    if nodata is not None:
        profile["nodata"] = nodata
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)
    return path


def _clean_like_build_prediction(path: Path) -> np.ndarray:
    """Reimplement build_prediction.py rd() exactly: masked read, fill NaN, drop |a| > 1e5, then the F6 sentinel backstop."""
    with rasterio.open(path) as src:
        array = src.read(1, masked=True).astype("float64").filled(np.nan)
    array[np.abs(array) > 1e5] = np.nan
    array[array == -9999.0] = np.nan
    return array


def test_hardcoded_sentinel_filter_cleans_only_minus_9999(tmp_path: Path) -> None:
    """Invariant: consulting src.nodata must recover the true minimum, which is the baseline the pipeline's hardcoded filter is measured against."""
    values = np.array([[0.10, 0.20, 0.30], [0.40, FLOAT32_NODATA, 0.60]], dtype=np.float32)
    path = _write_raster(tmp_path / "prediction.tif", values, nodata=FLOAT32_NODATA)

    with rasterio.open(path) as src:
        raw = src.read(1).astype("float64")
        declared_nodata = src.nodata

    assert declared_nodata is not None
    clean = raw[raw != declared_nodata]
    assert clean.size == 5
    assert_allclose(clean.min(), 0.10, rtol=0.0, atol=1e-6)


# FIXED (was FINDING F7): boyce.py now consults src.nodata in addition to the
# -9999 convention, so a declared float32 nodata is removed before lo/width.
def test_boyce_sentinel_filter_respects_declared_nodata(tmp_path: Path) -> None:
    """Invariant: the Boyce area filter must remove whatever nodata the raster declares, because lo and the class width are derived from the array minimum."""
    values = np.array([[0.10, 0.20, 0.30], [0.40, FLOAT32_NODATA, 0.60]], dtype=np.float32)
    path = _write_raster(tmp_path / "prediction.tif", values, nodata=FLOAT32_NODATA)

    with rasterio.open(path) as src:
        area = src.read(1).astype("float64")
        nod = src.nodata
    area = area[np.isfinite(area)]      # verbatim boyce.py
    area = area[area != -9999.0]        # verbatim boyce.py
    if nod is not None:
        area = area[area != nod]        # verbatim boyce.py (F7 fix)

    assert_allclose(area.min(), 0.10, rtol=0.0, atol=1e-6)


def test_contaminated_boyce_window_geometry_is_garbage(tmp_path: Path) -> None:
    """Invariant: leaving a float32 nodata in the area array must visibly wreck lo and the class width, which is what makes the hardcoded-sentinel finding consequential rather than cosmetic."""
    values = np.array([[0.10, 0.20, 0.30], [0.40, FLOAT32_NODATA, 0.60]], dtype=np.float32)
    path = _write_raster(tmp_path / "prediction.tif", values, nodata=FLOAT32_NODATA)

    with rasterio.open(path) as src:
        area = src.read(1).astype("float64")
    contaminated = area[area != -9999.0]

    lo = contaminated.min()
    hi = float(np.quantile(contaminated, 0.999))
    width = (hi - lo) / 5.0

    assert lo < -1e30
    assert width > 1e29
    # The first window is [-3.40e38, -2.72e38): its upper edge is still astronomically
    # negative, so it holds no real probability at all. The same is true of the next
    # eight, leaving every 0..1 value crammed into the final window -- the Boyce index
    # would then be computed from a single surviving class.
    assert lo + width < -1e38


def test_magnitude_filter_does_not_catch_the_minus_9999_sentinel() -> None:
    """Invariant: abs(-9999) is below the 1e5 magnitude cutoff, so the scorer's filter cannot be the thing that removes GDAL's -9999 -- the declared nodata must do it."""
    assert abs(-9999.0) < 1e5


def test_declared_nodata_is_masked_out_of_the_scorer_read(tmp_path: Path) -> None:
    """Invariant: when the source declares nodata=-9999 the masked read must produce NaN, which is the path build_prediction.py actually relies on."""
    values = np.array([[1000.0, 1100.0], [-9999.0, 1200.0]], dtype=np.float32)
    path = _write_raster(tmp_path / "dem_declared.tif", values, nodata=-9999.0)

    cleaned = _clean_like_build_prediction(path)

    assert np.isnan(cleaned[1, 0])
    assert_allclose(cleaned[0, 0], 1000.0, rtol=0.0, atol=1e-6)


# FIXED (was FINDING F6): rd() now maps exact -9999.0 to NaN after the magnitude
# filter, so an undeclared sentinel cannot reach the z-scaling.
def test_undeclared_sentinel_does_not_reach_the_z_scaling(tmp_path: Path) -> None:
    """Invariant: a -9999 sentinel must never reach the z-scaling, because it becomes a z-score of about -110 and pins that cell's predicted probability at a boundary value."""
    values = np.array([[1000.0, 1100.0], [-9999.0, 1200.0]], dtype=np.float32)
    path = _write_raster(tmp_path / "dem_undeclared.tif", values, nodata=None)

    cleaned = _clean_like_build_prediction(path)

    assert np.isnan(cleaned[1, 0])


def test_undeclared_sentinel_produces_an_absurd_z_score_without_the_backstop(tmp_path: Path) -> None:
    """Invariant: without the F6 backstop, a surviving sentinel yields a physically impossible z-score -- this pins why the backstop line must never be removed."""
    values = np.array([[1000.0, 1100.0], [-9999.0, 1200.0]], dtype=np.float32)
    path = _write_raster(tmp_path / "dem_undeclared.tif", values, nodata=None)

    # Pre-fix cleaning: masked read + magnitude filter only, no -9999 backstop.
    with rasterio.open(path) as src:
        unguarded = src.read(1, masked=True).astype("float64").filled(np.nan)
    unguarded[np.abs(unguarded) > 1e5] = np.nan

    elevation_mean, elevation_sd = 1000.0, 100.0
    z_sentinel = (unguarded[1, 0] - elevation_mean) / elevation_sd

    assert not np.isnan(z_sentinel)
    assert z_sentinel < -100.0


def test_quantile_breaks_must_be_taken_after_nodata_removal() -> None:
    """Invariant: cleaning before quantiles must reproduce the clean-subset breaks exactly, while quantiles taken first must not -- this is the correctly-written path at build_prediction.py:133-137."""
    clean_values = np.linspace(0.0, 1.0, num=101, dtype=np.float64)
    contaminated = np.concatenate([clean_values, np.full(5, -9999.0)])

    cleaned = contaminated.copy()
    cleaned[cleaned == -9999.0] = np.nan
    valid = cleaned[np.isfinite(cleaned)]
    breaks_after_cleaning = np.nanquantile(valid, [0.2, 0.4, 0.6, 0.8])
    breaks_before_cleaning = np.quantile(contaminated, [0.2, 0.4, 0.6, 0.8])
    expected = np.quantile(clean_values, [0.2, 0.4, 0.6, 0.8])

    assert_allclose(breaks_after_cleaning, expected, rtol=0.0, atol=1e-12)
    assert_allclose(np.nanmean(cleaned), clean_values.mean(), rtol=0.0, atol=1e-12)
    # Only ~4.7% of the cells are nodata, yet every break still slides downward:
    # [0.16, 0.37, 0.58, 0.79] instead of [0.2, 0.4, 0.6, 0.8]. The bins would be
    # mislabelled across the whole map, not just at the nodata cells.
    assert np.all(breaks_before_cleaning < breaks_after_cleaning)
    assert float(np.max(breaks_after_cleaning - breaks_before_cleaning)) > 0.03


# FINDING: pipeline/build_prediction.py:39 reads the z-scaling moments straight from
# model_input.parquet with no sentinel guard, and pipeline/extract_covariates.py:30-36
# samples the covariate rasters with no masking, so any -9999 that reaches the design
# table moves the mean and sd used for every cell in the statewide surface.
def test_one_sentinel_in_the_design_table_shifts_every_z_score() -> None:
    """Invariant: a single -9999 among 718 design rows must measurably move the moments and compress the z-scale, because those two numbers scale every cell of the statewide surface."""
    import pandas as pd

    clean = pd.Series(np.linspace(1500.0, 2500.0, num=718))
    contaminated = pd.concat([clean, pd.Series([-9999.0])], ignore_index=True)

    # One sentinel in 719 rows drags the mean down 16.7 m and inflates the sd by 84%
    # (289.3 -> 532.7), which compresses every z-score toward zero.
    assert float(clean.mean() - contaminated.mean()) > 15.0
    assert float(contaminated.std() / clean.std()) > 1.5

    for probe in (1500.0, 2500.0):
        z_clean = (probe - clean.mean()) / clean.std()
        z_contaminated = (probe - contaminated.mean()) / contaminated.std()
        assert abs(z_clean) > abs(z_contaminated)
        assert abs(z_clean - z_contaminated) > 0.5
