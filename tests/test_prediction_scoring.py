"""Adversarial tests for the raster scorer in pipeline/build_prediction.py.

The scorer is module-level code that opens seven real COGs, so it cannot be
imported. These tests reimplement its arithmetic verbatim (see
build_prediction.py:104-125) and pin it against hand-computed values, plus the
cross-language z-scaling trap that would silently rescale every covariate.
"""
from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

# Betas and moments used by the hand-computed 2x2 case. Kept module-level so the
# arithmetic in the comments below can be checked against exactly these numbers.
BETAS: dict[str, float] = {
    "(Intercept)": -2.0,
    "scale_Ruggedness": -1.0,
    "scale_Slope": -1.5,
    "scale_Elevation": 0.5,
    "scale_Curvature": -0.25,
    "scale_RoadsProximity": 0.1,
    "DirectionFlat": -1.2,
    "DirectionN": -0.1,
    "DirectionS": 0.3,
    "VegetationGrassland": 0.4,
    "VegetationOther": -2.5,
}

MOMENTS: dict[str, tuple[float, float]] = {
    "elevation": (1000.0, 100.0),
    "slope": (10.0, 5.0),
    "tri": (0.002, 0.001),
    "curvature": (0.0, 0.2),
    "dist_road_m": (800.0, 400.0),
}

# Verbatim from build_prediction.py:116-118. "E" is absent on purpose: it is the
# reference level and contributes 0.0, exactly as the pipeline leaves dir_arr at 0.
COMPASS_BINS: dict[str, tuple[float, float]] = {
    "N": (337.5, 22.5),
    "NE": (22.5, 67.5),
    "SE": (112.5, 157.5),
    "S": (157.5, 202.5),
    "SW": (202.5, 247.5),
    "W": (247.5, 292.5),
    "NW": (292.5, 337.5),
}


def _beta(name: str) -> float:
    """Mirror build_prediction.py:45 -- an absent term contributes zero, not an error."""
    return float(BETAS.get(name, 0.0))


def _z(values: np.ndarray, key: str) -> np.ndarray:
    if key not in MOMENTS:
        raise KeyError(f"No z-scaling moments registered for {key!r}")
    mean, sd = MOMENTS[key]
    if sd == 0.0:
        raise ValueError(f"Cannot z-scale {key!r} with zero standard deviation")
    return (np.asarray(values, dtype=np.float64) - mean) / sd


def direction_beta_grid(aspect_deg: np.ndarray, slope_deg: np.ndarray) -> np.ndarray:
    """Reimplement build_prediction.py:114-121: compass bins first, Flat override last."""
    aspect = np.asarray(aspect_deg, dtype=np.float64)
    slope = np.asarray(slope_deg, dtype=np.float64)
    if aspect.shape != slope.shape:
        raise ValueError(f"Expected matching shapes, got {aspect.shape} and {slope.shape}")

    contribution = np.zeros_like(aspect)
    for label, (lo, hi) in COMPASS_BINS.items():
        if lo < hi:
            selected = (aspect > lo) & (aspect <= hi)
        else:
            # North wraps the 360/0 seam, so the two half-open pieces are OR-ed.
            selected = (aspect > lo) | (aspect <= hi)
        contribution[selected] = _beta(f"Direction{label}")
    contribution[slope < 0.5] = _beta("DirectionFlat")
    return contribution


