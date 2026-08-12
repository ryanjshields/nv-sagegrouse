from __future__ import annotations

from typing import Iterable

import numpy as np
import pytest


EDGE_CASES: list[tuple[float, str]] = [
    (0.0, "N"),
    (22.5, "N"),
    (22.51, "NE"),
    (67.5, "NE"),
    (67.51, "E"),
    (112.5, "E"),
    (112.51, "SE"),
    (157.5, "SE"),
    (157.51, "S"),
    (202.5, "S"),
    (202.51, "SW"),
    (247.5, "SW"),
    (247.51, "W"),
    (292.5, "W"),
    (292.51, "NW"),
    (337.5, "NW"),
    (337.51, "N"),
    (360.0, "N"),
]
EXPECTED_LABELS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW", "Flat"}


def _require_scalar(value: float, name: str) -> float:
    if not np.isscalar(value):
        raise TypeError(f"Expected {name} to be scalar, got {type(value)!r}")
    return float(value)


def direction(aspect_deg: float) -> str:
    aspect_deg = _require_scalar(aspect_deg, "aspect_deg")
    if aspect_deg is None or aspect_deg != aspect_deg or aspect_deg < 0:
        return "N"
    for hi, lab in [
        (22.5, "N"),
        (67.5, "NE"),
        (112.5, "E"),
        (157.5, "SE"),
        (202.5, "S"),
        (247.5, "SW"),
        (292.5, "W"),
        (337.5, "NW"),
        (360.1, "N"),
    ]:
        if aspect_deg <= hi:
            return lab
    return "N"


def label_direction(slope_deg: float, aspect_deg: float) -> str:
    slope_deg = _require_scalar(slope_deg, "slope_deg")
    aspect_deg = _require_scalar(aspect_deg, "aspect_deg")
    return "Flat" if slope_deg < 0.5 else direction(aspect_deg)


def build_prediction_direction_label(slope_deg: float, aspect_deg: float) -> str:
    slope_deg = _require_scalar(slope_deg, "slope_deg")
    aspect_deg = _require_scalar(aspect_deg, "aspect_deg")
    if slope_deg < 0.5:
        return "Flat"
    label = "E"
    for candidate, (lo, hi) in {
        "N": (337.5, 22.5),
        "NE": (22.5, 67.5),
        "SE": (112.5, 157.5),
        "S": (157.5, 202.5),
        "SW": (202.5, 247.5),
        "W": (247.5, 292.5),
        "NW": (292.5, 337.5),
    }.items():
        in_bin = ((aspect_deg > lo) and (aspect_deg <= hi)) if lo < hi else ((aspect_deg > lo) or (aspect_deg <= hi))
        if in_bin:
            label = candidate
    return label


def _labels_from_cases(cases: Iterable[tuple[float, str]]) -> set[str]:
    labels = {label_direction(1.0, aspect) for aspect, _ in cases}
    labels.add(label_direction(0.49, 180.0))
    return labels


def test_slope_below_half_degree_is_flat() -> None:
    """Invariant: slopes below 0.5 degrees must override aspect because the pipeline reserves a separate Flat category."""
    assert label_direction(0.49, 180.0) == "Flat"


def test_slope_above_half_degree_uses_compass_direction() -> None:
    """Invariant: non-flat slopes must use aspect bins because the pipeline models compass direction away from flat terrain."""
    assert label_direction(0.51, 180.0) == "S"


def test_flat_boundary_is_exclusive() -> None:
    """Invariant: the Flat override is strict `< 0.5`, so exactly 0.5 degrees must stay in the compass bins rather than slipping flat."""
    assert label_direction(0.5, 180.0) == "S"


@pytest.mark.parametrize(("aspect_deg", "expected"), EDGE_CASES)
def test_direction_edges_match_the_extract_covariates_ladder(aspect_deg: float, expected: str) -> None:
    """Invariant: each 22.5-degree boundary must land in the documented upper-inclusive bin because off-by-one edge drift changes model categories."""
    assert label_direction(1.0, aspect_deg) == expected


def test_edge_sweep_produces_exactly_the_nine_expected_labels() -> None:
    """Invariant: the aspect classifier must stay within the model's fixed 9-label vocabulary because renames or extra labels would desynchronize downstream encoding."""
    assert _labels_from_cases(EDGE_CASES) == EXPECTED_LABELS


# FINDING: pipeline/extract_covariates.py:40 folds aspect nodata sentinels into "N", silently turning missing data into a real direction class.
@pytest.mark.xfail(
    strict=True,
    reason="Bug: nodata aspect values should be excluded, not labeled 'N'; strict=True makes this turn red once the pipeline is fixed so the xfail can be removed.",
)
def test_nodata_aspect_is_not_folded_into_north() -> None:
    """Invariant: aspect nodata must not be mapped to North because missing terrain orientation is not a valid ecological category."""
    assert direction(-9999.0) != "N"


# FINDING: pipeline/extract_covariates.py:48 treats negative slope nodata as "Flat", contaminating a real modelling category with missing data.
@pytest.mark.xfail(
    strict=True,
    reason="Bug: nodata slope values should be excluded, not labeled 'Flat'; strict=True makes this turn red once the pipeline is fixed so the xfail can be removed.",
)
def test_nodata_slope_is_not_folded_into_flat() -> None:
    """Invariant: slope nodata must not be mapped to Flat because missing topography is not flat terrain."""
    assert label_direction(-9999.0, 180.0) != "Flat"


# FINDING: pipeline/extract_covariates.py:40 maps NaN aspects through the `a != a` branch to "N", again turning missing data into a real direction class.
@pytest.mark.xfail(
    strict=True,
    reason="Bug: NaN aspect values should be excluded, not labeled 'N'; strict=True makes this turn red once the pipeline is fixed so the xfail can be removed.",
)
def test_nan_aspect_is_not_folded_into_north() -> None:
    """Invariant: NaN aspect values must not masquerade as North because that silently poisons the model input categories."""
    assert direction(float("nan")) != "N"


def test_build_prediction_bins_match_extract_covariates_at_every_edge() -> None:
    """Invariant: training-time and prediction-time aspect bins must agree at every edge because even one mismatch creates train/serve category skew."""
    for aspect_deg, expected in EDGE_CASES:
        assert build_prediction_direction_label(1.0, aspect_deg) == expected
        assert build_prediction_direction_label(1.0, aspect_deg) == label_direction(1.0, aspect_deg)
