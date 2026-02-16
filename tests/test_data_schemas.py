"""Tests for data schemas and BuildingRecord mapping."""

import pandas as pd
import pytest

from hcdt.data.schemas import BuildingRecord, OutageRecord


def test_building_record_from_fake_rows():
    """Construct 2–3 fake rows and verify mapping to BuildingRecord."""
    rows = [
        {
            "id": "B001",
            "event": "Michael",
            "lat": 29.94,
            "lon": -85.41,
            "footprint_area": 250.0,
            "stories": 2,
            "occupancy": "residential",
            "elevation_m": 3.5,
            "damage_state": "moderate",
            "flood_depth_m": None,
            "wind_speed_ms": 52.0,
            "tract_id": "12013",
        },
        {
            "id": "B002",
            "event": "Ian",
            "lat": 26.64,
            "lon": -81.87,
            "footprint_area": 180.0,
            "stories": 1,
            "occupancy": "residential",
            "elevation_m": 1.2,
            "damage_state": "severe",
            "flood_depth_m": 0.8,
            "wind_speed_ms": None,
            "tract_id": "12071",
        },
        {
            "id": "B003",
            "event": "Michael",
            "lat": 30.0,
            "lon": -85.0,
            "footprint_area": None,
            "stories": None,
            "occupancy": None,
            "elevation_m": None,
            "damage_state": None,
            "flood_depth_m": None,
            "wind_speed_ms": 48.0,
            "tract_id": None,
        },
    ]
    for row in rows:
        rec = BuildingRecord(**row)
        assert rec.id == row["id"]
        assert rec.event == row["event"]
        assert rec.lat == row["lat"]
        assert rec.lon == row["lon"]
        assert rec.wind_speed_ms == row.get("wind_speed_ms")
        assert rec.flood_depth_m == row.get("flood_depth_m")


def test_building_record_from_dataframe_rows():
    """Verify DataFrame rows (as dicts) map to BuildingRecord."""
    df = pd.DataFrame(
        [
            {"id": "1", "event": "Michael", "lat": 29.0, "lon": -85.0, "wind_speed_ms": 50.0},
            {"id": "2", "event": "Ian", "lat": 26.0, "lon": -82.0, "flood_depth_m": 0.5},
        ]
    )
    for _, row in df.iterrows():
        rec = BuildingRecord(**row.to_dict())
        assert rec.id in ("1", "2")
        assert rec.event in ("Michael", "Ian")
        assert rec.lat in (29.0, 26.0)


def test_outage_record_mapping():
    """OutageRecord accepts source values like 'utility' and 'crowd'."""
    r1 = OutageRecord(
        building_id="B001",
        outage_start="2022-09-28T12:00:00",
        outage_end="2022-10-01T18:00:00",
        source="utility",
    )
    assert r1.building_id == "B001"
    assert r1.source == "utility"

    r2 = OutageRecord(
        building_id="B002",
        outage_start="2022-10-01T00:00:00",
        outage_end="2022-10-02T00:00:00",
        source="crowd",
    )
    assert r2.source == "crowd"
