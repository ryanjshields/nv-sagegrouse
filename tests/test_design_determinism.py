from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from shapely.geometry import box


pytestmark = pytest.mark.slow


def _sample_coordinates(gdf: gpd.GeoDataFrame, count: int, seed: int) -> np.ndarray:
    if gdf.empty:
        raise ValueError("Expected at least one geometry to sample from")
    if count <= 0:
        raise ValueError(f"Expected a positive sample count, got {count}")
    sampled = gdf.sample_points(count, rng=seed).explode(index_parts=False)
    coords = np.column_stack([sampled.x.to_numpy(), sampled.y.to_numpy()])
    if coords.shape != (count, 2):
        raise ValueError(f"Expected sampled coordinates with shape {(count, 2)}, got {coords.shape}")
    return coords


def _run_prepare_design(uv_path: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [uv_path, "run", "pipeline/prepare_design.py"],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )


def test_sample_points_seed_is_repeatable_across_objects(synthetic_utm_box: tuple[float, float, float, float]) -> None:
    """Invariant: seeded `sample_points` must reproduce exact coordinates because the design script claims byte-stable reruns."""
    min_x, min_y, max_x, max_y = synthetic_utm_box
    polygon = box(min_x, min_y, max_x, max_y)
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:5070")

    first = _sample_coordinates(gdf, count=100, seed=20260811)
    second = _sample_coordinates(gdf, count=100, seed=20260811)
    rebuilt = _sample_coordinates(gpd.GeoDataFrame(geometry=[box(min_x, min_y, max_x, max_y)], crs="EPSG:5070"), count=100, seed=20260811)
    changed_seed = _sample_coordinates(gdf, count=100, seed=20260812)

    assert first.shape[0] == 100
    assert_array_equal(first, second)
    assert_array_equal(first, rebuilt)
    assert changed_seed.shape == first.shape
    assert np.any(changed_seed[:, 0] != first[:, 0]) or np.any(changed_seed[:, 1] != first[:, 1])


def test_prepare_design_is_byte_stable_and_seed_sensitive(
    tmp_path: Path,
    write_prepare_design_skeleton,
) -> None:
    """Invariant: rerunning `prepare_design.py` with the same seed must be byte-identical, while changing the seed must move available points."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        pytest.skip("uv is not on PATH; cannot run the real prepare_design.py subprocess test")

    skeleton = write_prepare_design_skeleton(tmp_path)
    design_path = Path(skeleton["design_path"])
    used_count = int(skeleton["used_count"])
    script_path = Path(skeleton["script_path"])

    start = time.perf_counter()
    first_run = _run_prepare_design(uv_path, tmp_path)
    elapsed = time.perf_counter() - start
    assert "DESIGN_COMPLETE" in first_run.stdout
    assert design_path.exists()
    first_bytes = design_path.read_bytes()
    first_design = pd.read_parquet(design_path)

    used = first_design[first_design["use"] == 1].copy()
    available = first_design[first_design["use"] == 0].copy()
    assert len(used) == used_count
    assert len(available) == 10 * len(used)
    baseline_available_xy = available[["x", "y"]].to_numpy()
    if baseline_available_xy.ndim != 2 or baseline_available_xy.shape[1] != 2:
        raise ValueError(f"Expected available coordinates with shape (n, 2), got {baseline_available_xy.shape}")

    design_path.unlink()
    second_run = _run_prepare_design(uv_path, tmp_path)
    assert "DESIGN_COMPLETE" in second_run.stdout
    second_bytes = design_path.read_bytes()
    assert first_bytes == second_bytes

    script_text = script_path.read_text(encoding="utf-8")
    script_path.write_text(script_text.replace("SEED = 20260811", "SEED = 20260812"), encoding="utf-8")
    third_run = _run_prepare_design(uv_path, tmp_path)
    assert "DESIGN_COMPLETE" in third_run.stdout

    reseeded_design = pd.read_parquet(design_path)
    reseeded_available_xy = reseeded_design.loc[reseeded_design["use"] == 0, ["x", "y"]].to_numpy()
    if reseeded_available_xy.shape != baseline_available_xy.shape:
        raise ValueError(
            f"Expected reseeded available coordinates to preserve shape {baseline_available_xy.shape}, "
            f"got {reseeded_available_xy.shape}"
        )
    assert np.any(reseeded_available_xy[:, 0] != baseline_available_xy[:, 0]) or np.any(
        reseeded_available_xy[:, 1] != baseline_available_xy[:, 1]
    )

    print(f"prepare_design subprocess runtime: {elapsed:.2f}s")
