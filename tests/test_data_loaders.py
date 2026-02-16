"""Tests for Michael and Ian loaders (fake files and column mapping)."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from hcdt.data import ian, michael
from hcdt.data.schemas import BuildingRecord


def test_load_michael_buildings_csv_adds_event():
    """load_michael_buildings adds event='Michael' and maps columns to BuildingRecord."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        pd.DataFrame(
            {
                "id": ["M1", "M2"],
                "lat": [29.94, 29.95],
                "lon": [-85.41, -85.40],
                "wind_speed": [52.0, 48.0],
                "damage_state": ["moderate", "minor"],
            }
        ).to_csv(path, index=False)
        df = michael.load_michael_buildings(path)
        assert "event" in df.columns
        assert (df["event"] == "Michael").all()
        assert list(df["id"]) == ["M1", "M2"]
        for _, row in df.iterrows():
            BuildingRecord(**row.to_dict())
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_ian_buildings_csv_adds_event():
    """load_ian_buildings adds event='Ian' and maps to BuildingRecord."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        pd.DataFrame(
            {
                "id": ["I1", "I2"],
                "latitude": [26.64, 26.65],
                "longitude": [-81.87, -81.86],
                "flood_depth_m": [0.8, 0.3],
                "first_floor_elev_m": [1.2, 2.0],
            }
        ).to_csv(path, index=False)
        df = ian.load_ian_buildings(path)
        assert "event" in df.columns
        assert (df["event"] == "Ian").all()
        for _, row in df.iterrows():
            BuildingRecord(**row.to_dict())
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_michael_buildings_missing_file():
    """load_michael_buildings raises FileNotFoundError for missing path."""
    with pytest.raises(FileNotFoundError, match="not found"):
        michael.load_michael_buildings("/nonexistent/michael.csv")


def test_load_ian_buildings_unsupported_format():
    """load_ian_buildings raises ValueError for unsupported extension."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ValueError, match="Unsupported format"):
            ian.load_ian_buildings(path)
    finally:
        Path(path).unlink(missing_ok=True)
