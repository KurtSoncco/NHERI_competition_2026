"""Load Ian-BD building data (DesignSafe PRJ-5770) with elevation and flood damage."""

from pathlib import Path

import pandas as pd

from ._loading import map_columns_to_building_record, to_building_record_frame
from .schemas import BuildingRecord

# Column name variants for Ian-BD exports (first-floor elevation, flood depth, damage).
IAN_COLUMN_MAP = {
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
    "ff_elev_m": "elevation_m",
    "damage_state": "damage_state",
    "damage": "damage_state",
    "flood_depth_m": "flood_depth_m",
    "flood_depth": "flood_depth_m",
    "depth_ft": "flood_depth_m",
    "wind_speed_ms": "wind_speed_ms",
    "wind_speed": "wind_speed_ms",
    "tract_id": "tract_id",
    "tract": "tract_id",
    "geoid": "tract_id",
}
EVENT_NAME = "Ian"


def load_ian_buildings(path: str) -> pd.DataFrame:
    """
    Load building data from a CSV or GeoPackage export of Ian-BD (PRJ-5770).

    Maps first-floor elevation, flood depth, and damage attributes to BuildingRecord
    and adds an `event` column set to 'Ian'. Expects data to be manually downloaded
    and unzipped from DesignSafe.

    Parameters
    ----------
    path : str
        Path to a .csv or .gpkg file.

    Returns
    -------
    pd.DataFrame
        One row per building with BuildingRecord column names.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Ian data path not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".gpkg":
        import geopandas as gpd

        gdf = gpd.read_file(path)
        df = pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))
        if "lat" not in df.columns and "lon" not in df.columns and gdf.geometry is not None:
            centroid = gdf.geometry.centroid
            df["lon"] = centroid.x
            df["lat"] = centroid.y
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported format for Ian data: {suffix}. Use .csv or .gpkg.")

    out = map_columns_to_building_record(df, IAN_COLUMN_MAP)
    out["event"] = EVENT_NAME
    return to_building_record_frame(out)
