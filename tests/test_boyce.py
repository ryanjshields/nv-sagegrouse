from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numpy.testing import assert_allclose


def _as_1d_float_array(values: np.ndarray | list[float], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1:
        raise ValueError(f"Expected {name} to be 1D, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"Expected {name} to be non-empty")
    return array


def boyce_index(midpoints: np.ndarray | list[float], pe_ratios: np.ndarray | list[float]) -> float:
    mids = _as_1d_float_array(midpoints, "midpoints")
    pe = _as_1d_float_array(pe_ratios, "pe_ratios")
    if mids.shape != pe.shape:
        raise ValueError(f"Expected matching shapes, got midpoints.shape={mids.shape} and pe_ratios.shape={pe.shape}")
    rank = lambda a: pd.Series(a).rank().values
    return float(np.corrcoef(rank(mids), rank(pe))[0, 1])


def moving_window_pe(
    p_used: np.ndarray | list[float], area: np.ndarray | list[float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    used = _as_1d_float_array(p_used, "p_used")
    available = _as_1d_float_array(area, "area")
    # boyce.py order: filter used values (finite, >= 0) BEFORE lo/hi and the clip.
    used = used[np.isfinite(used) & (used >= 0.0)]
    lo = float(available.min())
    hi = float(np.quantile(available, 0.999))
    # F10 fix (verbatim boyce.py): clip values above the 99.9th-percentile
    # ceiling into the top window instead of excluding them, and make the final
    # window upper-inclusive so p == hi is counted.
    available = np.minimum(available, hi)
    used = np.minimum(used, hi)
    width = (hi - lo) / 5.0
    starts = np.linspace(lo, hi - width, 10)
    ends = starts + width

    mids: list[float] = []
    ratios: list[float] = []
    obs: list[float] = []
    exp: list[float] = []
    for i, (start, end) in enumerate(zip(starts, ends, strict=True)):
        last = i == len(starts) - 1
        observed = float(((used >= start) & ((used <= end) if last else (used < end))).mean())
        expected = float(((available >= start) & ((available <= end) if last else (available < end))).mean())
        obs.append(observed)
        exp.append(expected)
        if expected > 0.0:
            mids.append(float(start + width / 2.0))
            ratios.append(observed / expected)
    return (
        np.asarray(mids, dtype=np.float64),
        np.asarray(ratios, dtype=np.float64),
        np.asarray(obs, dtype=np.float64),
        np.asarray(exp, dtype=np.float64),
        starts.astype(np.float64),
        ends.astype(np.float64),
    )


def test_perfect_monotone_ranking_gives_exactly_one() -> None:
    """Invariant: strictly increasing P/E against increasing class midpoint must yield a perfect Boyce score because the pipeline headline is Spearman-on-ranks."""
    value = boyce_index([0.1, 0.2, 0.3, 0.4, 0.5], [0.5, 1.0, 2.0, 3.0, 6.0])
    assert_allclose(value, 1.0, rtol=0.0, atol=1e-12)


def test_single_adjacent_swap_gives_exactly_nine_tenths() -> None:
    """Invariant: one adjacent rank swap must land on the hand-computed 0.9 Spearman value because a near-perfect monotone curve should not be rounded away."""
    mids = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float64)
    pe = np.array([0.5, 1.0, 2.0, 6.0, 3.0], dtype=np.float64)
    value = boyce_index(mids, pe)

    mids_ranks = np.arange(1.0, 6.0, dtype=np.float64)
    pe_ranks = np.array([1.0, 2.0, 3.0, 5.0, 4.0], dtype=np.float64)
    d = mids_ranks - pe_ranks
    # d = [0, 0, 0, -1, 1], so sum(d^2) = 2 and
    # Spearman = 1 - 6 * 2 / (5 * (5^2 - 1)) = 1 - 12 / 120 = 0.9 exactly.
    closed_form = 1.0 - (6.0 * float(np.square(d).sum())) / (5.0 * (5.0**2 - 1.0))

    assert_allclose(closed_form, 0.9, rtol=0.0, atol=1e-12)
    assert_allclose(value, 0.9, rtol=0.0, atol=1e-12)
    assert_allclose(value, closed_form, rtol=0.0, atol=1e-12)


def test_strict_counter_prediction_gives_exactly_negative_one() -> None:
    """Invariant: a surface that ranks used habitat backwards must score -1 rather than collapsing to zero or NaN because the Boyce index claims to detect counter-prediction."""
    value = boyce_index([0.1, 0.2, 0.3, 0.4, 0.5], [6.0, 3.0, 2.0, 1.0, 0.5])
    assert_allclose(value, -1.0, rtol=0.0, atol=1e-12)


def test_ties_use_average_ranks_before_correlation() -> None:
    """Invariant: tied P/E classes must receive average ranks because replacing pandas rank averaging with positional tie-breaking changes the ecological score."""
    mids = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    pe = np.array([1.0, 2.0, 2.0, 3.0], dtype=np.float64)
    mids_ranks = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
    pe_ranks = np.array([1.0, 2.5, 2.5, 4.0], dtype=np.float64)

    mids_centered = mids_ranks - mids_ranks.mean()
    pe_centered = pe_ranks - pe_ranks.mean()
    expected = float(
        np.sum(mids_centered * pe_centered)
        / math.sqrt(float(np.sum(mids_centered**2) * np.sum(pe_centered**2)))
    )

    assert_allclose(boyce_index(mids, pe), expected, rtol=0.0, atol=1e-12)


# FIXED (was FINDING F8): boyce.py now refuses to write artifacts when the index
# is non-finite (SystemExit "BOYCE_DEGENERATE"). The NaN math itself is correct
# and this test pins it: constant P/E is undefined, not neutral.
def test_constant_pe_ratio_is_undefined_and_returns_nan() -> None:
    """Invariant: constant P/E must stay undefined because Spearman on a zero-variance rank vector is mathematically NaN, not ecological neutrality."""
    value = boyce_index([0.1, 0.2, 0.3, 0.4, 0.5], [2.0, 2.0, 2.0, 2.0, 2.0])
    assert math.isnan(value)


def test_moving_window_pe_chain_keeps_lengths_finite_and_top_class_largest() -> None:
    """Invariant: the full moving-window P/E chain should preserve finite ratios and rank the last class highest when synthetic used points are staged from lower-overlap to top-window-only values."""
    area = np.linspace(0.0, 1.0, num=1000, endpoint=False, dtype=np.float64)
    # All ten synthetic used points fall in the final window; two are also in the
    # third-from-last overlap, six in the second-from-last overlap, and all ten in
    # the last window, so the retained P/E ladder is hand-checkable and increasing.
    p_used = np.array([0.796, 0.804, 0.816, 0.824, 0.832, 0.840, 0.884, 0.908, 0.944, 0.980], dtype=np.float64)

    mids, ratios, obs, exp, starts, ends = moving_window_pe(p_used, area)

    assert len(mids) == len(ratios)
    assert np.all(np.isfinite(ratios))
    assert starts.shape == (10,)
    assert ends.shape == (10,)
    assert ratios[-1] == ratios.max()
    assert obs[-3] < obs[-2] < obs[-1]
    assert_allclose(boyce_index(mids[-3:], ratios[-3:]), 1.0, rtol=0.0, atol=1e-12)


# FINDING: pipeline/boyce.py:31-33 deliberately defines a moving-window scheme rather than ten disjoint bins; that matches the docstring at line 7, but the overlapping P/E classes are autocorrelated, so the reported Spearman index is reviewer-stable rather than independent-bin stable.
def test_window_geometry_overlaps_instead_of_tiling() -> None:
    """Invariant: the ten Boyce windows must overlap because the pipeline advertises moving windows, and treating them as disjoint classes would misread the statistic."""
    area = np.linspace(0.0, 1.0, num=1000, endpoint=False, dtype=np.float64)
    _, _, _, _, starts, ends = moving_window_pe([0.85, 0.9], area)

    width = float(ends[0] - starts[0])
    step = float(starts[1] - starts[0])

    assert step < width
    assert starts[0] == 0.0
    assert ends[-1] <= float(np.quantile(area, 0.999))
    assert ends[-1] > starts[0]


# FIXED (was FINDING F10): used predictions at or above hi are clipped to hi and
# the final window is upper-inclusive, so the highest-suitability leks land in
# the top window instead of vanishing from every class.
def test_used_points_at_or_above_hi_land_in_the_top_window() -> None:
    """Invariant: used predictions at or above the 0.999 area quantile must be counted in the final window, because those are exactly the leks the monotonicity claim leans on."""
    area = np.linspace(0.0, 1.0, num=1000, endpoint=False, dtype=np.float64)
    hi = float(np.quantile(area, 0.999))
    # Every synthetic lek sits at or above hi -- the highest-suitability leks,
    # exactly the ones the "lek density rises with suitability" claim leans on.
    p_used = np.array([hi, hi + 1e-4, hi + 2e-4, hi + 1e-3], dtype=np.float64)

    mids, ratios, obs, exp, _, _ = moving_window_pe(p_used, area)

    assert obs.size == 10
    assert_allclose(obs[-1], 1.0, rtol=0.0, atol=0.0)
    assert_allclose(obs[:-1], 0.0, rtol=0.0, atol=0.0)
    # The clip pushes area mass INTO the top window, so exp > 0 there is
    # structural -- the retained P/E ladder (what boyce.py writes to
    # boyce_pe.csv) must therefore include the top window, not drop it.
    assert exp[-1] > 0.0
    assert mids.size == ratios.size == 10


# FINDING: pipeline/boyce.py:31-35 counts each used point once per overlapping window, so the "proportion of used leks in class i" at boyce.py:35 is not a partition and the ten observed shares sum to well above one.
def test_overlapping_windows_double_count_used_points() -> None:
    """Invariant: the observed shares must sum above one because the ten windows overlap, proving `obs` is a moving-window share rather than the class partition the docstring implies."""
    area = np.linspace(0.0, 1.0, num=1000, endpoint=False, dtype=np.float64)
    # Interior points, comfortably inside [lo, hi), so nothing is lost off the top end.
    p_used = np.array([0.15, 0.22, 0.31, 0.39, 0.48, 0.57, 0.66, 0.74], dtype=np.float64)

    _, _, obs, _, starts, ends = moving_window_pe(p_used, area)

    width = float(ends[0] - starts[0])
    step = float(starts[1] - starts[0])
    # width is (hi - lo)/5 while the step is (hi - lo - width)/9, so each point is
    # covered by roughly width/step ~= 1.8 windows and is counted in each of them.
    assert step < width
    assert obs.sum() > 1.0
