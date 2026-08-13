from __future__ import annotations

import numpy as np
from numpy.testing import assert_allclose
from scipy.ndimage import uniform_filter


def _as_matching_2d_arrays(slope_deg: np.ndarray, aspect_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    slope = np.asarray(slope_deg, dtype=np.float64)
    aspect = np.asarray(aspect_deg, dtype=np.float64)
    if slope.ndim != 2 or aspect.ndim != 2:
        raise ValueError(f"Expected 2D arrays, got slope.ndim={slope.ndim}, aspect.ndim={aspect.ndim}")
    if slope.shape != aspect.shape:
        raise ValueError(f"Expected matching shapes, got slope.shape={slope.shape} and aspect.shape={aspect.shape}")
    if slope.size == 0:
        raise ValueError("Expected non-empty arrays")
    return slope, aspect


def vrm_from_degrees(slope_deg: np.ndarray, aspect_deg: np.ndarray) -> np.ndarray:
    """Mirror of build_vrm.py after the F5 fix: valid-count-weighted focal mean."""
    slope, aspect = _as_matching_2d_arrays(slope_deg, aspect_deg)
    valid = np.isfinite(slope) & np.isfinite(aspect) & (slope > -9998) & (aspect > -9998)
    slope_rad = np.deg2rad(np.where(valid, slope, 0.0))
    aspect_rad = np.deg2rad(np.where(valid, aspect, 0.0))
    xy = np.sin(slope_rad)
    x = xy * np.sin(aspect_rad)
    y = xy * np.cos(aspect_rad)
    z = np.cos(slope_rad)
    n = uniform_filter(valid.astype(np.float64), size=3, mode="nearest")

    def fmean(component: np.ndarray) -> np.ndarray:
        s = uniform_filter(np.where(valid, component, 0.0), size=3, mode="nearest")
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(n > 0, s / n, 0.0)

    rx, ry, rz = fmean(x), fmean(y), fmean(z)
    vrm = 1.0 - np.sqrt(rx**2 + ry**2 + rz**2)
    vrm[~valid] = -9999.0
    return vrm


def blocked_vrm_from_degrees(slope_deg: np.ndarray, aspect_deg: np.ndarray, block_rows: int) -> np.ndarray:
    slope, aspect = _as_matching_2d_arrays(slope_deg, aspect_deg)
    if block_rows <= 0:
        raise ValueError(f"Expected a positive block size, got {block_rows}")
    height, width = slope.shape
    out = np.empty((height, width), dtype=np.float64)
    for row0 in range(0, height, block_rows):
        r_lo = max(row0 - 1, 0)
        r_hi = min(row0 + block_rows + 1, height)
        window_vrm = vrm_from_degrees(slope[r_lo:r_hi, :], aspect[r_lo:r_hi, :])
        crop_lo = row0 - r_lo
        row_count = min(block_rows, height - row0)
        cropped = window_vrm[crop_lo : crop_lo + row_count, :]
        if cropped.shape != (row_count, width):
            raise ValueError(f"Expected cropped block shape {(row_count, width)}, got {cropped.shape}")
        out[row0 : row0 + row_count, :] = cropped
    return out


def test_flat_plane_has_zero_vrm_everywhere() -> None:
    """Invariant: a perfectly flat surface has no normal dispersion, so VRM must be zero everywhere rather than merely small."""
    slope = np.zeros((8, 8), dtype=np.float64)
    aspect = np.zeros((8, 8), dtype=np.float64)
    assert_allclose(vrm_from_degrees(slope, aspect), 0.0, rtol=0.0, atol=1e-12)


def test_constant_oblique_plane_has_zero_vrm_everywhere() -> None:
    """Invariant: any constant plane, not just a horizontal one, has identical normals and therefore zero VRM; this catches magnitude-based misimplementations."""
    slope = np.full((8, 8), 30.0, dtype=np.float64)
    aspect = np.full((8, 8), 135.0, dtype=np.float64)
    assert_allclose(vrm_from_degrees(slope, aspect), 0.0, rtol=0.0, atol=1e-12)


def test_opposed_center_normal_yields_two_ninths_vrm_at_center() -> None:
    """Invariant: the hand-computed 3x3 checker case must equal exactly 2/9 at the center because it pins the formula to known arithmetic, not just qualitative behavior."""
    slope = np.full((3, 3), 90.0, dtype=np.float64)
    aspect = np.full((3, 3), 180.0, dtype=np.float64)
    aspect[1, 1] = 0.0
    vrm = vrm_from_degrees(slope, aspect)
    # Centre normal is (0, +1, 0); the other eight are (0, -1, 0), so the 3x3
    # mean vector at the centre is (0, (1 + 8 * -1) / 9, 0) = (0, -7/9, 0).
    # |R| = 7/9, therefore VRM = 1 - 7/9 = 2/9.
    assert_allclose(vrm[1, 1], 2.0 / 9.0, rtol=0.0, atol=1e-12)


def test_checkerboard_roughness_exceeds_smooth_ramp_by_large_margin() -> None:
    """Invariant: a highly alternating aspect field must be much rougher than a gentle directional ramp because VRM is meant to measure normal dispersion, not slope magnitude alone."""
    columns = np.linspace(130.0, 138.0, num=32, dtype=np.float64)
    smooth_slope = np.full((32, 32), 10.0, dtype=np.float64)
    smooth_aspect = np.tile(columns, (32, 1))

    row_ix, col_ix = np.indices((32, 32))
    rough_slope = np.full((32, 32), 60.0, dtype=np.float64)
    rough_aspect = np.where((row_ix + col_ix) % 2 == 0, 0.0, 180.0).astype(np.float64)

    smooth_mean = float(vrm_from_degrees(smooth_slope, smooth_aspect).mean())
    rough_mean = float(vrm_from_degrees(rough_slope, rough_aspect).mean())

    assert rough_mean > smooth_mean
    assert rough_mean > 10.0 * smooth_mean


def test_vrm_stays_within_unit_interval_up_to_roundoff() -> None:
    """Invariant: VRM must stay in [0, 1] for every cell, with a tiny lower epsilon only because floating-point roundoff can make |R| exceed 1 by about 1e-16."""
    rng = np.random.default_rng(0)
    slope = rng.uniform(0.0, 90.0, size=(64, 64))
    aspect = rng.uniform(0.0, 360.0, size=(64, 64))
    vrm = vrm_from_degrees(slope, aspect)
    assert np.all(vrm >= -1e-12)
    assert np.all(vrm <= 1.0 + 1e-12)


# FIXED (was FINDING F5): build_vrm.py now excludes nodata cells from the focal
# mean via a valid-count-weighted filter, declares nodata=-9999 in the profile,
# and writes -9999 at the nodata cell itself.
def test_nodata_does_not_poison_neighboring_vrm_cells() -> None:
    """Invariant: one nodata cell must not perturb neighboring VRM values because missing slope/aspect is not terrain roughness."""
    slope = np.full((9, 9), 30.0, dtype=np.float64)
    aspect = np.full((9, 9), 135.0, dtype=np.float64)
    slope[4, 4] = -9999.0
    aspect[4, 4] = -9999.0
    vrm = vrm_from_degrees(slope, aspect)
    neighbor_mask = np.zeros((9, 9), dtype=bool)
    neighbor_mask[3:6, 3:6] = True
    neighbor_mask[4, 4] = False
    assert_allclose(vrm[neighbor_mask], 0.0, rtol=0.0, atol=1e-12)
    assert vrm[4, 4] == -9999.0


def test_block_halo_matches_whole_array_computation() -> None:
    """Invariant: the blocked 1-cell-halo implementation must match the whole-array result exactly because a halo crop bug would create silent seam artifacts."""
    row_axis = np.linspace(0.0, 1.0, num=100, dtype=np.float64)[:, None]
    col_axis = np.linspace(0.0, 1.0, num=24, dtype=np.float64)[None, :]
    slope = 5.0 + 25.0 * row_axis + 10.0 * col_axis
    aspect = np.mod(40.0 + 200.0 * row_axis + 80.0 * col_axis, 360.0)

    whole = vrm_from_degrees(slope, aspect)
    blocked = blocked_vrm_from_degrees(slope, aspect, block_rows=16)
    assert_allclose(blocked, whole, rtol=0.0, atol=1e-12)
