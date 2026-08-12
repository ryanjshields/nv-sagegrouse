from __future__ import annotations

import math
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose


def _as_1d_array(values: np.ndarray | list[float] | list[int], name: str, dtype: np.dtype[np.float64]) -> np.ndarray:
    array = np.asarray(values, dtype=dtype)
    if array.ndim != 1:
        raise ValueError(f"Expected {name} to be 1D, got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"Expected {name} to be non-empty")
    return array


def _validated_auc_inputs(y: np.ndarray | list[int], p: np.ndarray | list[float]) -> tuple[np.ndarray, np.ndarray]:
    labels = _as_1d_array(y, "y", np.float64)
    scores = _as_1d_array(p, "p", np.float64)
    if labels.shape != scores.shape:
        raise ValueError(f"mismatched lengths: y.shape={labels.shape}, p.shape={scores.shape}")
    unique = set(np.unique(labels).tolist())
    if not unique.issubset({0.0, 1.0}):
        raise ValueError(f"labels must be binary 0/1, got {sorted(unique)}")
    n1 = int(np.sum(labels == 1.0))
    n0 = int(np.sum(labels == 0.0))
    if n1 == 0 or n0 == 0:
        raise ValueError(f"need at least one positive and one negative example, got n1={n1}, n0={n0}")
    return labels.astype(np.int64), scores


def rank_sum_auc(y: np.ndarray | list[int], p: np.ndarray | list[float]) -> float:
    labels, scores = _validated_auc_inputs(y, p)
    ranks = pd.Series(scores).rank().values
    n1 = int(np.sum(labels == 1))
    n0 = int(np.sum(labels == 0))
    return float((np.sum(ranks[labels == 1]) - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def pairwise_auc(y: np.ndarray | list[int], p: np.ndarray | list[float]) -> float:
    labels, scores = _validated_auc_inputs(y, p)
    used = scores[labels == 1]
    available = scores[labels == 0]
    concordance = ((used[:, None] > available[None, :]).astype(np.float64)) + 0.5 * (
        used[:, None] == available[None, :]
    ).astype(np.float64)
    return float(concordance.mean())


def test_hand_computed_four_point_example_gives_three_quarters() -> None:
    """Invariant: the rank-sum formula must reproduce the hand-worked 0.75 example because that pins the implementation to exact arithmetic rather than a library black box."""
    y = np.array([1, 1, 0, 0], dtype=np.int64)
    p = np.array([0.9, 0.4, 0.6, 0.1], dtype=np.float64)

    assert_allclose(rank_sum_auc(y, p), 0.75, rtol=0.0, atol=1e-12)
    assert_allclose(pairwise_auc(y, p), 0.75, rtol=0.0, atol=1e-12)


def test_all_ties_give_exactly_one_half() -> None:
    """Invariant: a complete tie between used and available scores must score 0.5 because tie-blind ranking silently biases the AUC away from chance."""
    y = np.array([1, 1, 0, 0], dtype=np.int64)
    p = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float64)

    assert_allclose(rank_sum_auc(y, p), 0.5, rtol=0.0, atol=1e-12)
    assert_allclose(pairwise_auc(y, p), 0.5, rtol=0.0, atol=1e-12)


def test_perfect_and_inverted_separation_hit_the_unit_interval_endpoints() -> None:
    """Invariant: complete separation must map to exactly 1.0 and complete inversion to exactly 0.0 because the pipeline reports AUC on an absolute 0-to-1 scale."""
    y = np.array([1, 1, 1, 0, 0, 0], dtype=np.int64)

    assert_allclose(rank_sum_auc(y, [0.9, 0.8, 0.7, 0.3, 0.2, 0.1]), 1.0, rtol=0.0, atol=1e-12)
    assert_allclose(rank_sum_auc(y, [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]), 0.0, rtol=0.0, atol=1e-12)


def test_negating_scores_complements_auc_to_one() -> None:
    """Invariant: flipping the score ordering must complement AUC to one because the metric is pure rank concordance, not calibration."""
    rng = np.random.default_rng(7)
    p = rng.normal(size=20)
    y = np.array([0, 1] * 10, dtype=np.int64)

    auc = rank_sum_auc(y, p)
    reversed_auc = rank_sum_auc(y, -p)
    assert_allclose(auc + reversed_auc, 1.0, rtol=0.0, atol=1e-12)


def test_strictly_increasing_transform_leaves_auc_unchanged() -> None:
    """Invariant: a strictly increasing transform must preserve AUC because the pipeline may evaluate either the linear predictor or the response probability."""
    rng = np.random.default_rng(7)
    p = rng.normal(size=24)
    y = np.array([1, 0, 1, 0, 0, 1] * 4, dtype=np.int64)

    logistic = 1.0 / (1.0 + np.exp(-p))
    assert_allclose(rank_sum_auc(y, p), rank_sum_auc(y, logistic), rtol=0.0, atol=1e-12)


@pytest.mark.slow
def test_python_rank_sum_auc_matches_rscript_reference_examples() -> None:
    """Invariant: the Python port must agree with the exact base-R helper because fidelity to the pipeline source matters more than agreement with any generic AUC implementation."""
    rscript = shutil.which("Rscript")
    if rscript is None:
        pytest.skip("Rscript is not on PATH; cannot cross-check against the pipeline's base-R auc helper")

    command = (
        "auc <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0); "
        "(sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }; "
        "cat(sprintf('%.17g\\n', auc(c(1,1,0,0), c(0.9,0.4,0.6,0.1)))); "
        "cat(sprintf('%.17g\\n', auc(c(1,1,0,0), c(0.5,0.5,0.5,0.5))))"
    )
    completed = subprocess.run(
        [rscript, "-e", command],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError(f"Expected exactly two R outputs, got {lines!r}")

    r_values = np.asarray([float(lines[0]), float(lines[1])], dtype=np.float64)
    py_values = np.asarray(
        [
            rank_sum_auc([1, 1, 0, 0], [0.9, 0.4, 0.6, 0.1]),
            rank_sum_auc([1, 1, 0, 0], [0.5, 0.5, 0.5, 0.5]),
        ],
        dtype=np.float64,
    )
    assert_allclose(py_values, r_values, rtol=0.0, atol=1e-12)


def test_input_validation_rejects_mismatched_lengths() -> None:
    """Invariant: y and p must have identical length because the rank-sum formula pairs one label with one score at every row."""
    with pytest.raises(ValueError, match="mismatched lengths"):
        rank_sum_auc([1, 0], [0.2])


def test_input_validation_rejects_all_used_labels() -> None:
    """Invariant: AUC needs both classes because ranking only presences has no negative baseline to compare against."""
    with pytest.raises(ValueError, match="positive and one negative"):
        rank_sum_auc([1, 1, 1], [0.2, 0.4, 0.6])


def test_input_validation_rejects_non_binary_labels() -> None:
    """Invariant: the pipeline helper assumes binary use labels, so any other coding must fail loudly instead of producing a meaningless fraction."""
    with pytest.raises(ValueError, match="binary 0/1"):
        rank_sum_auc([1, 2, 0], [0.2, 0.4, 0.6])
