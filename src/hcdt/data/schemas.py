"""Pydantic models for HCDT building and outage data."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class BuildingRecord(BaseModel):
    """Single building record with hazard and damage attributes."""

    model_config = ConfigDict(extra="forbid")

    id: str
    event: str
    lat: float
    lon: float
    footprint_area: Optional[float] = None
    stories: Optional[int] = None
    occupancy: Optional[str] = None
    elevation_m: Optional[float] = None
    damage_state: Optional[str] = None
    flood_depth_m: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    tract_id: Optional[str] = None


class OutageRecord(BaseModel):
    """Power/utility outage record for a building."""

    model_config = ConfigDict(extra="forbid")

    building_id: str
    outage_start: str  # ISO or parseable datetime string
    outage_end: str
    source: str  # e.g. 'utility', 'crowd'
