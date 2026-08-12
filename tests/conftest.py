from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box


def _validate_bounds(bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if len(bounds) != 4:
        raise ValueError(f"Expected four bounds values, got {len(bounds)}")
    min_x, min_y, max_x, max_y = bounds
    if not min_x < max_x:
        raise ValueError(f"Expected min_x < max_x, got {min_x} and {max_x}")
    if not min_y < max_y:
        raise ValueError(f"Expected min_y < max_y, got {min_y} and {max_y}")
    return min_x, min_y, max_x, max_y


def _validate_lek_frame(leks: pd.DataFrame) -> None:
    expected_columns = ["LEK STATUS", "UTME NAD83", "UTMN NAD83", "STATE", "LEKID"]
    if list(leks.columns) != expected_columns:
        raise ValueError(f"Expected columns {expected_columns}, got {list(leks.columns)}")
    if leks.empty:
        raise ValueError("Synthetic lek table must not be empty")
    if leks[["UTME NAD83", "UTMN NAD83"]].isna().any().any():
        raise ValueError("Synthetic lek coordinates must be finite")


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def synthetic_utm_box() -> tuple[float, float, float, float]:
    return _validate_bounds((500000.0, 4500000.0, 501000.0, 4501000.0))


@pytest.fixture
def synthetic_lek_table(synthetic_utm_box: tuple[float, float, float, float]) -> pd.DataFrame:
    min_x, min_y, max_x, max_y = synthetic_utm_box
    leks = pd.DataFrame(
        [
            {"LEK STATUS": " Active ", "UTME NAD83": min_x + 100.0, "UTMN NAD83": min_y + 100.0, "STATE": " nv ", "LEKID": "L001"},
            {"LEK STATUS": "Active", "UTME NAD83": min_x + 150.0, "UTMN NAD83": min_y + 180.0, "STATE": "NV", "LEKID": "L002"},
            {"LEK STATUS": "active", "UTME NAD83": min_x + 220.0, "UTMN NAD83": min_y + 260.0, "STATE": " Nv ", "LEKID": "L003"},
            {"LEK STATUS": "ACTIVE", "UTME NAD83": min_x + 300.0, "UTMN NAD83": min_y + 320.0, "STATE": "NV", "LEKID": "L004"},
            {"LEK STATUS": "Active", "UTME NAD83": min_x + 380.0, "UTMN NAD83": min_y + 420.0, "STATE": "NV", "LEKID": "L005"},
            {"LEK STATUS": " Active", "UTME NAD83": min_x + 450.0, "UTMN NAD83": min_y + 520.0, "STATE": "UT", "LEKID": "L006"},
            {"LEK STATUS": "Inactive", "UTME NAD83": min_x + 520.0, "UTMN NAD83": min_y + 620.0, "STATE": "NV", "LEKID": "L007"},
            {"LEK STATUS": " Inactive ", "UTME NAD83": min_x + 600.0, "UTMN NAD83": min_y + 700.0, "STATE": "UT", "LEKID": "L008"},
            {"LEK STATUS": "ACTIVE", "UTME NAD83": max_x + 800.0, "UTMN NAD83": max_y + 900.0, "STATE": "NV", "LEKID": "L009"},
            {"LEK STATUS": " active ", "UTME NAD83": max_x + 1000.0, "UTMN NAD83": max_y + 1100.0, "STATE": " UT ", "LEKID": "L010"},
            {"LEK STATUS": "Active", "UTME NAD83": min_x + 260.0, "UTMN NAD83": min_y + 760.0, "STATE": "NV", "LEKID": "L011"},
            {"LEK STATUS": "Inactive", "UTME NAD83": max_x + 1200.0, "UTMN NAD83": max_y + 1200.0, "STATE": "NV", "LEKID": "L012"},
        ]
    )
    _validate_lek_frame(leks)
    return leks


@pytest.fixture
def write_prepare_design_skeleton(
    repo_root: Path,
    synthetic_utm_box: tuple[float, float, float, float],
    synthetic_lek_table: pd.DataFrame,
) -> Any:
    def _write(dest_root: Path) -> dict[str, Path | int]:
        min_x, min_y, max_x, max_y = _validate_bounds(synthetic_utm_box)
        _validate_lek_frame(synthetic_lek_table)

        pipeline_dir = dest_root / "pipeline"
        vector_dir = dest_root / "data-local" / "vectors"
        design_dir = dest_root / "data-local" / "design"
        pipeline_dir.mkdir(parents=True, exist_ok=True)
        vector_dir.mkdir(parents=True, exist_ok=True)
        design_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(repo_root / "pipeline" / "prepare_design.py", pipeline_dir / "prepare_design.py")
        lek_csv = dest_root / "data-local" / "leks_all.csv"
        synthetic_lek_table.to_csv(lek_csv, index=False)

        lek_points = gpd.GeoDataFrame(
            synthetic_lek_table,
            geometry=gpd.points_from_xy(synthetic_lek_table["UTME NAD83"], synthetic_lek_table["UTMN NAD83"]),
            crs="EPSG:26911",
        )
        range_box_26911 = gpd.GeoDataFrame(
            geometry=[box(min_x - 50.0, min_y - 50.0, max_x - 120.0, max_y - 120.0)],
            crs="EPSG:26911",
        )
        range_box_5070 = range_box_26911.to_crs("EPSG:5070")
        range_path = vector_dir / "grsg_range_nv_5070.parquet"
        range_box_5070.to_parquet(range_path, index=False)

        active_mask = synthetic_lek_table["LEK STATUS"].str.strip().str.lower() == "active"
        state_mask = synthetic_lek_table["STATE"].str.strip().str.upper() == "NV"
        used_count = int((active_mask & state_mask).sum())
        if used_count <= 0:
            raise ValueError("Synthetic lek table must yield at least one used Nevada lek")

        inside_count = int(lek_points.to_crs("EPSG:5070").geometry.within(range_box_5070.union_all()).sum())
        if inside_count <= 0:
            raise ValueError("Synthetic range polygon must contain at least one synthetic lek")
        if inside_count >= len(lek_points):
            raise ValueError("Synthetic range polygon must exclude at least one synthetic lek")

        return {
            "script_path": pipeline_dir / "prepare_design.py",
            "design_path": design_dir / "design_points.parquet",
            "used_count": used_count,
            "lek_csv": lek_csv,
            "range_path": range_path,
        }

    return _write
