"""Load StEER Hurricane Michael building data (DesignSafe PRJ-2113)."""

from pathlib import Path

import pandas as pd

from ._loading import map_columns_to_building_record, to_building_record_frame
from .schemas import BuildingRecord

# Column name variants commonly found in StEER Michael exports (CSV/GeoPackage).
# Map source column -> BuildingRecord field. User data may use different names; adjust as needed.
MICHAEL_COLUMN_MAP = {
    "id": "id",
    "building_id": "id",
    "PID": "id",
    "lat": "lat",
    "latitude": "lat",
    "y": "lat",
    "lon": "lon",
    "longitude": "lon",
    "lng": "lon",
    "x": "lon",
    "footprint_area": "footprint_area",
    "area_sqft": "footprint_area",
    "area_sqm": "footprint_area",
    "stories": "stories",
    "num_stories": "stories",
    "occupancy": "occupancy",
    "occupancy_type": "occupancy",
    "elevation_m": "elevation_m",
    "elev_ft": "elevation_m",
    "first_floor_elev_m": "elevation_m",
    "damage_state": "damage_state",
    "damage": "damage_state",
    "wind_speed_ms": "wind_speed_ms",
    "wind_speed": "wind_speed_ms",
    "v_max_ms": "wind_speed_ms",
    "tract_id": "tract_id",
    "tract": "tract_id",
    "geoid": "tract_id",
}
EVENT_NAME = "Michael"


def load_michael_buildings(path: str) -> pd.DataFrame:
    """
    Load building data from a CSV or GeoPackage export of StEER Hurricane Michael (PRJ-2113).

    Maps source columns to BuildingRecord fields and adds an `event` column set to 'Michael'.
    Expects the file to have been manually downloaded and unzipped from DesignSafe.

    Parameters
    ----------
    path : str
        Path to a .csv or .gpkg file.

    Returns
    -------
    pd.DataFrame
        One row per building with BuildingRecord column names; geometry dropped for CSV-like output.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Michael data path not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".gpkg":
        import geopandas as gpd

        gdf = gpd.read_file(path)
        df = pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))
        # Extract lat/lon from geometry if not already in table
        if "lat" not in df.columns and "lon" not in df.columns and gdf.geometry is not None:
            centroid = gdf.geometry.centroid
            df["lon"] = centroid.x
            df["lat"] = centroid.y
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported format for Michael data: {suffix}. Use .csv or .gpkg.")

    out = map_columns_to_building_record(df, MICHAEL_COLUMN_MAP)
    out["event"] = EVENT_NAME
    return to_building_record_frame(out)