def score_stack(
    dem: np.ndarray,
    slope: np.ndarray,
    aspect: np.ndarray,
    vrm: np.ndarray,
    curvature: np.ndarray,
    dist_road: np.ndarray,
    vegetation_beta: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reimplement the linear predictor and logistic of build_prediction.py:105-123."""
    shapes = {a.shape for a in (dem, slope, aspect, vrm, curvature, dist_road, vegetation_beta)}
    if len(shapes) != 1:
        raise ValueError(f"Expected one common raster shape, got {sorted(shapes)}")

    eta = (
        _beta("(Intercept)")
        + _beta("scale_Ruggedness") * _z(vrm, "tri")
        + _beta("scale_Slope") * _z(slope, "slope")
        + _beta("scale_Elevation") * _z(dem, "elevation")
        + _beta("scale_Curvature") * _z(curvature, "curvature")
        + _beta("scale_RoadsProximity") * _z(dist_road, "dist_road_m")
    )
    eta = eta + direction_beta_grid(aspect, slope) + np.asarray(vegetation_beta, dtype=np.float64)
    return eta, 1.0 / (1.0 + np.exp(-eta))


def test_two_by_two_stack_matches_hand_computed_eta_and_probability() -> None:
    """Invariant: the scorer's z-scaling, factor handling and logistic must reproduce hand-derived values, because a silent sign or moment error would shift the whole statewide surface without any test noticing."""
    dem = np.array([[1100.0, 900.0], [1000.0, 1200.0]])
    slope = np.array([[20.0, 0.2], [10.0, 30.0]])
    aspect = np.array([[180.0, 0.0], [10.0, 100.0]])
    vrm = np.array([[0.003, 0.001], [0.002, 0.004]])
    curvature = np.array([[0.2, -0.2], [0.0, 0.4]])
    dist_road = np.array([[1200.0, 400.0], [800.0, 1600.0]])
    vegetation = np.array(
        [[_beta("VegetationGrassland"), 0.0], [_beta("VegetationOther"), _beta("VegetationGrassland")]]
    )

    eta, probability = score_stack(dem, slope, aspect, vrm, curvature, dist_road, vegetation)

    # Cell 00: z = elev 1.0, slope 2.0, vrm 1.0, curv 1.0, road 1.0; aspect 180 -> S.
    #   -2.0 + (-1.0*1.0) + (-1.5*2.0) + (0.5*1.0) + (-0.25*1.0) + (0.1*1.0) + 0.3 + 0.4 = -4.95
    # Cell 01: slope 0.2 < 0.5 -> Flat beta despite aspect 0; z_slope = (0.2-10)/5 = -1.96.
    #   -2.0 + (-1.0*-1.0) + (-1.5*-1.96) + (0.5*-1.0) + (-0.25*-1.0) + (0.1*-1.0) + (-1.2) + 0.0 = 0.39
    expected_eta = np.array([[-4.95, 0.39], [-4.60, -8.90]])
    expected_probability = np.array(
        [[0.007033587154995161, 0.5962826992967879], [0.009951801866904324, 0.00013637032707949703]]
    )

    assert_allclose(eta, expected_eta, rtol=0.0, atol=1e-9)
    assert_allclose(probability, expected_probability, rtol=0.0, atol=1e-9)


@pytest.mark.parametrize("slope_value", [0.0, 0.49, 0.4999])
def test_slope_below_half_degree_takes_the_flat_beta(slope_value: float) -> None:
    """Invariant: sub-0.5-degree cells must take DirectionFlat even when aspect reads due north, because gdaldem writes aspect 0 for flat ground and folding it into N would contaminate the aspect effects."""
    contribution = direction_beta_grid(np.array([[0.0]]), np.array([[slope_value]]))
    assert contribution[0, 0] == _beta("DirectionFlat")


@pytest.mark.parametrize("slope_value", [0.5, 0.51, 5.0])
def test_slope_at_or_above_half_degree_takes_the_compass_beta(slope_value: float) -> None:
    """Invariant: the Flat threshold is a strict less-than, so exactly 0.5 must fall through to the compass bin -- the most likely off-by-one in the whole scorer."""
    contribution = direction_beta_grid(np.array([[0.0]]), np.array([[slope_value]]))
    assert contribution[0, 0] == _beta("DirectionN")


def test_east_and_shrubland_reference_levels_contribute_exactly_zero() -> None:
    """Invariant: E aspect and Shrubland vegetation are the model's reference levels, so their contribution must be exactly 0.0 or every other coefficient is silently re-based."""
    east = direction_beta_grid(np.array([[100.0]]), np.array([[10.0]]))
    assert east[0, 0] == 0.0

    common = dict(
        dem=np.array([[1000.0]]),
        slope=np.array([[10.0]]),
        vrm=np.array([[0.002]]),
        curvature=np.array([[0.0]]),
        dist_road=np.array([[800.0]]),
    )
    eta_reference, _ = score_stack(aspect=np.array([[100.0]]), vegetation_beta=np.array([[0.0]]), **common)
    eta_south, _ = score_stack(aspect=np.array([[180.0]]), vegetation_beta=np.array([[0.0]]), **common)
    eta_grassland, _ = score_stack(
        aspect=np.array([[100.0]]), vegetation_beta=np.array([[_beta("VegetationGrassland")]]), **common
    )

    # At the reference cell every z-score is zero, so eta collapses to the intercept.
    assert_allclose(eta_reference, [[-2.0]], rtol=0.0, atol=1e-12)
    assert_allclose(eta_south - eta_reference, [[_beta("DirectionS")]], rtol=0.0, atol=1e-12)
    assert_allclose(eta_grassland - eta_reference, [[_beta("VegetationGrassland")]], rtol=0.0, atol=1e-12)


# FINDING: pipeline/build_prediction.py:39 builds the z-scaling moments with pandas .std()
# (ddof=1). pipeline/fit_models.R:24-32 z-scales with R scale(), also ddof=1, so they agree
# today -- but numpy's .std() defaults to ddof=0, and swapping it in would rescale every
# covariate with no error raised anywhere.
def test_pandas_std_is_sample_sd_and_numpy_default_is_not() -> None:
    """Invariant: the scorer's moments must stay sample-sd (ddof=1) to match R's scale(); this pins the exact sqrt(n/(n-1)) gap that a numpy swap would introduce."""
    column = pd.Series([1000.0, 1100.0, 1200.0, 900.0, 1050.0])
    n = len(column)

    pandas_sd = float(column.std())
    numpy_sd = float(np.std(column.to_numpy()))

    assert pandas_sd != numpy_sd
    assert_allclose(pandas_sd, numpy_sd * np.sqrt(n / (n - 1)), rtol=0.0, atol=1e-12)

    mean = float(column.mean())
    z_pandas = (column.to_numpy() - mean) / pandas_sd
    z_numpy = (column.to_numpy() - mean) / numpy_sd
    assert_allclose(z_numpy, z_pandas * np.sqrt(n / (n - 1)), rtol=0.0, atol=1e-12)


@pytest.mark.slow
def test_pandas_std_matches_r_scale_sd() -> None:
    """Invariant: the Python-side moments must equal R's sd() to 1e-12, because fit_models.R and build_prediction.py z-scale the same covariates in two different languages."""
    rscript = shutil.which("Rscript")
    if rscript is None:
        pytest.skip("Rscript is not on PATH; cannot cross-check the sample-sd convention")

    values = [1000.0, 1100.0, 1200.0, 900.0, 1050.0]
    literal = ", ".join(repr(v) for v in values)
    completed = subprocess.run(
        [rscript, "-e", f"cat(sprintf('%.15f', sd(c({literal}))))"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    r_sd = float(completed.stdout.strip())
    assert_allclose(float(pd.Series(values).std()), r_sd, rtol=0.0, atol=1e-12)
